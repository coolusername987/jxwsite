#!/usr/bin/env python3
"""Build the static site into dist/.

    python3 scripts/build.py

Netlify runs this on every deploy (see netlify.toml). It:
  * renders src/index.html, filling in business details from site.config.json
  * generates the city pages (/diamond-bar/, /walnut/, ...), /privacy/, /thank-you.html and 404.html
  * writes per-page SEO tags (title, description, canonical, Open Graph, Twitter) and JSON-LD
  * writes sitemap.xml, robots.txt and site.webmanifest
  * marks deploy previews / branch deploys as noindex

Canonical domain, in order of precedence:
  1. SITE_URL environment variable
  2. "siteUrl" in site.config.json
  3. URL environment variable (set by Netlify to the site's primary domain)
  4. https://jxwsite.netlify.app (local builds)

Standard library only, Python 3.8+.
"""
import json
import os
import re
import shutil
import sys
from html import escape
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
DIST = ROOT / "dist"
CONFIG = json.loads((ROOT / "site.config.json").read_text(encoding="utf-8"))
FALLBACK_URL = "https://jxwsite.netlify.app"


def resolve_site_url():
    for value in (os.environ.get("SITE_URL"), CONFIG.get("siteUrl"), os.environ.get("URL")):
        if value and value.strip():
            return value.strip().rstrip("/")
    return FALLBACK_URL


SITE = resolve_site_url()
CONTEXT = os.environ.get("CONTEXT", "production")  # Netlify sets production / deploy-preview / branch-deploy
INDEXABLE = CONTEXT == "production"

e = escape
PHONE = CONFIG["phone"]["display"]
PHONE_HREF = "tel:" + CONFIG["phone"]["e164"]
EMAIL = CONFIG.get("email", "").strip()
ADDR = CONFIG.get("address", {})
LIC = CONFIG["license"]
LANGUAGES = [l for l in CONFIG.get("languages", []) if l.strip()]
SOCIAL = [u for u in CONFIG.get("social", []) if u.strip()]
HOURS = CONFIG.get("hours", [])


def address_display():
    if not ADDR.get("streetAddress"):
        return ""
    line2 = " ".join(p for p in [
        ", ".join(p for p in [ADDR.get("addressLocality", ""), ADDR.get("addressRegion", "")] if p),
        ADDR.get("postalCode", ""),
    ] if p)
    return ", ".join(p for p in [ADDR["streetAddress"], line2] if p)


ADDRESS = address_display()

IMG = "https://images.unsplash.com/photo-{}?w={}&q=80&auto=format"
HERO_PHOTO = "1600585154340-be6161a56a0c"
HERO_ALT = "Modern two-story home with floor-to-ceiling glass windows and a lawn beneath a large tree"


def og_image(photo):
    return "https://images.unsplash.com/photo-{}?w=1200&h=630&fit=crop&q=80".format(photo)


def srcset(photo, widths):
    return ", ".join("{} {}w".format(e(IMG.format(photo, w)), w) for w in widths)


PHONE_ICON = ('<svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path fill="currentColor" '
              'd="M6.6 10.8a15.1 15.1 0 0 0 6.6 6.6l2.2-2.2a1 1 0 0 1 1-.25c1.12.37 2.33.57 3.6.57a1 1 0 0 1 1 1V20a1 1 0 0 1-1 '
              '1A17 17 0 0 1 3 4a1 1 0 0 1 1-1h3.5a1 1 0 0 1 1 1c0 1.27.2 2.48.57 3.6a1 1 0 0 1-.25 1z"/></svg>')
SEARCH_ICON = ('<svg width="20" height="20" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path fill="currentColor" '
               'd="M15.5 14h-.79l-.28-.27A6.47 6.47 0 0 0 16 9.5 6.5 6.5 0 1 0 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 '
               '4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/></svg>')

# --------------------------------------------------------------------------------------------
# City content. Facts are kept to verifiable basics; have Jian review and add local knowledge.
# --------------------------------------------------------------------------------------------
CITIES = [
    {
        "slug": "diamond-bar",
        "name": "Diamond Bar",
        "photo": "1600596542815-ffad4c1539a9",
        "alt": "White modern home with a rooftop terrace beside a swimming pool",
        "lede": "Hillside neighborhoods, a central freeway location, and steady demand from families. Here's how I help buyers and sellers in Diamond Bar.",
        "living": [
            "Diamond Bar is a city in eastern Los Angeles County, set in rolling hills where the 57 and 60 freeways meet. Most of the city is residential, with single-family homes on winding streets, plus townhomes and condos closer to the main corridors.",
            "Neighborhoods range from established tracts to The Country Estates, a guard-gated community in the hills. Most of the city is served by Walnut Valley Unified, with some areas in Pomona Unified, so school assignments are worth confirming for any specific address.",
        ],
        "facts": [
            ("County", "Los Angeles"),
            ("School districts", "Walnut Valley USD; parts of Pomona USD"),
            ("Getting around", "SR-57 and SR-60"),
        ],
        "buying": "In hillside areas I look closely at slope, HOA rules where they apply, and recent sales on the same street, not just the ZIP code.",
        "nearby": ["walnut", "rowland-heights", "chino-hills", "pomona"],
    },
    {
        "slug": "walnut",
        "name": "Walnut",
        "photo": "1600047509807-ba8f99d2cdde",
        "alt": "Modern home with a wood-clad upper story, large windows, and a front lawn",
        "lede": "Quiet, low-density neighborhoods and a small-town feel in the east San Gabriel Valley.",
        "living": [
            "Walnut is a city in the east San Gabriel Valley in Los Angeles County, known for low-density residential neighborhoods, open space, and trails, including equestrian areas in parts of the city.",
            "Mt. San Antonio College is located in Walnut. The city is served mainly by Walnut Valley Unified, with some areas in Rowland Unified, so confirm school assignments for the exact address you're considering.",
        ],
        "facts": [
            ("County", "Los Angeles"),
            ("School districts", "Walnut Valley USD; parts of Rowland USD"),
            ("Getting around", "SR-60, with SR-57 nearby"),
        ],
        "buying": "Larger lots and fewer listings mean the right home may not come up often, so I set up alerts and move quickly when it does.",
        "nearby": ["diamond-bar", "rowland-heights", "west-covina", "pomona"],
    },
    {
        "slug": "rowland-heights",
        "unincorporated": True,
        "name": "Rowland Heights",
        "photo": "1600566753190-17f0baa2a6c3",
        "alt": "Two-story modern home with timber and dark cladding and a glass upper level",
        "lede": "An unincorporated community with a busy dining and shopping scene along Colima Road.",
        "living": [
            "Rowland Heights is an unincorporated community in Los Angeles County, between Hacienda Heights and Diamond Bar along the 60 freeway. Colima Road is lined with restaurants, markets, and shops, many of them Asian-owned.",
            "Homes range from single-family neighborhoods on the hillsides to townhomes and condos near the main roads. Most of the area is served by Rowland Unified, with some parts in Hacienda La Puente Unified.",
        ],
        "facts": [
            ("County", "Los Angeles (unincorporated)"),
            ("School districts", "Rowland USD; parts of Hacienda La Puente USD"),
            ("Getting around", "SR-60, with SR-57 nearby"),
        ],
        "buying": "Because Rowland Heights is unincorporated, permits and many services run through Los Angeles County rather than a city hall. I help buyers check permit history before they commit.",
        "nearby": ["hacienda-heights", "diamond-bar", "walnut", "west-covina"],
    },
    {
        "slug": "hacienda-heights",
        "unincorporated": True,
        "name": "Hacienda Heights",
        "photo": "1600563438938-a9a27216b4f5",
        "alt": "Modern gabled home behind a dark slatted fence under a clear blue sky",
        "lede": "Established hillside neighborhoods in the Puente Hills, minutes from the 60 freeway.",
        "living": [
            "Hacienda Heights is an unincorporated community in Los Angeles County on the slopes of the Puente Hills. Many neighborhoods are made up of established single-family homes, some with views across the San Gabriel Valley.",
            "It's home to Hsi Lai Temple, one of the area's best-known landmarks. The community is served by Hacienda La Puente Unified.",
        ],
        "facts": [
            ("County", "Los Angeles (unincorporated)"),
            ("School district", "Hacienda La Puente USD"),
            ("Getting around", "SR-60, with I-605 to the west"),
        ],
        "buying": "Older homes can come with additions that were updated, or never permitted. I compare each listing to public records and flag questions early.",
        "nearby": ["rowland-heights", "west-covina", "el-monte", "walnut"],
    },
    {
        "slug": "pomona",
        "name": "Pomona",
        "photo": "1523217582562-09d0def993a6",
        "alt": "Minimal white stucco home with stacked geometric forms",
        "lede": "Historic neighborhoods, a university town, and a wide range of homes and price points.",
        "living": [
            "Pomona is a city at the eastern edge of Los Angeles County. It's home to Cal Poly Pomona, where I study real estate, and the Fairplex, which hosts the LA County Fair.",
            "Housing ranges from historic homes in older neighborhoods such as Lincoln Park to newer tracts and condos. Most of the city is served by Pomona Unified.",
        ],
        "facts": [
            ("County", "Los Angeles"),
            ("School district", "Pomona USD"),
            ("Getting around", "I-10, SR-60, SR-71; Metrolink service"),
        ],
        "buying": "Pomona's mix of home ages and styles makes comparable sales tricky. I pull comps block by block, not citywide.",
        "nearby": ["diamond-bar", "chino-hills", "walnut", "west-covina"],
    },
    {
        "slug": "chino-hills",
        "name": "Chino Hills",
        "photo": "1512917774080-9991f1c4c750",
        "alt": "Single-story modern home with glass walls opening onto a pool deck",
        "lede": "Newer neighborhoods and open space on the Inland Empire side of the hills.",
        "living": [
            "Chino Hills is a city in San Bernardino County, at the western edge of the Inland Empire. Much of it was developed as planned neighborhoods, with parks, trails, and Chino Hills State Park along its edges.",
            "Many homes are in communities with HOAs, and some carry Mello-Roos special taxes. The city is served by Chino Valley Unified.",
        ],
        "facts": [
            ("County", "San Bernardino"),
            ("School district", "Chino Valley USD"),
            ("Getting around", "SR-71, with SR-60 and SR-57 nearby"),
        ],
        "buying": "I check HOA dues and any Mello-Roos taxes up front, so the monthly payment you plan for is the real one.",
        "nearby": ["diamond-bar", "pomona", "walnut", "rowland-heights"],
    },
    {
        "slug": "west-covina",
        "name": "West Covina",
        "photo": "1564013799919-ab600027ffc6",
        "alt": "White two-story home with a wraparound balcony and a pool framed by palm trees",
        "lede": "Central San Gabriel Valley living along the 10 freeway, with a wide range of homes.",
        "living": [
            "West Covina is a city in the San Gabriel Valley in Los Angeles County, along Interstate 10. Shopping centers on Plaza West Covina, and neighborhoods range from flat tracts to hillside areas in the south of the city.",
            "Several school districts serve parts of West Covina, including West Covina Unified, Covina-Valley Unified, and Rowland Unified, so the assigned schools depend on the exact address.",
        ],
        "facts": [
            ("County", "Los Angeles"),
            ("School districts", "West Covina USD, Covina-Valley USD, Rowland USD (by area)"),
            ("Getting around", "I-10, with SR-57 and I-605 nearby"),
        ],
        "buying": "Two homes a mile apart can sit in different school districts. I confirm boundaries for every home on your shortlist.",
        "nearby": ["el-monte", "hacienda-heights", "walnut", "pomona"],
    },
    {
        "slug": "el-monte",
        "name": "El Monte",
        "photo": "1600573472550-8090b5e0745e",
        "alt": "Interior with a floating staircase and a glass wall looking out to a pool",
        "lede": "A central location, transit to downtown LA, and single-family homes, where I recently represented a buyer.",
        "living": [
            "El Monte is a city in the western San Gabriel Valley in Los Angeles County, along Interstate 10. The El Monte Bus Station connects to downtown Los Angeles, and Metrolink also stops in the city.",
            "Housing includes single-family homes, townhomes, and multi-unit properties. Schools are split among several districts, including El Monte City, Mountain View, and El Monte Union High School districts.",
        ],
        "facts": [
            ("County", "Los Angeles"),
            ("School districts", "El Monte City SD, Mountain View SD, El Monte Union HSD"),
            ("Getting around", "I-10 and I-605; El Monte Bus Station; Metrolink"),
        ],
        "buying": "Single-family and multi-unit homes often share the same streets here. I help buyers compare them on real numbers: monthly payment, condition, and rental potential.",
        "deal": ("Single-family home", "$779K"),
        "nearby": ["west-covina", "hacienda-heights", "rowland-heights", "walnut"],
    },
]

BY_SLUG = {c["slug"]: c for c in CITIES}
BY_NAME = {c["name"]: c for c in CITIES}
missing = [n for n in CONFIG["serviceArea"]["cities"] if n not in BY_NAME]
if missing:
    sys.exit("site.config.json lists cities with no page content in scripts/build.py: " + ", ".join(missing))
SERVICE_CITIES = [BY_NAME[n] for n in CONFIG["serviceArea"]["cities"]]


# --------------------------------------------------------------------------------------------
# Shared head + structured data
# --------------------------------------------------------------------------------------------
def head(title, description, path, photo=HERO_PHOTO, photo_alt=HERO_ALT, index=True, extra=""):
    url = SITE + path
    robots = "index, follow, max-image-preview:large" if (index and INDEXABLE) else "noindex, follow"
    canonical = '\n  <link rel="canonical" href="{}">'.format(e(url)) if index else ""
    return """  <title>{title}</title>
  <meta name="description" content="{desc}">
  <meta name="robots" content="{robots}">{canonical}
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="{site_name}">
  <meta property="og:locale" content="en_US">
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{desc}">
  <meta property="og:url" content="{url}">
  <meta property="og:image" content="{image}">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:image:alt" content="{alt}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{title}">
  <meta name="twitter:description" content="{desc}">
  <meta name="twitter:image" content="{image}">
  <meta name="twitter:image:alt" content="{alt}">
  <meta name="theme-color" content="#FAFAF8">
  <meta name="format-detection" content="telephone=no">
  <link rel="icon" href="/images/favicon.svg" type="image/svg+xml">
  <link rel="icon" href="/images/icon-192.png" sizes="192x192" type="image/png">
  <link rel="apple-touch-icon" href="/images/apple-touch-icon.png">
  <link rel="manifest" href="/site.webmanifest">{extra}""".format(
        title=e(title), desc=e(description), robots=robots, canonical=canonical,
        site_name=e(CONFIG["businessName"]), url=e(url), image=e(og_image(photo)), alt=e(photo_alt),
        extra=extra)


def place(city):
    return {"@type": "Place" if city.get("unincorporated") else "City", "name": city["name"] + ", CA"}


def agent_node(area=None):
    node = {
        "@type": "RealEstateAgent",
        "@id": SITE + "/#agent",
        "name": CONFIG["businessName"],
        "alternateName": [CONFIG["agentName"], CONFIG["agentShortName"]],
        "description": CONFIG["description"],
        "url": SITE + "/",
        "telephone": CONFIG["phone"]["e164"],
        "image": SITE + "/images/jian-xing-wu.jpg",
        "logo": SITE + "/images/icon-512.png",
        "address": {"@type": "PostalAddress", **{k: v for k, v in ADDR.items() if v}},
        "areaServed": area or ([place(c) for c in SERVICE_CITIES]
                               + [{"@type": "Place", "name": r} for r in CONFIG["serviceArea"]["regions"]]),
        "identifier": "California DRE #" + LIC["agent"],
        "hasCredential": {
            "@type": "EducationalOccupationalCredential",
            "credentialCategory": "license",
            "name": "California DRE License #" + LIC["agent"],
            "recognizedBy": {"@type": "GovernmentOrganization", "name": "California Department of Real Estate"},
        },
        "parentOrganization": {
            "@type": "RealEstateAgent",
            "name": LIC["brokerage"],
            "legalName": LIC["brokerageLegalName"],
            "identifier": "California DRE #" + LIC["broker"],
        },
        "makesOffer": [
            {"@type": "Offer", "itemOffered": {
                "@type": "Service", "name": s["name"], "description": s["description"],
                "provider": {"@id": SITE + "/#agent"},
                "areaServed": [{"@type": "Place", "name": r} for r in CONFIG["serviceArea"]["regions"]],
            }} for s in CONFIG["services"]
        ],
    }
    if EMAIL:
        node["email"] = EMAIL
    if LANGUAGES:
        node["knowsLanguage"] = LANGUAGES
    if SOCIAL:
        node["sameAs"] = SOCIAL
    if HOURS:
        node["openingHoursSpecification"] = [
            {"@type": "OpeningHoursSpecification", "dayOfWeek": h["days"], "opens": h["opens"], "closes": h["closes"]}
            for h in HOURS
        ]
    return node


def website_node():
    return {"@type": "WebSite", "@id": SITE + "/#website", "url": SITE + "/", "name": CONFIG["businessName"],
            "inLanguage": "en-US", "publisher": {"@id": SITE + "/#agent"}}


def jsonld(*nodes):
    data = {"@context": "https://schema.org", "@graph": list(nodes)}
    text = json.dumps(data, indent=2, ensure_ascii=False).replace("</", "<\\/")
    return '  <script type="application/ld+json">\n{}\n  </script>'.format(text)


def breadcrumbs(items):
    return {"@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": name, "item": SITE + path}
        for i, (name, path) in enumerate(items)
    ]}


# --------------------------------------------------------------------------------------------
# Templating for src/index.html: {{token}} and {{#flag}}...{{/flag}} (kept only when flag is truthy)
# --------------------------------------------------------------------------------------------
def render(template, ctx):
    out = re.sub(r"\{\{#(\w+)\}\}(.*?)\{\{/\1\}\}", lambda m: m.group(2) if ctx.get(m.group(1)) else "", template, flags=re.S)

    def token(m):
        if m.group(1) not in ctx:
            sys.exit("Unknown template token: {{%s}}" % m.group(1))
        return str(ctx[m.group(1)])
    out = re.sub(r"\{\{(\w+)\}\}", token, out)
    if "{{" in out:
        sys.exit("Unrendered template token left in output")
    return out


def footer_areas(current=None, indent="          "):
    items = []
    for c in SERVICE_CITIES:
        if c["slug"] == current:
            items.append('{}<li><span aria-current="page">{}</span></li>'.format(indent, e(c["name"])))
        else:
            items.append('{}<li><a href="/{}/">{} real estate</a></li>'.format(indent, c["slug"], e(c["name"])))
    return "\n".join(items)


def social_links():
    if not SOCIAL:
        return ""
    def label(url):
        host = re.sub(r"^https?://(www\.)?", "", url).split("/")[0]
        return host.split(".")[0].capitalize()
    lis = "".join('<li><a href="{0}" rel="me noopener" target="_blank">{1}<span class="sr-only"> (opens in a new tab)</span></a></li>'.format(e(u), e(label(u))) for u in SOCIAL)
    return '          <ul class="footer-social">{}</ul>\n'.format(lis)


def build_index():
    template = (SRC / "index.html").read_text(encoding="utf-8")
    extra = '\n  <link rel="preload" as="image" href="{}" imagesrcset="{}" imagesizes="100vw" fetchpriority="high">'.format(
        e(IMG.format(HERO_PHOTO, 1600)), srcset(HERO_PHOTO, [800, 1200, 1600, 2000]))
    ctx = {
        "head": head("Jian-Xing Wu | REALTOR® in Diamond Bar, Walnut & the San Gabriel Valley",
                     "REALTOR® Jian-Xing Wu helps buyers and sellers in Diamond Bar, Walnut & the San Gabriel Valley. "
                     "Get a free home value estimate or call " + PHONE + ".",
                     "/", extra=extra),
        "jsonld": jsonld(website_node(), agent_node(), {
            "@type": "WebPage", "@id": SITE + "/#webpage", "url": SITE + "/",
            "name": "Jian-Xing Wu | REALTOR® in Diamond Bar, Walnut & the San Gabriel Valley",
            "isPartOf": {"@id": SITE + "/#website"}, "about": {"@id": SITE + "/#agent"},
            "primaryImageOfPage": IMG.format(HERO_PHOTO, 1600),
        }),
        "phone_display": e(PHONE),
        "phone_href": e(PHONE_HREF),
        "email": e(EMAIL),
        "address": ADDRESS,
        "address_display": e(ADDRESS),
        "languages": e(", ".join(LANGUAGES)),
        "footer_areas": footer_areas(),
        "social_links": social_links(),
    }
    html = render(template, ctx)
    key = os.environ.get("GOOGLE_MAPS_API_KEY", "").strip()
    if key:
        if not re.fullmatch(r"[A-Za-z0-9_-]+", key):
            sys.exit("GOOGLE_MAPS_API_KEY contains unexpected characters")
        html = html.replace("__GOOGLE_MAPS_API_KEY__", key)
    write("index.html", html)


# --------------------------------------------------------------------------------------------
# Sub-page layout (city pages, privacy, thank-you, 404)
# --------------------------------------------------------------------------------------------
CSS = """
:root{--bg:#FAFAF8;--surface:#fff;--ink:#111;--muted:#55554F;--line:#E4E3DE;--line-strong:#C9C7C0;--accent:#2C3E57;--accent-hover:#1F2D40;--radius:3px;--gutter:24px;--serif:"Cormorant Garamond",Georgia,"Times New Roman",serif;--sans:"Inter",system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif}
*,*::before,*::after{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--sans);font-size:1.0625rem;line-height:1.65;-webkit-font-smoothing:antialiased;overflow-x:clip}
img{display:block;max-width:100%;height:auto}
a{color:inherit}
h1,h2,h3{font-family:var(--serif);font-weight:500;line-height:1.08;letter-spacing:-.01em;margin:0 0 .5em}
h2{font-size:clamp(2rem,4.2vw,3.1rem)}
h3{font-size:1.55rem}
p{margin:0 0 1em}
ul,ol{margin:0;padding:0}
:focus-visible{outline:2px solid var(--accent);outline-offset:3px}
.container{width:100%;max-width:1200px;margin:0 auto;padding:0 var(--gutter)}
.skip-link{position:absolute;left:16px;top:-60px;z-index:200;background:var(--ink);color:#fff;padding:10px 16px;text-decoration:none}
.skip-link:focus{top:12px}
.sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}
.eyebrow{font-size:.75rem;font-weight:600;letter-spacing:.16em;text-transform:uppercase;color:var(--muted);margin:0 0 1.1rem}
.lede{font-size:1.125rem;color:var(--muted);max-width:620px}
.btn{display:inline-flex;align-items:center;justify-content:center;gap:8px;min-height:52px;padding:14px 28px;font:inherit;font-size:.9375rem;font-weight:600;line-height:1.2;border:1px solid transparent;border-radius:var(--radius);cursor:pointer;text-decoration:none;text-align:center;transition:background-color .2s,color .2s}
.btn-primary{background:var(--accent);color:#fff}
.btn-primary:hover{background:var(--accent-hover)}
.btn-outline{border-color:var(--ink);color:var(--ink)}
.btn-outline:hover{background:var(--ink);color:#fff}
.text-link{font-weight:500;text-decoration:underline;text-underline-offset:5px;text-decoration-thickness:1px}
.site-header{position:sticky;top:0;z-index:50;background:rgba(250,250,248,.97);border-bottom:1px solid var(--line)}
.header-inner{display:flex;align-items:center;gap:10px 24px;flex-wrap:wrap;max-width:1200px;min-height:68px;margin:0 auto;padding:10px var(--gutter)}
.wordmark{margin-right:auto;font-size:.875rem;font-weight:600;letter-spacing:.26em;text-decoration:none;white-space:nowrap}
.nav ul{display:flex;flex-wrap:wrap;gap:4px 24px;list-style:none}
.nav a{display:inline-block;padding:6px 0;font-size:.78rem;font-weight:500;letter-spacing:.14em;text-transform:uppercase;text-decoration:none;border-bottom:1px solid transparent}
.nav a:hover{border-bottom-color:var(--ink)}
.header-phone{display:inline-flex;align-items:center;gap:8px;min-height:44px;padding:8px 14px;font-size:.875rem;font-weight:600;letter-spacing:.02em;white-space:nowrap;color:var(--accent);text-decoration:none;border:1px solid var(--accent);border-radius:var(--radius);transition:background-color .2s,color .2s}
.header-phone:hover{background:var(--accent);color:#fff}
@media (max-width:900px){.nav{order:3;flex-basis:100%}.nav ul{gap:2px 18px}}
@media (max-width:760px){.site-header{position:static}}
.crumbs{padding-top:18px;padding-bottom:18px;font-size:.8125rem;color:var(--muted)}
.crumbs ol{display:flex;flex-wrap:wrap;gap:6px;list-style:none}
.crumbs li+li::before{content:"/";margin-right:6px;color:var(--line-strong)}
.crumbs a{text-decoration:none}
.crumbs a:hover{text-decoration:underline}
.hero{position:relative;color:#fff;padding:clamp(80px,12vw,140px) 0}
.hero-media{position:absolute;inset:0;background:#2a2f36}
.hero-media img{width:100%;height:100%;object-fit:cover}
.hero-media::after{content:"";position:absolute;inset:0;background:rgba(12,16,22,.58)}
.hero>.container{position:relative}
.hero .eyebrow{color:rgba(255,255,255,.85)}
.hero h1{font-size:clamp(2.6rem,6.4vw,4.8rem);margin-bottom:.3em;max-width:820px}
.hero .lede{color:rgba(255,255,255,.9);margin-bottom:36px}
.hero-call{margin:16px 0 0;color:rgba(255,255,255,.9)}
.hero-call a{color:#fff;font-weight:600;text-underline-offset:4px;white-space:nowrap}
.search-label{display:block;margin-bottom:10px;font-size:.75rem;font-weight:600;letter-spacing:.16em;text-transform:uppercase;color:rgba(255,255,255,.9)}
.search-bar{display:flex;align-items:center;gap:12px;max-width:740px;padding:6px 6px 6px 20px;background:#fff;color:var(--ink);border-radius:4px;box-shadow:0 1px 3px rgba(0,0,0,.1),0 10px 30px rgba(0,0,0,.14)}
.search-bar:focus-within{outline:2px solid #fff;outline-offset:3px}
.search-bar svg{flex:none;color:#5F6368}
.search-bar input{flex:1;min-width:0;padding:14px 0;font:inherit;font-size:1.125rem;color:var(--ink);background:transparent;border:0;outline:none}
.search-bar input::placeholder{color:#6B6B66}
.search-bar .btn{flex:none}
@media (max-width:600px){.search-bar{flex-wrap:wrap;padding:6px;gap:0}.search-bar svg{margin:0 10px 0 12px}.search-bar input{padding:14px 8px 14px 0}.search-bar .btn{width:100%;margin-top:4px}}
.section{padding:clamp(64px,9vw,112px) 0;border-top:1px solid var(--line)}
.page-intro{padding:clamp(56px,8vw,96px) 0}
.page-intro h1{font-size:clamp(2.4rem,5.6vw,4rem)}
.prose{max-width:720px}
.prose h2{font-size:clamp(1.6rem,3vw,2rem);margin-top:1.6em}
.prose ul{padding-left:1.2em;margin:0 0 1em}
.prose li{margin-bottom:.4em}
.two-col{display:grid;grid-template-columns:minmax(0,7fr) minmax(0,5fr);gap:clamp(40px,7vw,96px);align-items:start}
@media (max-width:860px){.two-col{grid-template-columns:1fr}}
.facts{list-style:none;border-top:1px solid var(--line)}
.facts li{display:flex;flex-direction:column;gap:2px;padding:16px 0;border-bottom:1px solid var(--line);font-size:.9375rem}
.facts .k{font-size:.75rem;font-weight:600;letter-spacing:.13em;text-transform:uppercase;color:var(--muted)}
.note{font-size:.8125rem;color:var(--muted);margin-top:16px}
.steps{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:24px;list-style:none;margin-top:40px}
@media (max-width:860px){.steps{grid-template-columns:1fr}}
.steps li{padding:32px 28px;border:1px solid var(--line);border-radius:var(--radius);background:var(--surface)}
.steps p{margin:0;color:var(--muted)}
.deal{max-width:520px;margin-top:40px;padding:clamp(28px,4vw,40px);border:1px solid var(--line);border-radius:var(--radius);background:var(--surface)}
.deal-price{margin:0 0 6px;font-family:var(--serif);font-size:3rem;line-height:1}
.deal p:last-child{margin:0}
.actions{display:flex;flex-wrap:wrap;gap:12px;margin-top:36px}
.nearby{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:16px;list-style:none;margin-top:32px}
@media (max-width:860px){.nearby{grid-template-columns:repeat(2,minmax(0,1fr))}}
.nearby a{display:block;padding:22px 20px;border:1px solid var(--line);border-radius:var(--radius);background:var(--surface);text-decoration:none;font-family:var(--serif);font-size:1.4rem;line-height:1.15;transition:border-color .2s}
.nearby a:hover{border-color:var(--ink)}
.nearby span{display:block;margin-top:6px;font-family:var(--sans);font-size:.8125rem;color:var(--muted)}
.cta{background:var(--surface)}
.cta-inner{display:flex;justify-content:space-between;align-items:center;gap:24px 48px;flex-wrap:wrap}
.cta-inner h2{margin:0}
.cta-actions{display:flex;flex-wrap:wrap;gap:12px}
.site-footer{padding:56px 0 40px;border-top:1px solid var(--line);font-size:.875rem;color:var(--muted)}
.site-footer p{margin:0 0 6px}
.footer-top{display:flex;justify-content:space-between;gap:28px;flex-wrap:wrap;padding-bottom:28px;margin-bottom:24px;border-bottom:1px solid var(--line)}
.footer-top .wordmark{color:var(--ink)}
.footer-phone a{font-size:1.125rem;font-weight:600;color:var(--ink);text-decoration:none;border-bottom:1px solid var(--line-strong)}
.footer-social{display:flex;flex-wrap:wrap;gap:4px 14px;list-style:none;margin-top:8px}
.footer-social a{color:var(--ink)}
.areas{display:flex;flex-wrap:wrap;gap:6px 18px;list-style:none;margin:6px 0 20px}
.areas a{text-decoration:none;color:var(--ink)}
.areas a:hover{text-decoration:underline}
.mobile-cta{display:none}
@media (max-width:760px){body{padding-bottom:calc(76px + env(safe-area-inset-bottom))}.mobile-cta{position:fixed;left:0;right:0;bottom:0;z-index:40;display:grid;grid-template-columns:1fr 1fr;gap:8px;padding:10px 12px calc(10px + env(safe-area-inset-bottom));background:rgba(250,250,248,.97);border-top:1px solid var(--line)}.mobile-cta .btn{min-height:48px;padding:10px 12px;font-size:.875rem;white-space:nowrap}.mobile-cta .btn-outline{background:var(--surface)}.mobile-cta .btn-outline:hover{background:var(--ink);color:#fff}}
@media (max-width:480px){:root{--gutter:16px}.wordmark{letter-spacing:.2em}}
""".strip()


def page(title, description, path, body, *, photo=HERO_PHOTO, photo_alt=HERO_ALT, index=True, ld="",
         contact_href="/#contact", sell_href="/?intent=Sell#contact", current_city=None, preload=""):
    social = social_links()
    email_line = '\n          <p><a href="mailto:{0}">{0}</a></p>'.format(e(EMAIL)) if EMAIL else ""
    address_line = "\n          <p>{}</p>".format(e(ADDRESS)) if ADDRESS else ""
    return """<!doctype html>
<!-- Generated by scripts/build.py. Edit the script or site.config.json, not this file. -->
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
{head}
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link rel="preconnect" href="https://images.unsplash.com">
  <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
{ld}
  <style>
{css}
  </style>
</head>
<body>
  <a class="skip-link" href="#main">Skip to content</a>

  <header class="site-header">
    <div class="header-inner">
      <a class="wordmark" href="/" aria-label="Jian-Xing Wu, home">JIAN-XING WU</a>
      <nav class="nav" aria-label="Primary">
        <ul>
          <li><a href="/#buy">Buy</a></li>
          <li><a href="{sell}">Sell</a></li>
          <li><a href="/#value">Home Value</a></li>
          <li><a href="/#communities">Communities</a></li>
          <li><a href="/#about">About</a></li>
          <li><a href="{contact}">Contact</a></li>
        </ul>
      </nav>
      <a class="header-phone" href="{phone_href}">{icon}<span>{phone}</span></a>
    </div>
  </header>

  <main id="main">
{body}
  </main>

  <footer class="site-footer">
    <div class="container">
      <div class="footer-top">
        <div>
          <p class="wordmark">JIAN-XING WU</p>
          <p>REALTOR® | DRE #{agent}</p>
          <p>{brokerage} | {legal} | DRE #{broker}</p>
        </div>
        <div>
          <p class="footer-phone"><a href="{phone_href}">{phone}</a></p>{email_line}{address_line}
{social}        </div>
      </div>
      <p class="eyebrow" style="margin-bottom:4px">Areas served</p>
      <ul class="areas">
{areas}
      </ul>
      <p>Equal Housing Opportunity. Jian-Xing Wu and {brokerage} are committed to the federal Fair Housing Act and California fair housing laws.</p>
      <p>Photos are for illustration only and do not show specific listings.</p>
      <p>© 2026 Jian-Xing Wu. All rights reserved. · <a href="/privacy/">Privacy policy</a></p>
    </div>
  </footer>

  <div class="mobile-cta">
    <a class="btn btn-outline" href="{phone_href}">{icon}<span>{phone}</span></a>
    <a class="btn btn-primary" href="{contact}">Book a Consult</a>
  </div>
</body>
</html>
""".format(
        head=head(title, description, path, photo, photo_alt, index=index, extra=preload), ld=ld, css=CSS, body=body,
        sell=sell_href, contact=contact_href, phone=e(PHONE), phone_href=e(PHONE_HREF), icon=PHONE_ICON,
        agent=LIC["agent"], broker=LIC["broker"], brokerage=e(LIC["brokerage"]), legal=e(LIC["brokerageLegalName"]),
        email_line=email_line, address_line=address_line, social=social, areas=footer_areas(current_city, "        "))


def city_page(city):
    name, slug = city["name"], city["slug"]
    src = "city-" + slug
    path = "/{}/".format(slug)
    title = "{} Real Estate Agent | Jian-Xing Wu, REALTOR®".format(name)
    desc = ("Buying or selling in {}, CA? REALTOR® Jian-Xing Wu helps first-time buyers, families, and sellers. "
            "Free home value estimate. Call {}.").format(name, PHONE)
    contact_href = "/?area={}&amp;src={}#contact".format(quote(name), src)
    sell_href = "/?intent=Sell&amp;area={}&amp;src={}#contact".format(quote(name), src)

    facts = "\n".join('            <li><span class="k">{}</span><span>{}</span></li>'.format(e(k), e(v)) for k, v in city["facts"])
    living = "\n".join("          <p>{}</p>".format(e(p)) for p in city["living"])
    nearby = "\n".join(
        '          <li><a href="/{}/">{}<span>{} area guide →</span></a></li>'.format(s, e(BY_SLUG[s]["name"]), e(BY_SLUG[s]["name"]))
        for s in city["nearby"])
    deal = ""
    if city.get("deal"):
        kind, price = city["deal"]
        deal = """
        <article class="deal">
          <p class="eyebrow">Recently closed · Buyer side</p>
          <h3>{}</h3>
          <p class="deal-price">{}</p>
          <p>{} · Represented the buyer</p>
        </article>""".format(e(name), e(price), e(kind))

    body = """    <nav class="crumbs container" aria-label="Breadcrumb">
      <ol>
        <li><a href="/">Home</a></li>
        <li><a href="/#communities">Communities</a></li>
        <li><span aria-current="page">{name}</span></li>
      </ol>
    </nav>

    <section class="hero" aria-labelledby="city-title">
      <div class="hero-media">
        <img src="{img}" srcset="{srcset}" sizes="100vw" alt="{alt}" width="1600" height="1067" fetchpriority="high">
      </div>
      <div class="container">
        <p class="eyebrow">{name}, California</p>
        <h1 id="city-title">{name} real estate agent</h1>
        <p class="lede">{lede}</p>
        <form action="/" method="GET" id="value">
          <input type="hidden" name="src" value="{src}">
          <label class="search-label" for="city-address">What's your {name} home worth?</label>
          <div class="search-bar">
            {search_icon}
            <input id="city-address" name="address" type="text" required autocomplete="street-address" spellcheck="false" placeholder="Enter your home address">
            <button class="btn btn-primary" type="submit">Get My Home Value</button>
          </div>
        </form>
        <p class="hero-call">Questions about {name}? Call or text Jian at <a href="{phone_href}">{phone}</a></p>
      </div>
    </section>

    <section class="section" aria-labelledby="living-title">
      <div class="container two-col">
        <div>
          <p class="eyebrow">Living in {name}</p>
          <h2 id="living-title">About {name}.</h2>
{living}
        </div>
        <div>
          <ul class="facts">
{facts}
          </ul>
          <p class="note">School boundaries change. Always confirm the assigned schools for a specific address with the district.</p>
        </div>
      </div>
    </section>

    <section class="section" aria-labelledby="buying-title">
      <div class="container">
        <p class="eyebrow">Buying in {name}</p>
        <h2 id="buying-title">How I help {name} buyers.</h2>
        <p class="lede">{buying}</p>
        <ul class="steps">
          <li><h3>Numbers first</h3><p>Recent sales and price per square foot on truly comparable homes, before you write an offer.</p></li>
          <li><h3>Quick replies</h3><p>Questions answered fast by call, text, or email, so you don't lose a home while you wait.</p></li>
          <li><h3>First-time buyer guidance</h3><p>From pre-approval to closing, one clear step at a time, with a lender introduction if you need one.</p></li>
        </ul>{deal}
        <div class="actions">
          <a class="btn btn-primary" href="{contact}">Book a free {name} consultation</a>
          <a class="btn btn-outline" href="{phone_href}">Call {phone}</a>
        </div>
      </div>
    </section>

    <section class="section" aria-labelledby="nearby-title">
      <div class="container">
        <p class="eyebrow">Nearby</p>
        <h2 id="nearby-title">Other areas I serve.</h2>
        <ul class="nearby">
{nearby}
        </ul>
        <p style="margin-top:28px"><a class="text-link" href="/#communities">See all communities</a></p>
      </div>
    </section>

    <section class="section cta" aria-labelledby="cta-title">
      <div class="container cta-inner">
        <div>
          <p class="eyebrow">Selling in {name}?</p>
          <h2 id="cta-title">Start with your home's value.</h2>
        </div>
        <div class="cta-actions">
          <a class="btn btn-primary" href="#value">Get My Home Value</a>
          <a class="btn btn-outline" href="{sell}">Talk to Jian about selling</a>
        </div>
      </div>
    </section>""".format(
        name=e(name), img=e(IMG.format(city["photo"], 1600)), srcset=srcset(city["photo"], [800, 1200, 1600, 2000]),
        alt=e(city["alt"]), lede=e(city["lede"]), src=src, search_icon=SEARCH_ICON, phone=e(PHONE),
        phone_href=e(PHONE_HREF), living=living, facts=facts, buying=e(city["buying"]), deal=deal,
        contact=contact_href, sell=sell_href, nearby=nearby)

    ld = jsonld(
        {"@type": "WebPage", "@id": SITE + path + "#webpage", "url": SITE + path, "name": title,
         "description": desc, "isPartOf": {"@id": SITE + "/#website"}, "about": {"@id": SITE + "/#agent"},
         "breadcrumb": {"@id": SITE + path + "#breadcrumb"}},
        dict(breadcrumbs([("Home", "/"), ("Communities", "/#communities"), (name + " real estate agent", path)]),
             **{"@id": SITE + path + "#breadcrumb"}),
        agent_node(area=[place(city)] + [place(BY_SLUG[s]) for s in city["nearby"]]),
    )
    preload = '\n  <link rel="preload" as="image" href="{}" imagesrcset="{}" imagesizes="100vw" fetchpriority="high">'.format(
        e(IMG.format(city["photo"], 1600)), srcset(city["photo"], [800, 1200, 1600, 2000]))
    write(slug + "/index.html", page(title, desc, path, body, photo=city["photo"], photo_alt=city["alt"], ld=ld,
                                     contact_href=contact_href, sell_href=sell_href, current_city=slug, preload=preload))


def simple_section(eyebrow, h1, inner):
    return """    <section class="page-intro">
      <div class="container prose">
        <p class="eyebrow">{}</p>
        <h1>{}</h1>
{}
      </div>
    </section>""".format(e(eyebrow), e(h1), inner)


def build_thank_you():
    inner = """        <p class="lede">Jian will follow up soon. If you asked for a home value, expect a personalized estimate within 24 hours.</p>
        <p>Need to talk sooner? Call or text <a href="{href}">{phone}</a>.</p>
        <div class="actions">
          <a class="btn btn-primary" href="/">Back to home</a>
          <a class="btn btn-outline" href="{href}">Call {phone}</a>
        </div>""".format(href=e(PHONE_HREF), phone=e(PHONE))
    write("thank-you.html", page("Thank You | Jian-Xing Wu, REALTOR®", "Your message to Jian-Xing Wu has been received.",
                                 "/thank-you.html", simple_section("Thank you", "Your message is on its way.", inner), index=False))


def build_404():
    links = "\n".join('          <li><a href="/{}/">{} real estate</a></li>'.format(c["slug"], e(c["name"])) for c in SERVICE_CITIES)
    inner = """        <p class="lede">The page you're looking for doesn't exist or has moved.</p>
        <div class="actions">
          <a class="btn btn-primary" href="/">Go to the home page</a>
          <a class="btn btn-outline" href="{href}">Call {phone}</a>
        </div>
        <h2>Communities</h2>
        <ul>
{links}
        </ul>""".format(href=e(PHONE_HREF), phone=e(PHONE), links=links)
    write("404.html", page("Page Not Found | Jian-Xing Wu, REALTOR®", "This page could not be found.", "/404.html",
                           simple_section("404", "Page not found.", inner), index=False))


def build_privacy():
    contact = e(CONFIG.get("privacyContact") or EMAIL or PHONE)
    if "@" in contact:
        contact_html = '<a href="mailto:{0}">{0}</a>'.format(contact)
    else:
        contact_html = 'call or text <a href="{}">{}</a>'.format(e(PHONE_HREF), e(PHONE))
    inner = """        <p class="lede">How this website collects and uses information. Effective November 2, 2026.</p>

        <h2>Information you give us</h2>
        <p>When you submit the contact form or request a home value estimate, we collect what you enter. This can include your name, phone number, email address, property address, what you're looking for, and any message.</p>
        <p>Each submission also records the page you were on, the time, and any campaign tags in the link you followed (such as utm_source).</p>

        <h2>How it's used</h2>
        <ul>
          <li>To respond to your request and provide the home value estimate or market analysis you asked for.</li>
          <li>To contact you by phone call, text message, or email, as you agreed on the form.</li>
        </ul>
        <p>We do not sell your personal information. Mobile numbers and text-message consent are not shared with third parties for their marketing.</p>

        <h2>Text messages</h2>
        <p>Consent to receive calls or texts is not a condition of any purchase. Message and data rates may apply. Reply STOP to opt out of texts at any time, or HELP for help.</p>

        <h2>Service providers</h2>
        <ul>
          <li><strong>Netlify</strong> hosts this website and stores form submissions.</li>
          <li><strong>RentCast</strong> receives the property address you enter to return an automated value estimate.</li>
          <li><strong>Google</strong> serves the website's fonts and, when enabled, address suggestions as you type.</li>
          <li><strong>Unsplash</strong> serves some of the photos on this site.</li>
        </ul>

        <h2>Cookies and tracking</h2>
        <p>This site does not use advertising or analytics cookies. It keeps campaign tags from your link in your browser's session storage so they can be attached to a form you submit; this is cleared when you close the tab.</p>

        <h2>Your choices</h2>
        <p>To ask what information we have about you, or to correct or delete it, {contact}.</p>

        <p class="note">Jian-Xing Wu, REALTOR®, DRE #{agent} · {brokerage} ({legal}), DRE #{broker}</p>""".format(
        contact=contact_html, agent=LIC["agent"], broker=LIC["broker"],
        brokerage=e(LIC["brokerage"]), legal=e(LIC["brokerageLegalName"]))
    title = "Privacy Policy | Jian-Xing Wu, REALTOR®"
    desc = "How the Jian-Xing Wu, REALTOR® website collects, uses, and protects the information you submit."
    ld = jsonld({"@type": "WebPage", "@id": SITE + "/privacy/#webpage", "url": SITE + "/privacy/", "name": title,
                 "isPartOf": {"@id": SITE + "/#website"}})
    write("privacy/index.html", page(title, desc, "/privacy/", simple_section("Privacy", "Privacy policy.", inner), ld=ld))


# --------------------------------------------------------------------------------------------
# Crawling files
# --------------------------------------------------------------------------------------------
def build_crawl_files():
    urls = ["/"] + ["/{}/".format(c["slug"]) for c in SERVICE_CITIES] + ["/privacy/"]
    body = "\n".join("  <url><loc>{}</loc></url>".format(e(SITE + u)) for u in urls)
    write("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n'
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{}\n</urlset>\n'.format(body))
    if INDEXABLE:
        robots = "User-agent: *\nAllow: /\nDisallow: /.netlify/\n\nSitemap: {}/sitemap.xml\n".format(SITE)
    else:
        robots = "# Non-production deploy ({}): keep out of search results.\nUser-agent: *\nDisallow: /\n".format(CONTEXT)
        write("_headers", "/*\n  X-Robots-Tag: noindex, nofollow\n")
    write("robots.txt", robots)
    write("site.webmanifest", json.dumps({
        "name": CONFIG["businessName"],
        "short_name": CONFIG["agentName"],
        "start_url": "/",
        "display": "browser",
        "background_color": "#FAFAF8",
        "theme_color": "#2C3E57",
        "icons": [
            {"src": "/images/icon-192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "/images/icon-512.png", "sizes": "512x512", "type": "image/png"},
            {"src": "/images/favicon.svg", "sizes": "any", "type": "image/svg+xml"},
        ],
    }, indent=2, ensure_ascii=False) + "\n")


def write(rel, text):
    out = DIST / rel
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")


def main():
    if DIST.exists():
        shutil.rmtree(DIST)
    shutil.copytree(SRC / "images", DIST / "images", ignore=shutil.ignore_patterns(".*"))
    build_index()
    for city in SERVICE_CITIES:
        city_page(city)
    build_privacy()
    build_thank_you()
    build_404()
    build_crawl_files()
    pages = sorted(str(p.relative_to(DIST)) for p in DIST.rglob("*.html"))
    print("Built {} pages for {} (context: {}, indexable: {})".format(len(pages), SITE, CONTEXT, INDEXABLE))
    if SITE == FALLBACK_URL and not os.environ.get("NETLIFY"):
        print("note: using fallback URL; set SITE_URL or siteUrl in site.config.json for the production domain")


if __name__ == "__main__":
    main()
