#!/usr/bin/env python3
"""Generate the city landing pages (/diamond-bar/, /walnut/, ...) and sitemap.xml.

Edit CITIES below, then run from the repo root:

    python3 scripts/build-city-pages.py

Pages are plain static HTML. They are real pages (no redirects): each one links into the main
site's home value tool and contact form, passing the address or area in the URL.
"""
from html import escape
from pathlib import Path
from urllib.parse import quote
import json

ROOT = Path(__file__).resolve().parent.parent
SITE_URL = "[SITE URL]"  # same placeholder as index.html; replace everywhere when the domain is live

IMG = "https://images.unsplash.com/photo-{}?w=1600&q=80"

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
.btn{display:inline-flex;align-items:center;justify-content:center;min-height:52px;padding:14px 28px;font:inherit;font-size:.9375rem;font-weight:600;line-height:1.2;border:1px solid transparent;border-radius:var(--radius);cursor:pointer;text-decoration:none;text-align:center;transition:background-color .2s,color .2s}
.btn-primary{background:var(--accent);color:#fff}
.btn-primary:hover{background:var(--accent-hover)}
.btn-outline{border-color:var(--ink);color:var(--ink)}
.btn-outline:hover{background:var(--ink);color:#fff}
.text-link{font-weight:500;text-decoration:underline;text-underline-offset:5px;text-decoration-thickness:1px}
.site-header{position:sticky;top:0;z-index:50;background:rgba(250,250,248,.97);border-bottom:1px solid var(--line)}
.header-inner{display:flex;align-items:center;justify-content:space-between;gap:12px 24px;flex-wrap:wrap;min-height:68px;padding:10px var(--gutter)}
.wordmark{font-size:.875rem;font-weight:600;letter-spacing:.26em;text-decoration:none;white-space:nowrap}
.nav ul{display:flex;flex-wrap:wrap;gap:4px 28px;list-style:none}
.nav a{display:inline-block;padding:6px 0;font-size:.78rem;font-weight:500;letter-spacing:.14em;text-transform:uppercase;text-decoration:none;border-bottom:1px solid transparent}
.nav a:hover{border-bottom-color:var(--ink)}
.crumbs{padding:18px 0;font-size:.8125rem;color:var(--muted)}
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
.search-label{display:block;margin-bottom:10px;font-size:.75rem;font-weight:600;letter-spacing:.16em;text-transform:uppercase;color:rgba(255,255,255,.9)}
.search-bar{display:flex;align-items:center;gap:12px;max-width:740px;padding:6px 6px 6px 20px;background:#fff;color:var(--ink);border-radius:4px;box-shadow:0 1px 3px rgba(0,0,0,.1),0 10px 30px rgba(0,0,0,.14)}
.search-bar:focus-within{outline:2px solid #fff;outline-offset:3px}
.search-bar svg{flex:none;color:#5F6368}
.search-bar input{flex:1;min-width:0;padding:14px 0;font:inherit;font-size:1.125rem;color:var(--ink);background:transparent;border:0;outline:none}
.search-bar input::placeholder{color:#6B6B66}
.search-bar .btn{flex:none}
@media (max-width:600px){.search-bar{flex-wrap:wrap;padding:6px;gap:0}.search-bar svg{margin:0 10px 0 12px}.search-bar input{padding:14px 8px 14px 0}.search-bar .btn{width:100%;margin-top:4px}}
.section{padding:clamp(64px,9vw,112px) 0;border-top:1px solid var(--line)}
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
.areas{display:flex;flex-wrap:wrap;gap:6px 18px;list-style:none;margin:6px 0 20px}
.areas a{text-decoration:none;color:var(--ink)}
.areas a:hover{text-decoration:underline}
@media (max-width:480px){:root{--gutter:16px}}
""".strip()

SEARCH_ICON = '<svg width="20" height="20" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path fill="currentColor" d="M15.5 14h-.79l-.28-.27A6.47 6.47 0 0 0 16 9.5 6.5 6.5 0 1 0 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/></svg>'

e = escape


def areas_list(current=None):
    items = []
    for c in CITIES:
        if c["slug"] == current:
            items.append(f'<li><span aria-current="page">{e(c["name"])}</span></li>')
        else:
            items.append(f'<li><a href="/{c["slug"]}/">{e(c["name"])}</a></li>')
    return "\n          ".join(items)


def json_ld(city):
    url = f"{SITE_URL}/{city['slug']}/"
    agent = {
        "@context": "https://schema.org",
        "@type": "RealEstateAgent",
        "name": "Jian-Xing Wu",
        "url": f"{SITE_URL}/",
        "image": f"{SITE_URL}/images/jian-xing-wu.jpg",
        "telephone": "[PHONE]",
        "email": "[EMAIL]",
        "address": {"@type": "PostalAddress", "streetAddress": "[OFFICE ADDRESS]", "addressRegion": "CA", "addressCountry": "US"},
        "identifier": "California DRE #02236314",
        "parentOrganization": {
            "@type": "RealEstateAgent",
            "name": "Pinnacle Real Estate Group",
            "legalName": "Navigators Real Estate, Inc.",
            "identifier": "California DRE #01918023",
        },
        "areaServed": {"@type": "City", "name": f"{city['name']}, CA"},
    }
    crumbs = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{SITE_URL}/"},
            {"@type": "ListItem", "position": 2, "name": "Communities", "item": f"{SITE_URL}/#communities"},
            {"@type": "ListItem", "position": 3, "name": f"{city['name']} real estate", "item": url},
        ],
    }
    return "\n".join(
        f'  <script type="application/ld+json">\n{json.dumps(obj, indent=2, ensure_ascii=False)}\n  </script>'
        for obj in (agent, crumbs)
    )


def page(city):
    name = city["name"]
    slug = city["slug"]
    src = f"city-{slug}"
    url = f"{SITE_URL}/{slug}/"
    photo = IMG.format(city["photo"])
    title = f"{name} Real Estate & Homes for Sale | Jian-Xing Wu, REALTOR®"
    desc = (f"Buying or selling a home in {name}, CA? Jian-Xing Wu, REALTOR® with Pinnacle Real Estate Group, "
            f"helps first-time buyers and families. Get a free {name} home value estimate. DRE #02236314.")
    contact_href = f"/?area={quote(name)}&amp;src={src}#contact"
    sell_href = f"/?intent=Sell&amp;area={quote(name)}&amp;src={src}#contact"

    facts = "\n".join(
        f'            <li><span class="k">{e(k)}</span><span>{e(v)}</span></li>' for k, v in city["facts"]
    )
    living = "\n".join(f"          <p>{e(p)}</p>" for p in city["living"])
    nearby = "\n".join(
        f'          <li><a href="/{s}/">{e(BY_SLUG[s]["name"])}<span>Area guide →</span></a></li>'
        for s in city["nearby"]
    )
    deal = ""
    if city.get("deal"):
        kind, price = city["deal"]
        deal = f"""
        <article class="deal">
          <p class="eyebrow">Recently closed · Buyer side</p>
          <h3>{e(name)}</h3>
          <p class="deal-price">{e(price)}</p>
          <p>{e(kind)} · Represented the buyer</p>
        </article>"""

    return f"""<!doctype html>
<!-- Generated by scripts/build-city-pages.py. Edit the script, not this file. -->
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{e(title)}</title>
  <meta name="description" content="{e(desc)}">
  <link rel="canonical" href="{url}">
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="Jian-Xing Wu, REALTOR®">
  <meta property="og:title" content="{e(title)}">
  <meta property="og:description" content="{e(desc)}">
  <meta property="og:url" content="{url}">
  <meta property="og:image" content="{photo}">
  <meta property="og:image:alt" content="{e(city['alt'])}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="theme-color" content="#FAFAF8">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link rel="preconnect" href="https://images.unsplash.com">
  <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
{json_ld(city)}
  <style>
{CSS}
  </style>
</head>
<body>
  <a class="skip-link" href="#main">Skip to content</a>

  <header class="site-header">
    <div class="header-inner" style="max-width:1200px;margin:0 auto">
      <a class="wordmark" href="/" aria-label="Jian-Xing Wu, home">JIAN-XING WU</a>
      <nav class="nav" aria-label="Primary">
        <ul>
          <li><a href="/#buy">Buy</a></li>
          <li><a href="{sell_href}">Sell</a></li>
          <li><a href="/#value">Home Value</a></li>
          <li><a href="/#communities">Communities</a></li>
          <li><a href="/#about">About</a></li>
          <li><a href="{contact_href}">Contact</a></li>
        </ul>
      </nav>
    </div>
  </header>

  <main id="main">
    <nav class="crumbs container" aria-label="Breadcrumb">
      <ol>
        <li><a href="/">Home</a></li>
        <li><a href="/#communities">Communities</a></li>
        <li><span aria-current="page">{e(name)}</span></li>
      </ol>
    </nav>

    <section class="hero" aria-labelledby="city-title">
      <div class="hero-media">
        <img src="{photo}" alt="{e(city['alt'])}" width="1600" height="1067" fetchpriority="high">
      </div>
      <div class="container">
        <p class="eyebrow">{e(name)}, California</p>
        <h1 id="city-title">{e(name)} real estate</h1>
        <p class="lede">{e(city['lede'])}</p>
        <form action="/" method="GET" id="value">
          <input type="hidden" name="src" value="{src}">
          <label class="search-label" for="city-address">What's your {e(name)} home worth?</label>
          <div class="search-bar">
            {SEARCH_ICON}
            <input id="city-address" name="address" type="text" required autocomplete="street-address" spellcheck="false" placeholder="Enter your home address">
            <button class="btn btn-primary" type="submit">Get My Home Value</button>
          </div>
        </form>
      </div>
    </section>

    <section class="section" aria-labelledby="living-title">
      <div class="container two-col">
        <div>
          <p class="eyebrow">Living in {e(name)}</p>
          <h2 id="living-title">About {e(name)}.</h2>
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
        <p class="eyebrow">Buying in {e(name)}</p>
        <h2 id="buying-title">How I help {e(name)} buyers.</h2>
        <p class="lede">{e(city['buying'])}</p>
        <ul class="steps">
          <li><h3>Numbers first</h3><p>Recent sales and price per square foot on truly comparable homes, before you write an offer.</p></li>
          <li><h3>Quick replies</h3><p>Questions answered fast by call, text, or email, so you don't lose a home while you wait.</p></li>
          <li><h3>First-time buyer guidance</h3><p>From pre-approval to closing, one clear step at a time, with a lender introduction if you need one.</p></li>
        </ul>{deal}
        <p style="margin-top:36px"><a class="btn btn-primary" href="{contact_href}">Tell me what you're looking for in {e(name)}</a></p>
      </div>
    </section>

    <section class="section" aria-labelledby="nearby-title">
      <div class="container">
        <p class="eyebrow">Nearby</p>
        <h2 id="nearby-title">Other areas I serve.</h2>
        <ul class="nearby">
{nearby}
        </ul>
      </div>
    </section>

    <section class="section cta" aria-labelledby="cta-title">
      <div class="container cta-inner">
        <div>
          <p class="eyebrow">Selling in {e(name)}?</p>
          <h2 id="cta-title">Start with your home's value.</h2>
        </div>
        <div class="cta-actions">
          <a class="btn btn-primary" href="#value">Get My Home Value</a>
          <a class="btn btn-outline" href="{sell_href}">Talk to Jian</a>
        </div>
      </div>
    </section>
  </main>

  <footer class="site-footer">
    <div class="container">
      <div class="footer-top">
        <div>
          <p class="wordmark">JIAN-XING WU</p>
          <p>REALTOR® | DRE #02236314</p>
          <p>Pinnacle Real Estate Group | Navigators Real Estate, Inc. | DRE #01918023</p>
        </div>
        <div>
          <p>[OFFICE ADDRESS]</p>
          <p><a href="tel:[PHONE]">[PHONE]</a> · <a href="mailto:[EMAIL]">[EMAIL]</a></p>
        </div>
      </div>
      <p class="eyebrow" style="margin-bottom:4px">Areas</p>
      <ul class="areas">
          {areas_list(slug)}
      </ul>
      <p>Equal Housing Opportunity. Jian-Xing Wu and Pinnacle Real Estate Group are committed to the federal Fair Housing Act and California fair housing laws.</p>
      <p>Photos are for illustration and do not show specific {e(name)} properties.</p>
      <p>© 2026 Jian-Xing Wu. All rights reserved. · <a href="#">Privacy policy</a></p>
    </div>
  </footer>
</body>
</html>
"""


def sitemap():
    urls = [f"{SITE_URL}/"] + [f"{SITE_URL}/{c['slug']}/" for c in CITIES]
    body = "\n".join(f"  <url><loc>{u}</loc></url>" for u in urls)
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{body}\n</urlset>\n'


def main():
    for city in CITIES:
        out = ROOT / city["slug"] / "index.html"
        out.parent.mkdir(exist_ok=True)
        out.write_text(page(city), encoding="utf-8")
        print("wrote", out.relative_to(ROOT))
    (ROOT / "sitemap.xml").write_text(sitemap(), encoding="utf-8")
    print("wrote sitemap.xml")


if __name__ == "__main__":
    main()
