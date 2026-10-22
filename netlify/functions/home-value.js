/**
 * GET /.netlify/functions/home-value?address=<full street address>
 *
 * Looks up an automated valuation (AVM) from RentCast and returns:
 *   { ok: true, address, price, priceRangeLow, priceRangeHigh, comparables: [{ address, price, beds, baths, sqft }] }
 * or, on any failure:
 *   { ok: false, error }
 *
 * The RentCast API key stays server-side (process.env.RENTCAST_API_KEY) and is never sent to the browser.
 * Zillow, Redfin and Realtor.com have no public valuation APIs and are never scraped.
 */

const RENTCAST_URL = 'https://api.rentcast.io/v1/avm/value';
const REQUEST_TIMEOUT_MS = 8000;

// Best-effort guards for the RentCast free tier (~50 lookups/month). Both live in memory, so they only
// apply within one warm function instance; see README for stronger options.
const MAX_LOOKUPS_PER_IP = 3;
const RATE_WINDOW_MS = 24 * 60 * 60 * 1000;
const CACHE_TTL_MS = 24 * 60 * 60 * 1000;
const lookupsByIp = new Map();
const cache = new Map();

function json(statusCode, body) {
  return {
    statusCode,
    headers: {
      'Content-Type': 'application/json; charset=utf-8',
      'Cache-Control': 'no-store',
      'X-Content-Type-Options': 'nosniff'
    },
    body: JSON.stringify(body)
  };
}

function positiveNumber(value) {
  const n = Number(value);
  return Number.isFinite(n) && n > 0 ? n : null;
}

function wholeDollars(value) {
  const n = positiveNumber(value);
  return n === null ? null : Math.round(n);
}

function clientIp(headers) {
  return (
    headers['x-nf-client-connection-ip'] ||
    headers['client-ip'] ||
    (headers['x-forwarded-for'] || '').split(',')[0].trim() ||
    'unknown'
  );
}

function isRateLimited(ip) {
  const now = Date.now();
  const recent = (lookupsByIp.get(ip) || []).filter((t) => now - t < RATE_WINDOW_MS);
  if (recent.length >= MAX_LOOKUPS_PER_IP) {
    lookupsByIp.set(ip, recent);
    return true;
  }
  recent.push(now);
  lookupsByIp.set(ip, recent);
  return false;
}

function toComparable(comp) {
  const address =
    comp.formattedAddress ||
    [comp.addressLine1, comp.city, comp.state].filter(Boolean).join(', ') ||
    null;
  return {
    address,
    price: wholeDollars(comp.price),
    beds: Number.isFinite(comp.bedrooms) ? comp.bedrooms : null,
    baths: Number.isFinite(comp.bathrooms) ? comp.bathrooms : null,
    sqft: wholeDollars(comp.squareFootage)
  };
}

exports.handler = async (event) => {
  if (event.httpMethod !== 'GET') {
    return json(405, { ok: false, error: 'Method not allowed.' });
  }

  const address = String((event.queryStringParameters || {}).address || '')
    .trim()
    .replace(/\s+/g, ' ');
  if (address.length < 6 || address.length > 200) {
    return json(400, { ok: false, error: 'Please provide a full street address.' });
  }

  const apiKey = process.env.RENTCAST_API_KEY;
  if (!apiKey) {
    console.error('home-value: RENTCAST_API_KEY is not set');
    return json(503, { ok: false, error: 'Valuation service is not configured.' });
  }

  const cacheKey = address.toLowerCase();
  const cached = cache.get(cacheKey);
  if (cached && Date.now() - cached.at < CACHE_TTL_MS) {
    return json(200, cached.body);
  }

  if (isRateLimited(clientIp(event.headers || {}))) {
    return json(429, { ok: false, error: 'Too many lookups. Jian will follow up with your estimate.' });
  }

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  try {
    const url = `${RENTCAST_URL}?address=${encodeURIComponent(address)}&compCount=5`;
    const res = await fetch(url, {
      headers: { 'X-Api-Key': apiKey, Accept: 'application/json' },
      signal: controller.signal
    });

    if (res.status === 404) {
      return json(404, { ok: false, error: 'No valuation data found for this address.' });
    }
    if (!res.ok) {
      const detail = await res.text().catch(() => '');
      console.error(`home-value: RentCast responded ${res.status}`, detail.slice(0, 300));
      return json(502, { ok: false, error: 'Valuation service is unavailable right now.' });
    }

    const data = await res.json();
    const price = wholeDollars(data && data.price);
    if (!price) {
      return json(404, { ok: false, error: 'No estimate is available for this address.' });
    }

    const comparables = (Array.isArray(data.comparables) ? data.comparables : [])
      .map(toComparable)
      .filter((c) => c.price)
      .slice(0, 3);

    const body = {
      ok: true,
      address: (data.subjectProperty && data.subjectProperty.formattedAddress) || address,
      price,
      priceRangeLow: wholeDollars(data.priceRangeLow),
      priceRangeHigh: wholeDollars(data.priceRangeHigh),
      comparables
    };
    cache.set(cacheKey, { at: Date.now(), body });
    return json(200, body);
  } catch (err) {
    const timedOut = err && err.name === 'AbortError';
    console.error('home-value: lookup failed', timedOut ? 'timeout' : err);
    return json(timedOut ? 504 : 502, { ok: false, error: 'Valuation service is unavailable right now.' });
  } finally {
    clearTimeout(timer);
  }
};
