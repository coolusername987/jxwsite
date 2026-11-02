# Jian-Xing Wu, REALTOR® | website

A static site in plain HTML, CSS and vanilla JS, built by a small Python script. It has one Netlify Function for home-value lookups. There are no frameworks and no npm dependencies.

```
site.config.json                 business details: name, phone, email, address, service area, hours, social links
src/index.html                   main page template (inline CSS + JS); {{tokens}} are filled in at build time
src/images/                      headshot, favicon and app icons
scripts/build.py                 builds everything into dist/ (also holds the city-page content)
netlify/functions/home-value.js  server-side RentCast valuation lookup
netlify.toml                     build command, publish dir (dist), functions dir, headers
dist/                            build output (git-ignored; Netlify builds it on every deploy)
```

`scripts/build.py` produces:
- `/`: the main page
- the city pages `/diamond-bar/`, `/walnut/`, `/rowland-heights/`, `/hacienda-heights/`, `/pomona/`, `/chino-hills/`, `/west-covina/` and `/el-monte/`
- `/privacy/`, `/thank-you.html` and `/404.html`
- `sitemap.xml`, `robots.txt` and `site.webmanifest`

## 1. Build and test locally

```
python3 scripts/build.py                     # writes dist/
python3 -m http.server 8000 --directory dist # browse http://localhost:8000
```

To run the valuation function locally too, install the Netlify CLI and run `netlify dev`.
Netlify Forms only accept submissions on a deployed site. Locally, a form POST fails and the page shows its error message, which is expected.

Edit `src/`, `site.config.json` or `scripts/build.py`. Never edit `dist/`, because it's rebuilt from scratch every time.

## 2. Business details (`site.config.json`)

All business details live in this one file and flow into every page, the footer and the structured data:
- phone, email and office address
- service area, services and languages
- hours and social links

If a field is empty, it's left out of the site and the structured data. It never shows up as placeholder text.

| Field | Status |
|---|---|
| `phone` | **Set:** (626) 465-8068 / `+16264658068` |
| `siteUrl` | Empty: the build uses `SITE_URL`, then Netlify's `URL` (see below) |
| `email` | **Needed.** Shown in the contact section, footer and structured data once set |
| `address` | **Needed.** Office street address, city and ZIP (only CA/US are filled in) |
| `languages` | **Needed.** e.g. `["English", "Mandarin"]` |
| `hours` | Optional. schema.org opening hours, e.g. `[{"days": ["Monday","Tuesday","Wednesday","Thursday","Friday"], "opens": "09:00", "closes": "18:00"}]` |
| `social` | Optional. Full profile URLs (Instagram, LinkedIn, Zillow agent profile…); used for footer links and `sameAs` |
| `privacyContact` | Optional. Email for privacy requests; falls back to the email, then the phone |

### Canonical domain

Canonical URLs, Open Graph URLs, structured data and the sitemap all use one base URL. The first value that's set wins:

1. the `SITE_URL` environment variable
2. `siteUrl` in `site.config.json`
3. Netlify's built-in `URL` variable, which is the site's **primary domain**
4. `https://jxwsite.netlify.app` (local builds)

Once a custom domain is connected and set as primary in Netlify, step 3 switches to it automatically. Netlify also redirects the `.netlify.app` address to the primary domain. Setting `SITE_URL` (or `siteUrl`) pins the canonical domain explicitly. Do that once the domain is final.

Deploy previews and branch deploys are built as **noindex**: a `noindex` robots meta tag, an `X-Robots-Tag` header and `Disallow: /` in robots.txt. Only production is indexable.

## 3. Deploy to Netlify

1. In Netlify, import the GitHub repo. The build command (`python3 scripts/build.py`) and the publish directory (`dist`) come from `netlify.toml`.
2. **Turn on form detection.** Go to **Site configuration → Forms → Enable form detection**, then redeploy so Netlify finds the `lead` and `home-value` forms.
3. Add the environment variables below and redeploy.

| Variable | Required | Scope | Purpose |
|---|---|---|---|
| `RENTCAST_API_KEY` | Yes, for estimates | Functions | Key from https://app.rentcast.io/app/api. It's used only inside the function and never sent to the browser. |
| `SITE_URL` | Recommended once the domain is final | Builds | Production domain, e.g. `https://www.example.com`, no trailing slash |
| `GOOGLE_MAPS_API_KEY` | Optional | Builds | Turns on address autocomplete. The build writes it into the page, so it's public by design. Restrict it to your domain (HTTP referrers) and to **Places API (New)** + **Maps JavaScript API**. |

If `RENTCAST_API_KEY` is missing or a lookup fails, the visitor is still thanked. They're told Jian will follow up with a personalized estimate within 24 hours, and their contact info is already saved in Netlify Forms.

### RentCast quota / rate limiting

The RentCast free tier allows about **50 lookups per month**. The function guards that quota in a few ways:
- It caches each address for 24 hours.
- It allows **3 lookups per IP per 24 hours** (`MAX_LOOKUPS_PER_IP`).
- The site only calls it after the visitor gives their contact details.

The cache and limit live in memory, so they only apply within one warm function instance. They're a soft guard, not a hard limit. For stronger protection:
- Set a usage cap or billing alert in RentCast. This is the real backstop.
- Move to Netlify Functions v2 and use `config.rateLimit`. Or store counts in Netlify Blobs.

## 4. Form email notifications

Set this up separately for **each** form:

1. **Site configuration → Notifications → Emails and webhooks → Form submission notifications**.
2. Click **Add notification → Email notification**, choose "New form submission", pick the form `lead`, enter Jian's email and save.
3. Repeat for `home-value`.

Every submission includes these hidden fields:
- `lead_source`: which button or section it came from, e.g.:
  - `hero-home-value-search`
  - `home-value-results-cta`
  - `community-tile:Walnut`
  - `city-walnut`
  - `mobile-cta-bar`
  - `closing-cta`
- `page_url`
- `utm_source`, `utm_medium`, `utm_campaign`
- `submitted_at`

The honeypot field (`bot-field`) sends spam to Netlify's spam list.

## 5. Page layout

Main page, top to bottom:

1. **Home Lookup:** the hero with the home-value search bar.
2. **Home value results:** hidden until someone uses the search.
3. **Booking form** ("Book a free consultation", form name `lead`). It sits **directly below Home Lookup**. A large click-to-call phone box sits beside it.
4. **Services:** buy, sell, home value.
5. **Buy:** the IDX placeholder and the sample listings.
6. **Communities:** links to each city page.
7. **Recent deals.**
8. **About.**
9. **Testimonials.**
10. **Closing call to action:** "Book a Free Consultation" plus a call button.
11. **Footer:** phone, DRE numbers, areas served, Equal Housing Opportunity statement, privacy policy.

The phone number appears in the header, the hero, the booking area, the closing call to action and the footer. On phones, a call/book bar is also pinned to the bottom of the screen. Every phone link uses `tel:+16264658068`.

## 6. How the home value flow works

1. A visitor enters an address in the hero search bar, or on a city page.
2. Step 2 (a dialog) asks for name, phone, email, selling timeline and consent.
3. The `home-value` form posts to Netlify Forms first, so the lead is saved before any number is shown.
4. The browser calls `/.netlify/functions/home-value?address=…`, which calls RentCast `GET /v1/avm/value`.
5. The results panel shows:
   - the estimate and its range
   - up to 3 nearby comparables
   - the disclaimer
   - Zillow, Redfin and Realtor.com links
   - a **Get my free detailed market analysis from Jian** button that pre-fills the booking form

Zillow, Redfin and Realtor.com are only linked to, never scraped.

## 7. City pages (local SEO)

The city pages are real, indexable pages with local content, not redirects. Each one has:
- its own title ("{City} Real Estate Agent | Jian-Xing Wu, REALTOR®"), meta description and canonical URL
- Open Graph and Twitter tags
- structured data: WebPage, BreadcrumbList and RealEstateAgent
- a home-value search and booking buttons that pass the city or address to the main page

To edit their content, change `CITIES` in `scripts/build.py`. To add or remove a city from the site, also update `serviceArea.cities` in `site.config.json`. The build stops with an error if a configured city has no content.

**Before launch:** have Jian review each city's facts (county, school districts, freeways, landmarks) and add Jian's own local knowledge.

## 8. Remaining placeholders

| Item | Where |
|---|---|
| Email, office address, languages, hours, social links | `site.config.json` (see section 2) |
| The 3 "Sample listing" cards in Buy (`[Address], [City]`, `[Price]…`) | `src/index.html`. Replace them with real listings (with permission) or keep them labeled as samples. |
| `<!-- IDX search embed goes here -->` | `src/index.html`. Also add the IDX vendor's domains to the `Content-Security-Policy` in `netlify.toml`. |
| Unsplash photos | Listed in the comment at the top of `src/index.html`. They're placeholders; replace them with licensed photos. |
| Privacy policy text | Generated at `/privacy/` from `scripts/build.py`. Have the broker or an attorney review it. |

## 9. SEO checklist after launch

- Connect the custom domain, set it as primary in Netlify, and set `SITE_URL`.
- Verify the domain in **Google Search Console**, submit `/sitemap.xml`, and use URL Inspection on `/` and a city page.
- Create or claim a **Google Business Profile**. Use the exact same name and phone number, (626) 465-8068, and the same service area. Link it to the site.
- Keep the name, phone and brokerage identical on Zillow, Realtor.com, Yelp, the brokerage roster and social profiles, and add those profile URLs to `social` in the config.
- Ask satisfied clients for Google reviews. Only add real reviews, with permission, to the Testimonials section.
- Test the structured data with Google's Rich Results Test and validator.schema.org once the site is live.
- Optional: add privacy-friendly analytics (e.g. Netlify Analytics or Plausible) and update `/privacy/` if you do.

## 10. Compliance notes

- Testimonials show "Client review coming soon." Add real reviews only, with each client's permission.
- Don't add "top producer", rankings, award or experience claims.
- Don't add Pinnacle or Keller Williams logos without brokerage approval.
- Have the brokerage review the SMS consent wording and the privacy policy. Consent is required to submit, but the wording says it is not a condition of purchase.
