# Jian-Xing Wu, REALTOR® | website

A single-page site in plain HTML, CSS and vanilla JS, with one Netlify Function for home-value lookups.

```
index.html                       the whole site (inline CSS + JS)
thank-you.html                   fallback success page when JavaScript is off
images/jian-xing-wu.jpg          headshot used in the About section
netlify/functions/home-value.js  server-side RentCast valuation lookup
netlify.toml                     publish dir, functions dir, security headers
```

## 1. Deploy to Netlify

1. Push this folder to a GitHub repo.
2. In Netlify: **Add new site → Import an existing project**, then pick the repo.
   - Build command and publish directory come from `netlify.toml`. Leave the UI fields blank.
3. **Turn on form detection.** New Netlify sites have it off by default. Go to
   **Site configuration → Forms** and click **Enable form detection**. Then redeploy
   (**Deploys → Trigger deploy → Deploy site**) so Netlify finds the `lead` and `home-value` forms.
4. Add the environment variables (section 2) and redeploy again.
5. Optional: add a custom domain under **Domain management**.

To test locally, run `npm i -g netlify-cli`, then `netlify dev`. This serves the site and the function at `http://localhost:8888`.
Netlify Forms only accept submissions on a deployed site. Locally, the form POST fails and the page shows its error message, which is expected.

## 2. Environment variables

Set these under **Site configuration → Environment variables**:

| Variable | Required | Scope | Purpose |
|---|---|---|---|
| `RENTCAST_API_KEY` | Yes, for estimates | Functions | Your key from https://app.rentcast.io/app/api. It's used only inside the function and never sent to the browser. |
| `GOOGLE_MAPS_API_KEY` | Optional | Builds | Turns on address autocomplete. The build command writes it into `index.html`, so it's public by design. Restrict it to your domain (HTTP referrers) and to the **Places API (New)** + **Maps JavaScript API** in Google Cloud. |

If `RENTCAST_API_KEY` is missing or a lookup fails, the visitor is still thanked. They're told Jian will follow up with a personalized estimate within 24 hours, and their contact info is already saved in Netlify Forms.

If you'd rather not use an env var for Google, replace `__GOOGLE_MAPS_API_KEY__` in `index.html` with the key itself.

### RentCast quota / rate limiting

The RentCast free tier allows about **50 lookups per month**. The function guards that quota in a few ways:

- It caches each address for 24 hours, so repeat lookups don't spend quota.
- It allows **3 lookups per IP per 24 hours** (`MAX_LOOKUPS_PER_IP`).
- The site only calls it after the visitor submits name, phone and email.

The cache and per-IP limit live in memory, so they only apply within one warm function instance. They're a soft guard, not a hard limit. For stronger protection:
- Set a usage cap or billing alert in the RentCast dashboard. This is the real backstop.
- Move to Netlify Functions v2 and use its built-in `config.rateLimit` (per-IP rate limiting at the edge). Or store counts in Netlify Blobs.
- Upgrade the RentCast plan if leads outgrow the free tier.

## 3. Form email notifications

You need to set this up separately for **each** form:

1. **Site configuration → Notifications → Emails and webhooks**.
2. Under **Form submission notifications**, click **Add notification → Email notification**.
3. Choose **Event to listen for:** "New form submission". For **Form**, pick `lead`.
4. Enter Jian's email and save.
5. Repeat steps 2–4 and pick `home-value`.

Submissions are also listed under **Forms** in the Netlify dashboard and can be exported as CSV.
Spam caught by the honeypot (`bot-field`) goes to the "Spam submissions" list.

Every submission includes these hidden fields:
- `lead_source`: which button or section it came from, e.g. `hero-home-value-search`, `home-value-results-cta`, `community-tile:Walnut`, `nav-sell`
- `page_url`
- `utm_source`, `utm_medium`, `utm_campaign`: read from the URL and remembered for the browser session
- `submitted_at`: ISO timestamp

## 4. Placeholders to replace

Search the project for `[` to find them:

| Placeholder | Where |
|---|---|
| `[PHONE]` | `index.html` (contact, success message, footer, JSON-LD) and `thank-you.html`. `tel:[PHONE]` links work with formats like `+1-626-555-0123`. |
| `[EMAIL]` | `index.html` (contact, footer, JSON-LD) and `thank-you.html` |
| `[OFFICE ADDRESS]` | `index.html` (contact, footer, JSON-LD) |
| `[SITE URL]` | `index.html` `<head>`: canonical, `og:url`, JSON-LD `url`/`image`. Use the live domain without a trailing slash. |
| `[Languages placeholder]` | About section. Also update `knowsLanguage` in the JSON-LD. |
| `[Address], [City]`, `[Price] · [Beds]…` | The 3 "Sample listing" cards in Buy. Replace them with real listings (with the seller's/listing agent's permission) or keep them clearly labeled as samples. |
| `<!-- IDX search embed goes here -->` | Buy section. Paste your IDX vendor's embed code there. **Also add the vendor's domains to the `Content-Security-Policy` in `netlify.toml`** (`script-src`, `frame-src`, `img-src`, `connect-src`), or the browser will block the embed. |
| Privacy policy `href="#"` | Footer and both consent checkboxes |
| Unsplash photos | All are listed in the comment at the top of `index.html`. They're placeholders; replace them with licensed photos. |
| `images/jian-xing-wu.jpg` | Swap in a professional headshot if you like (any ~4:5 or square image works). |

## 5. How the home value flow works

1. The visitor types an address in the hero search bar.
2. They click **Get My Home Value**. A short step 2 asks for name, phone, email, selling timeline and consent.
3. The full `home-value` form posts to Netlify Forms. The lead is saved before any number is shown.
4. The browser calls `/.netlify/functions/home-value?address=…`, which calls RentCast `GET /v1/avm/value`.
5. The results panel shows:
   - the estimate and its range
   - up to 3 nearby comparables
   - the disclaimer
   - links to the same address on Zillow, plus Google searches limited to Redfin and Realtor.com
   - a **Get my free detailed market analysis from Jian** button, which pre-fills the main form with the address, "Sell", and the contact info

Zillow, Redfin and Realtor.com are only linked to, never scraped. None of them offer a public valuation API.

## 6. Compliance notes

- The testimonials section shows "Client review coming soon." Add real reviews only, with each client's permission.
- Don't add "top producer", rankings, award or experience claims.
- Don't add Pinnacle or Keller Williams logos without brokerage approval.
- Ask the brokerage to review the consent wording before running SMS campaigns. Consent is required to submit, but the wording says it is not a condition of purchase.
