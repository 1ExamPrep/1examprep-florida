#!/usr/bin/env python3
"""Build passyourfloridacontractorexam.com (design: Exam Path) into the repo root.

Input: data/products-raw.json (every active 1 Exam Prep product with Florida in the title), tools/flclass.py,
tools/flcopy.py, assets/. Output: static HTML with JSON-LD, assets/finder.json for the exam path picker,
sitemap, robots, llms.txt, agents.md and a 404 page.
"""
import html, json, os, re, shutil, sys
from collections import defaultdict
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "tools"))
from flclass import classify, ptype, clean_sentences, also
import schemakit
from flcopy import *

ICONS = json.load(open(os.path.join(os.path.dirname(__file__), "tools", "icons.json")))
CFG = json.load(open("site-config.json"))
SITE = CFG["siteUrl"].rstrip("/")
BRAND = CFG["brand"]
PHONE, PHONE_TEL, EMAIL = CFG["phone"], CFG["phoneTel"], CFG["email"]
FORM_ID = CFG["contactFormId"]
OUT = "."
STATE_NAME = "Florida"
BLOG_URLS = []
STOP = {"the", "and", "for", "of", "on", "with", "to", "a", "an", "in", "by", "from", "based", "includes", "florida"}
e = lambda s: html.escape(str(s), quote=True)


def icon(c, cls="ic"):
    key = CLASSES.get(c, {}).get("icon", c)
    return (f'<svg class="{cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICONS.get(key, ICONS["code-books-and-courses"])}</svg>')


def money(x):
    x = float(x)
    if x == 0:
        return "Free"
    return f"${x:,.0f}" if x == int(x) else f"${x:,.2f}"


def slugify(s, maxlen=70):
    s = s.lower().replace("&", " ").replace("’", "").replace("'", "")
    s = s.translate(str.maketrans("áéíóúñ", "aeioun"))
    words = [w for w in re.split(r"[^a-z0-9]+", s) if w and w not in STOP]
    out = ""
    for w in words:
        if len(out) + len(w) + 1 > maxlen:
            break
        out = f"{out}-{w}" if out else w
    return out


def words(text):
    return len(re.findall(r"[A-Za-z0-9$%][\w$%,.'’-]*", text))


# ---------------------------------------------------------------- products
raw = json.load(open("data/products-raw.json"))
products, by_class, listed, used = [], defaultdict(list), defaultdict(list), set()
for p in raw:
    if p["status"] != "ACTIVE":
        continue
    c = classify(p["title"])
    tkey, tlabel, torder = ptype(p["title"])
    slug = slugify(re.sub(r"\bFlorida\b", "", p["title"]))
    base, n = slug, 2
    while (c, slug) in used:
        slug, n = f"{base}-{n}", n + 1
    used.add((c, slug))
    v = p["variants"]["nodes"][0]
    img = ((p.get("featuredMedia") or {}).get("preview") or {}).get("image") or {}
    lo = float(p["priceRangeV2"]["minVariantPrice"]["amount"])
    hi = float(p["priceRangeV2"]["maxVariantPrice"]["amount"])
    cmp = ((p.get("compareAtPriceRange") or {}).get("maxVariantCompareAtPrice") or {})
    item = dict(
        title=re.sub(r"\s+", " ", p["title"]).strip(), handle=p["handle"], cls=c, slug=slug, tkey=tkey, tlabel=tlabel, torder=torder,
        lo=lo, hi=hi, compare=float(cmp.get("amount") or 0), variant=v["legacyResourceId"], sku=v.get("sku") or v["legacyResourceId"],
        img=img.get("url"), alt=(img.get("altText") or p["title"]).strip(), desc=p.get("description") or "", ptype_raw=p.get("productType") or "",
        spanish=bool(re.search(r"spanish|español|curso de|examen de", p["title"], re.I)),
    )
    item["url"] = f"/{c}/{slug}/"
    item["cart"] = f"https://1examprep.com/cart/{item['variant']}:1"
    products.append(item)
    by_class[c].append(item)
    for extra in also(p["title"], c):
        listed[extra].append(item)
for c in by_class:
    by_class[c].sort(key=lambda x: (x["torder"], -x["lo"], x["title"]))
for c in CLASSES:
    listed[c] = sorted(by_class.get(c, []) + listed.get(c, []), key=lambda x: (x["torder"], -x["lo"], x["title"]))

left = [x["title"] for x in by_class.get("code-books-and-references", []) if not re.search(r"building code|chapter|statutes|energy efficient", x["title"], re.I)]
if left:
    print("Check these (landed in code books):", *left, sep="\n  ")


def paid(ps):
    return [p for p in ps if p["lo"] > 0] or ps


def low(c):
    return min(p["lo"] for p in paid(listed[c]))


def cls_url(c):
    return f"/{c}/"


def cls_name(c):
    return CLASSES[c]["name"]


def short_name(c):
    return re.sub(r"\s*\(.*?\)", "", cls_name(c))


GROUP_CLASSES = {g: [c for c in CLASSES if CLASSES[c]["group"] == g and listed.get(c)] for g, *_ in GROUPS}
live_classes = [c for g in GROUP_CLASSES for c in GROUP_CLASSES[g]]
GNAME = {g: n for g, n, _ in GROUPS}

# ---------------------------------------------------------------- exam path (what to buy for each license)


ADDON_SKIP = re.compile(r"contractors manual|tabs only|pre-printed tabs|flash card", re.I)


def pick(c, choice, as_addon=False):
    """Best product on license c for an exam path choice, or None. Add-ons skip single manuals, tabs and flash cards."""
    want = dict((k, t) for k, _, t in PATH_CHOICES)[choice]
    ps = [p for p in listed[c] if p["tkey"] in want and not p["spanish"] and not ((as_addon or c == "business-and-finance") and ADDON_SKIP.search(p["title"]))]
    if not ps:
        return None
    year = lambda p: max([int(y) for y in re.findall(r"\b(20[12]\d)\b", p["title"])] or [0])
    ps.sort(key=lambda p: (0 < year(p) < 2023, want.index(p["tkey"]), -year(p), -p["lo"] if choice == "everything" else p["lo"]))
    return ps[0]


def partner_for(c):
    g = CLASSES[c]["group"]
    part = PATH[g]["partner"]
    if not part or part == c or not listed.get(part):
        return None
    return part


def addon(c, choice):
    """The second-exam product to pair with a pick, matched to the same kind of package where possible."""
    part = partner_for(c)
    if not part or choice in ("everything", "free"):
        return None
    if part == "electrical-business" and choice == "books":
        m = [p for p in listed["business-and-finance"] if re.search(r"contractors manual, 2025 edition; highlighted and tabbed \[electrical", p["title"], re.I)]
        if m:
            return m[0]
    for ch in (choice, "books", "course"):
        x = pick(part, ch, as_addon=True)
        if x:
            return x
    return None


def exam_list(c):
    g = CLASSES[c]["group"]
    if c == "nascla-commercial-general-building":
        return ["NASCLA Commercial General Building", "Business and Finance", "Florida Building Code portion"]
    if g == "div2":
        return [f"{short_name(c)} trade knowledge", "Business and Finance"]
    if g == "inspectors" and c != "principles-and-practice":
        return [f"{short_name(c)} ICC exam", "Florida Principles and Practice"]
    if c in ("journeyman-electrician", "journeyman-and-master-plumber"):
        return ["County journeyman or master exam"]
    if c in ("business-and-finance", "electrical-business", "principles-and-practice"):
        return [short_name(c)]
    return PATH[g]["exams"]


# ---------------------------------------------------------------- shared chrome
FONTS = "https://fonts.googleapis.com/css2?family=Montserrat:ital,wght@0,500;0,600;0,700;0,800;1,800&family=Poppins:ital,wght@0,400;0,500;0,600;1,400&display=swap"


def head(title, desc, path, ld, og_img="/assets/logo.png", extra=""):
    canon = SITE + path
    og = og_img if og_img.startswith("http") else SITE + og_img
    blocks = "\n".join(f'<script type="application/ld+json">{json.dumps(b, ensure_ascii=False)}</script>' for b in ld)
    return f"""<!doctype html>
<html lang="en-US">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{canon}">
<meta name="robots" content="index, follow, max-image-preview:large">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{e(BRAND)}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{canon}">
<meta property="og:image" content="{og}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{e(title)}">
<meta name="twitter:description" content="{e(desc)}">
<meta name="twitter:image" content="{og}">
<meta name="theme-color" content="#14284B">
<link rel="icon" href="/assets/favicon.ico" sizes="any">
<link rel="icon" href="/assets/favicon-48.png" type="image/png" sizes="48x48">
<link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTS}">
<link rel="stylesheet" href="/assets/site.css">\n{'<link rel="preload" as="image" type="image/webp" href="/assets/img/hero-1200.webp" media="(min-width: 981px)">' if path == "/" else ""}
{extra}<script src="/assets/site.js" defer></script>
{blocks}
</head>
<body>
"""


LOGO = '<img class="logo" src="/assets/logo-on-light.png" width="240" height="56" alt="Pass Your Florida Contractor Exam">'


def header():
    return f"""<a class="skip" href="#main">Skip to content</a>
<header class="top" data-shrink>
  <div class="wrap top-in">
    <a class="brand" href="/">{LOGO}</a>
    <nav class="nav" aria-label="Main">
      <a href="/#exam-path">Exam path</a>
      <a href="/#find-your-license">Licenses</a>
      <a href="/how-to-get-licensed/">How to get licensed</a>
      <a href="/business-and-finance/">Business and Finance</a>
      <a href="/blog/">Blog</a>
      <a href="/faq/">FAQ</a>
      <a href="/reviews/">Reviews</a>
      <a href="/contact/">Contact</a>
    </nav>
    <a class="call" href="tel:{PHONE_TEL}">{svg("phone")}{PHONE}</a>
  </div>
</header>
"""


def footer():
    cols = []
    for g, gname, _ in GROUPS:
        cs = GROUP_CLASSES[g][:7]
        links = "".join(f'<li><a href="{cls_url(c)}">{e(short_name(c))}</a></li>' for c in cs)
        cols.append(f'<div><p class="f-h">{e(gname.split(":")[0])}</p><ul>{links}</ul></div>')
    return f"""<footer class="foot">
  <div class="wrap">
    <div class="f-grid">
      <div class="f-brand">
        <a class="brand" href="/"><img class="logo" src="/assets/logo-nav.png" width="240" height="56" alt="Pass Your Florida Contractor Exam"></a>
        <p>{e(CFG['tagline'])}</p>
        <p>Orders ship from 1 Exam Prep. Call <a href="tel:{PHONE_TEL}">{PHONE}</a>, email <a href="mailto:{EMAIL}">{EMAIL}</a> or use the <a href="/contact/">contact form</a>. Read <a href="/reviews/">customer reviews</a> or the <a href="/blog/">blog</a> for answers to common exam questions.</p>
      </div>
      {''.join(cols)}
    </div>
    <p class="f-small">Independent exam prep. Not affiliated with the Florida DBPR, the CILB, the ECLB, Professional Testing, Inc. or Pearson VUE. Prices and packages last synced from Shopify on {UPDATED_TEXT}.</p>
  </div>
</footer>
</body>
</html>
"""


ORG = {"@type": "Organization", "@id": SITE + "/#org", "name": BRAND, "url": SITE + "/",
       "logo": {"@type": "ImageObject", "url": SITE + "/assets/icon-512.png", "width": 512, "height": 512}, "image": SITE + "/assets/logo.png",
       "telephone": PHONE_TEL, "email": EMAIL, "areaServed": {"@type": "State", "name": "Florida"},
       "parentOrganization": {"@type": "Organization", "name": "1 Exam Prep", "url": "https://1examprep.com/"},
       "contactPoint": {"@type": "ContactPoint", "contactType": "customer service", "telephone": PHONE_TEL, "email": EMAIL, "areaServed": "US-FL", "availableLanguage": ["English", "Spanish"]},
       "sameAs": [v for v in CFG.get("social", {}).values() if v]}
PUB = {"@type": "Organization", "@id": SITE + "/#org", "name": BRAND, "url": SITE + "/"}


def crumbs(items):
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": n, "item": SITE + u} for i, (n, u) in enumerate(items)]}


def crumb_html(items):
    parts = [f'<a href="{u}">{e(n)}</a>' for n, u in items[:-1]] + [f'<span aria-current="page">{e(items[-1][0])}</span>']
    return '<nav class="crumbs" aria-label="Breadcrumb">' + ' <span aria-hidden="true">/</span> '.join(parts) + "</nav>"


def faq_ld(qas):
    return {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": re.sub("<[^>]+>", "", a)}} for q, a in qas]}


def faq_html(qas, hid="frequently-asked-questions", title="Frequently asked questions"):
    items = "".join(f'<details class="qa reveal"><summary><h3 id="q-{slugify(q, 50)}">{e(q)}</h3></summary><p>{a}</p></details>' for q, a in qas)
    return f'<section class="sec"><h2 id="{hid}">{title}</h2><div class="faq">{items}</div></section>'


def sources_html(links):
    li = "".join(f'<li><a href="{u}" rel="noopener" target="_blank">{e(n)}</a></li>' for n, u in links)
    return (f'<aside class="sources"><p class="s-h">Sources</p><ul>{li}</ul>'
            f'<p class="updated">Last updated <time datetime="{UPDATED}">{UPDATED_TEXT}</time></p></aside>')


def takeaways(items):
    """Key takeaways box, same markup as the other Pass Your sites."""
    items = [i for i in items if i]
    if not items:
        return ""
    li = "".join(f"<li>{e(i)}</li>" for i in items)
    return (f'<aside class="takeaways" aria-labelledby="key-takeaways"><h2 id="key-takeaways">Key takeaways</h2><ul>{li}</ul>'
            f'<p class="upd">Updated <time datetime="{UPDATED}">{UPDATED_TEXT}</time> · prices checked against the 1 Exam Prep store</p></aside>')


def fl(name):
    return name if name.startswith("Florida") else "Florida " + name


def exam_sentence(c):
    x = exam_list(c)
    if not x:
        return ""
    return x[0] if len(x) == 1 else ", ".join(x[:-1]) + " and " + x[-1]


SRC_CORE = [("Florida DBPR Construction Industry Licensing Board", DBPR_CILB), ("DBPR construction examinations", DBPR_EXAMS)]


def group_sources(c):
    g = CLASSES[c]["group"]
    if g == "electrical":
        return [("DBPR electrical examinations", DBPR_ELEC), SRC_CORE[0]]
    if g == "inspectors":
        return [("ICC bulletin for Florida DBPR candidates", ICC_FL), SRC_CORE[0]]
    if c == "nascla-commercial-general-building":
        return [("NASCLA participating agencies", NASCLA_FL)] + SRC_CORE
    if g == "county":
        return [SRC_CORE[0], ("DBPR construction industry FAQ", DBPR_FAQ)]
    return SRC_CORE + [("Business and Finance exemption, rule 61G4-16.0015", FAC_BF)]


def write(path, content):
    fp = os.path.join(OUT, path.strip("/"), "index.html") if not path.endswith((".txt", ".xml", ".md", ".html", ".json")) else os.path.join(OUT, path.strip("/"))
    os.makedirs(os.path.dirname(fp) or ".", exist_ok=True)
    open(fp, "w").write(content)


def price_span(p):
    if p["hi"] > p["lo"]:
        return f"{money(p['lo'])} to {money(p['hi'])}"
    return money(p["lo"])


def img_tag(p, w, eager=False):
    if p["img"]:
        sep = "&" if "?" in p["img"] else "?"
        load = 'fetchpriority="high"' if eager else 'loading="lazy" decoding="async"'
        return f'<img src="{e(p["img"])}{sep}width={w}" alt="{e(p["alt"])}" width="{w}" height="{w}" {load}>'
    return f'<div class="noimg" role="img" aria-label="{e(p["title"])}"><img src="/assets/icon-192.png" alt="Florida exam path icon" width="96" height="96"></div>'


def card(p, sub=None):
    cmpx = f'<s>{money(p["compare"])}</s> ' if p["compare"] > p["hi"] else ""
    pr = "Free demo" if p["lo"] == 0 else f"From {money(p['lo'])}"
    return (f'<article class="pcard reveal" data-type="{p["tkey"]}"><a href="{p["url"]}">{img_tag(p, 480)}'
            f'<span class="ptag">{e(sub or p["tlabel"])}</span><h3 id="p-{p["cls"][:20]}-{p["slug"][:50]}">{e(p["title"])}</h3><p class="price">{cmpx}<b>{pr}</b></p></a></article>')


# ---------------------------------------------------------------- sidebar rail
def rail_call():
    return (f'<div class="r-card r-call"><p class="r-h">Need help choosing?</p><p>Tell the 1 Exam Prep team your license and test date, '
            f'and they will match you with the right books.</p><a class="r-phone" href="tel:{PHONE_TEL}">{PHONE}</a>'
            f'<p class="r-small">{EMAIL}</p><a href="/contact/">Send us a message</a></div>')


def rail_class(c, first_hid):
    ps = listed[c]
    rows = [("Packages", str(len(ps))), ("From", money(low(c))), ("Board", PATH[CLASSES[c]["group"]]["short"]), ("Format", "Open book"), ("To pass", "70% per part" if CLASSES[c]["group"] in ("div1", "div2") else "See your bulletin")]
    dl = "".join(f"<div><dt>{a}</dt><dd>{b}</dd></div>" for a, b in rows)
    part = partner_for(c)
    also_card = (f'<div class="r-card"><p class="r-h">Also required</p><p>{e(short_name(part))} is the other exam on this path, and most candidates order both together.</p>'
                 f'<a href="{cls_url(part)}">{e(short_name(part))} prep</a></div>') if part else ""
    return (f'<aside class="rail" aria-label="{e(cls_name(c))} quick facts"><div class="rail-in">'
            f'<div class="r-card r-facts"><div class="r-ic">{icon(c)}</div><p class="r-h">{e(short_name(c))} at a glance</p><dl>{dl}</dl>'
            f'<a class="btn r-btn" href="#{first_hid}">See your exam path</a></div>{also_card}{rail_call()}</div></aside>')


def rail_product(p, price):
    c = p["cls"]
    return (f'<aside class="rail" aria-label="Buy {e(p["title"])}"><div class="rail-in">'
            f'<div class="r-card r-buy"><p class="r-h">{e(p["tlabel"])}</p><p class="r-price">{price}</p>'
            f'<a class="btn r-btn" href="{p["cart"]}" rel="nofollow">{"Get the free demo" if p["lo"] == 0 else "Buy now"}</a><p class="r-small">Secure checkout at 1 Exam Prep</p></div>'
            f'<div class="r-card"><div class="r-ic">{icon(c)}</div><p class="r-h">{e(short_name(c))}</p>'
            f'<p>Compare all {len(listed[c])} packages for this license.</p><a href="{cls_url(c)}">See every package</a></div>'
            f'{rail_call()}</div></aside>')


def rail_popular(label):
    li = "".join(f'<li><a href="{cls_url(c)}"><span class="r-li-ic">{icon(c)}</span>{e(short_name(c))}</a></li>' for c in POPULAR if listed.get(c))
    return (f'<aside class="rail" aria-label="{e(label)}"><div class="rail-in">'
            f'<div class="r-card"><p class="r-h">Popular licenses</p><ul class="r-list">{li}</ul>'
            f'<a class="btn r-btn" href="/#exam-path">Start your exam path</a></div>'
            f'{rail_call()}</div></aside>')


# ---------------------------------------------------------------- exam path box on license pages
def path_box(c):
    """Three ready-made bundles for this license: good, better, best, each with the second exam added."""
    tiers = []
    for choice, label in (("books", "Books only"), ("books-course", "Books plus a course"), ("everything", "Everything done for me")):
        p = pick(c, choice)
        if not p or any(p is t[1] for t in tiers):
            continue
        a = addon(c, choice)
        tiers.append((label, p, a))
    if not tiers:
        return ""
    cells = []
    for i, (label, p, a) in enumerate(tiers):
        total = p["lo"] + (a["lo"] if a else 0)
        cart = p["cart"] + (f",{a['variant']}:1" if a else "")
        best = i == len(tiers) - 1 and len(tiers) > 1 and p["tkey"] in ("one-package", "ultimate")
        mid = len(tiers) == 3 and i == 1
        badge = '<span class="t-badge">Most popular</span>' if mid else ('<span class="t-badge alt">Best value</span>' if best else "")
        add = (f'<li>Plus <a href="{a["url"]}">{e(a["title"])}</a> ({money(a["lo"])})</li>') if a else ""
        inc = "" if a else ('<li>Business and Finance prep included</li>' if p["tkey"] == "one-package" else "")
        cells.append(f'<div class="tier{" on" if mid or len(tiers) == 1 else ""} reveal">{badge}<h3 id="tier-{i + 1}">{e(label)}</h3>'
                     f'<p class="t-price"><b>{money(total)}</b>{" for both exams" if a else ""}</p>'
                     f'<ul class="ticks"><li><a href="{p["url"]}">{e(p["title"])}</a> ({money(p["lo"])})</li>{add}{inc}</ul>'
                     f'<a class="btn" href="{cart}" rel="nofollow">Buy this path</a></div>')
    exams = [("the " + x[0].lower() + x[1:]) if x.startswith("County") else x for x in exam_list(c)]
    steps = " then ".join(exams) if len(exams) < 3 else ", ".join(exams[:-1]) + " and " + exams[-1]
    return (f'<section class="sec"><h2 id="your-exam-path">What is your exam path for {e(short_name(c))}?</h2>'
            f'<p>To earn this license you pass {steps}. ' + ('Each bundle below already pairs the trade prep with the second exam, '
            'so one checkout covers every part. ' if any(t[2] for t in tiers) else 'Each option below is a complete starting point for that exam. ') +
            'Prices come straight from the 1 Exam Prep store.</p>'
            f'<div class="tiers">{"".join(cells)}</div></section>')


# ---------------------------------------------------------------- license pages
def exam_rows(c):
    g = CLASSES[c]["group"]
    rows = [("Licensing board", PATH[g]["board"])]
    if g in ("div1", "div2"):
        rows += [("Register with", "Professional Testing, Inc. (PTI)"), ("Test at", "Pearson VUE, computer based"), ("Format", "Open book, approved references only"),
                 ("Exam parts", ", ".join(exam_list(c))), ("Passing score", "70% on each part"), ("Business and Finance", "120 questions, about 6.5 hours")]
    elif g == "electrical":
        rows += [("Test at", "Pearson VUE, computer based"), ("Format", "Open book"), ("Exam parts", "Technical and Safety, plus Business"),
                 ("Technical and Safety", "100 questions, 5.5 hours"), ("Business", "50 questions, about 2 hours")]
    elif g == "inspectors":
        rows += [("Exam parts", ", ".join(exam_list(c))), ("ICC exam", "Taken through ICC with Pearson VUE"), ("Principles and Practice", "Scheduled with Pearson VUE")]
    elif g == "county":
        rows += [("Exam vendor", "Prov or GITS, set by the county"), ("Format", "Open book on most trade exams"), ("Also often required", "A county Business and Law exam")]
    else:
        rows += [("Who needs it", CLASSES[c]["who"].capitalize())]
    return "".join(f'<tr><th scope="row">{e(a)}</th><td>{e(b)}</td></tr>' for a, b in rows)


def who_text(c):
    k = CLASSES[c]
    g = k["group"]
    base = f"The Florida {short_name(c)} license {k['scope']}. Most buyers are {k['who']}."
    if g in ("div1", "div2"):
        return base + " A state certified license lets you work anywhere in Florida, and it is issued to you as the qualifier of your business."
    if g == "electrical":
        return base + " The state certification lets you contract statewide, while counties still issue journeyman cards."
    if g == "inspectors":
        return base + " Florida licenses inspectors and plans examiners through DBPR, and local building departments hire from that list."
    if g == "county":
        return base + " A county card is good only where that county or city recognizes it, so check with your local licensing office."
    return base


def exam_text(c):
    g = CLASSES[c]["group"]
    if c == "nascla-commercial-general-building":
        return "Florida accepts a passing NASCLA Commercial General Building score in place of its own trade exam. You still pass Florida Business and Finance and a Florida Building Code portion."
    if g == "div1":
        return f"Division I candidates pass 3 parts: Contract Administration, Project Management and Business and Finance. {BF}"
    if g == "div2":
        return f"Division II candidates pass the {short_name(c)} trade knowledge exam and Business and Finance. {BF}"
    if g == "electrical":
        return "ECLB certification exams come in 2 parts, Technical and Safety and Business, both taken at Pearson VUE. The Technical and Safety part has 100 questions in 5.5 hours, and the Business part has 50."
    if g == "inspectors":
        return "Florida inspector and plans examiner candidates pass an ICC technical exam and the Florida Principles and Practice exam, which Pearson VUE schedules after DBPR authorizes you."
    if g == "county":
        return "County exams are set by each county board and given by Prov or GITS, so the book list follows your county's bulletin. Many counties also require a Business and Law exam."
    return BF


def class_faq(c):
    n = short_name(c)
    ps = paid(listed[c])
    cheapest = min(ps, key=lambda p: p["lo"])
    g = CLASSES[c]["group"]
    demo = next((p for p in listed[c] if p["tkey"] == "demo"), None)
    qas = [
        (f"Who needs the Florida {n} license?", who_text(c)),
        (f"What exams do I take for {n}?", exam_text(c)),
        ("Is the Florida contractor exam open book?", "Yes. The state construction and electrical exams are open book, but only the references in the Candidate Information Booklet are allowed, so tabbed and highlighted books save time."),
        (f"What is the cheapest way to prepare for {n}?", f"The lowest priced item here is {e(cheapest['title'])} at {money(cheapest['lo'])}. Most candidates pair the books with a course."),
    ]
    if g in ("div1", "div2"):
        qas.append(("How do I schedule the exam?", "Register with Professional Testing, Inc. and get approved, then book your seats with Pearson VUE. You can test before you apply for the license itself."))
        qas.append(("Do I have to take Business and Finance again for a second license?", "No. A current, active CILB licensee who tests for a new category is exempt from Business and Finance under rule 61G4-16.0015."))
    elif g == "electrical":
        qas.append(("How do I schedule the electrical exam?", "Apply to DBPR for the ECLB exam, and once you are approved, book the Technical and Safety and Business parts with Pearson VUE."))
    elif g == "inspectors":
        qas.append(("Do I need to pass Principles and Practice too?", "Yes. DBPR issues an inspector or plans examiner license only after you pass the ICC technical exam and the Florida Principles and Practice exam."))
    elif g == "business":
        qas.append(("Who has to pass Business and Finance?", "Every certified construction contractor passes it once, whatever the trade. Electrical contractors take the ECLB business exam instead, and a current CILB licensee adding a category is exempt."))
        qas.append(("Can I buy a single book instead of a package?", "Yes. Single references, tabs and the Florida Contractors Manual are sold on their own, so you can fill gaps in a library you already own."))
    elif g == "county":
        qas.append(("Which county uses which exam?", "Each county board picks Prov or GITS and lists the books in its bulletin. Check with your county licensing office, then match the book list here."))
    if demo:
        qas.append(("Can I try the prep before I buy?", f"Yes. The {e(demo['title'])} is free, so you can see how the questions and explanations work first."))
    qas.append(("How fast do orders ship?", f"Books ship free by USPS Media Mail from 1 Exam Prep, and online courses open by email. Call {PHONE} with a deadline for the fastest option."))
    return qas[:8]


def class_takeaways(c):
    ps = listed[c]
    pp = paid(ps)
    g = CLASSES[c]["group"]
    demo = any(p["tkey"] == "demo" for p in ps)
    part = partner_for(c)
    best = pick(c, "books-course") or pick(c, "books")
    out = [f"{len(ps)} {short_name(c)} prep products, from {money(min(p['lo'] for p in pp))} to {money(max(p['hi'] for p in pp))}."]
    if g in ("div1", "div2", "electrical", "inspectors"):
        if g in ("div1", "div2"):
            out.append(f"To get this license you pass {exam_sentence(c)}, open book, with 70% needed on each CILB part.")
        elif g == "electrical" and c not in ("electrical-business",):
            out.append("To get this license you pass the Technical and Safety exam and the Business exam, both open book at Pearson VUE.")
        else:
            out.append(f"To get this license you pass {exam_sentence(c)} at Pearson VUE.")
    elif g == "county":
        out.append("Counties license this trade, and Prov or GITS give the exam, so match the books to your county's bulletin.")
        nc = sum(1 for p in ps if p["tkey"] in ("course", "live", "practice") or p["ptype_raw"] in ("Online Course", "Practice Course", "Live Training"))
        out.append(f"{nc} of the {len(ps)} items are online courses or practice tests; the rest are books, tabs and study guides.")
    else:
        out.append(f"{fl(short_name(c))} {CLASSES[c]['scope'].split(';')[0].rstrip('.')}.")
    if part and best:
        a = addon(c, "books-course") or addon(c, "books")
        if a:
            out.append(f"The most popular path pairs {best['title']} with {short_name(part)} prep for {money(best['lo'] + a['lo'])} in one order.")
    if g in ("div1", "div2"):
        out.append("A current, active CILB licensee adding this license skips Business and Finance.")
    if demo:
        out.append("A free AI tutor demo lets you try the questions before you buy.")
    out.append("Every Buy now button goes straight to secure checkout at our fulfillment center, 1 Exam Prep.")
    return out[:5]


def class_page(c):
    k = CLASSES[c]
    n, sn = k["name"], short_name(c)
    ps = listed[c]
    lo = low(c)
    path = cls_url(c)
    title = f"Florida {sn} Exam Prep | Books and Courses"
    if len(title) > 60:
        title = f"Florida {sn} Exam Prep"
    if len(title) > 60:
        title = f"{sn} Exam Prep"[:60]
    if len(title) < 30:
        title = f"{title} | Florida Books"
    desc = f"Florida {sn} exam prep: {len(ps)} packages from {money(lo)}, including highlighted and tabbed books, courses and rentals. Ships from 1 Exam Prep."
    if len(desc) > 160:
        desc = f"{len(ps)} Florida {sn} exam prep packages from {money(lo)}: tabbed books, courses and rentals."[:160]
    if len(desc) < 70:
        desc += " Open-book ready."
    exams = exam_list(c)
    lead = (f"The Florida {sn} license {k['scope'].split(';')[0].split(', which')[0].split(', so')[0]}. We carry {len(ps)} prep packages for it, "
            f"starting at {money(lo)}. Pick a ready-made exam path below, or choose books, a course or an all-in-one package on its own.")
    if words(lead) > 60:
        lead = (f"The Florida {sn} license {k['scope'].split(',')[0]}. We carry {len(ps)} prep packages for it, "
                f"starting at {money(lo)}. Pick a ready-made exam path below, or choose books or a course on its own.")
    if words(lead) < 40:
        lead += f" Every package ships from 1 Exam Prep, the team behind this site."
    qas = class_faq(c)
    crumb = [("Home", "/"), (sn, path)]
    types = []
    for p in ps:
        if p["tkey"] not in [t[0] for t in types]:
            types.append((p["tkey"], p["tlabel"]))
    chips = "".join(f'<button type="button" class="chip" data-filter="{t}">{e(l)}</button>' for t, l in types)
    chips = f'<div class="chips" role="group" aria-label="Filter by package type"><button type="button" class="chip on" data-filter="all">All {len(ps)}</button>{chips}</div>' if len(types) > 1 else ""
    big = [p for p in ps if p["torder"] <= 5]
    small = [p for p in ps if p["torder"] > 5]
    if len(ps) <= 9 or not big or not small:
        chunks = [ps[i:i + 9] for i in range(0, len(ps), 9)]
        heads = ["Which package should you buy?"] + [f"More {sn} packages" + (f", part {j + 2}" if len(ps) > 18 else "") for j, _ in enumerate(chunks[1:])]
    else:
        chunks = [big[i:i + 9] for i in range(0, len(big), 9)] + [small[i:i + 9] for i in range(0, len(small), 9)]
        nb = len(range(0, len(big), 9))
        heads = ["Which package should you buy?"] + [f"More complete packages, part {j + 2}" for j in range(nb - 1)] + ["Books, courses and add-ons"] + [f"More books and add-ons, part {j + 2}" for j in range(len(chunks) - nb - 1)]
    used_ids = set()
    grid_html = ""
    for i, (h, ch) in enumerate(zip(heads, chunks)):
        hid = slugify(h, 40)
        while hid in used_ids:
            hid += "-2"
        used_ids.add(hid)
        lo_c, hi_c = min(p["lo"] for p in paid(ch)), max(p["hi"] for p in ch)
        intro = (f"The {len(ch)} {sn} packages in this group run from {money(lo_c)} to {money(hi_c)}. "
                 f"Complete packages save the most study hours, while single books suit candidates who already own part of the library.")
        grid_html += f'<section class="sec"><h2 id="{hid}">{e(h)}</h2><p>{intro}</p>{chips if i == 0 else ""}<div class="grid">{"".join(card(p) for p in ch)}</div></section>'
    related = [r for r in GROUP_CLASSES[k["group"]] if r != c][:4]
    part = partner_for(c)
    if part:
        related = [part] + related
    related = [r for r in dict.fromkeys(related) if r != c][:5]
    rel = "".join(f'<li><a href="{cls_url(r)}">{e(short_name(r))} exam prep</a></li>' for r in related)
    item_list = {"@context": "https://schema.org", "@type": "CollectionPage", "name": f"Florida {sn} exam prep", "url": SITE + path,
                 "description": desc, "dateModified": UPDATED, "publisher": PUB, "isPartOf": {"@id": SITE + "/#website"},
                 "about": {"@type": "Thing", "name": f"Florida {n} license"},
                 "mainEntity": {"@type": "ItemList", "numberOfItems": len(ps), "itemListElement": [
                     {"@type": "ListItem", "position": i + 1, "url": SITE + p["url"], "name": p["title"]} for i, p in enumerate(ps)]}}
    pb = path_box(c)
    first_hid = "your-exam-path" if pb else slugify(heads[0], 40)
    body = f"""{header()}<main id="main">
<section class="phero phero-class">
  <div class="wrap">
    {crumb_html(crumb)}
    <div class="phero-ic">{icon(c)}</div>
    <div class="eyebrow">{e(GNAME[k['group']])}</div>
    <h1>Florida {e(sn)} exam prep</h1>
    <p class="lead">{lead}</p>
    <ol class="pathline" aria-label="Exams on this path">{''.join(f'<li><span>{i + 1}</span>{e(x)}</li>' for i, x in enumerate(exams))}<li class="done"><span>&#10003;</span>Licensed</li></ol>
  </div>
</section>
<div class="wrap cols">
<div class="main-col">
{takeaways(class_takeaways(c))}
<section class="sec"><h2 id="who-needs-it">Who needs the Florida {e(sn)} license?</h2><p>{e(who_text(c))}</p></section>
<section class="sec"><h2 id="what-is-on-the-exam">What is on the {e(sn)} exam?</h2><p>{e(exam_text(c))}</p>
<table class="facts-table reveal"><caption>{e(sn)} exam at a glance</caption><tbody>{exam_rows(c)}</tbody></table></section>
{pb}
{grid_html}
<section class="sec"><h2 id="related-licenses">Related Florida licenses</h2><p>Many contractors add a second license once the first is approved, and a current CILB licensee skips Business and Finance the second time. These pages cover the closest matches.</p><ul class="links">{rel}<li><a href="/how-to-get-licensed/">How to get a Florida contractor license</a></li></ul></section>
{faq_html(qas)}
{sources_html(group_sources(c))}
</div>
{rail_class(c, first_hid)}
</div>
</main>
{footer()}"""
    write(path, head(title, desc, path, [crumbs(crumb), item_list, faq_ld(qas)]) + body)


# ---------------------------------------------------------------- product pages
def product_takeaways(p, a):
    c = p["cls"]
    sn = short_name(c)
    free = p["lo"] == 0
    what = f"for the Florida {sn} exam" if CLASSES[c]["group"] != "business" else f"from the {fl(sn)} range"
    out = [f"{p['tlabel']} {what}: {'free' if free else price_span(p)}"
           + (f", down from {money(p['compare'])}." if p["compare"] > p["hi"] else ".")]
    if exam_sentence(c):
        out.append(f"The {sn} license takes {exam_sentence(c)}.")
    else:
        out.append(f"{fl(sn)} {CLASSES[c]['scope'].split(';')[0]}.")
    if a:
        out.append(f"Add {a['title']} ({money(a['lo'])}) to cover the second exam in the same order.")
    ship = schemakit.ships(p["title"], p["ptype_raw"])
    out.append("Books ship free by USPS Media Mail inside the U.S." if ship else "Online access arrives by email, with nothing to ship.")
    if not free:
        out.append("The 1 Exam Prep store lists all sales as final, so check the contents with the team before you buy if unsure.")
    return out


def product_page(p):
    c = p["cls"]
    sn = short_name(c)
    path = p["url"]
    tdesc, includes = TYPE_HELP[p["tkey"]]
    sents = clean_sentences(p["desc"], p["title"], 3)
    short = re.sub(r"\s*[\(\[].*?[\)\]]", "", p["title"]).strip(" -;:")
    short = short if len(short) < 70 else short[:67].rsplit(" ", 1)[0]
    title = short if len(short) <= 60 else short[:58].rsplit(" ", 1)[0]
    if len(title) < 30:
        title = f"{title} | Florida Exam Prep"[:60]
    price = price_span(p)
    free = p["lo"] == 0
    desc = (f"{short}: free AI tutor demo for the Florida {sn} exam. Try sample questions before you buy." if free else
            f"{short}: {p['tlabel'].lower()} for the Florida {sn} exam. {price}. Ships from 1 Exam Prep.")
    if len(desc) > 160:
        desc = (f"Free AI tutor demo for the Florida {sn} exam. Try sample questions before you buy." if free else
                f"{p['tlabel']} for the Florida {sn} exam, {price}. Ships from 1 Exam Prep.")
    if len(desc) > 160:
        desc = desc[:157].rsplit(" ", 1)[0] + "."
    if len(desc) < 70:
        desc += " Open-book exam ready."
    art = "an" if p['tlabel'].lower()[0] in "aeiou" else "a"
    lead = (f"The {short} is {art} {p['tlabel'].lower()} for the Florida {sn} exam, {'free of charge' if free else 'priced at ' + price}. "
            f"{tdesc} {'Get it' if free else 'Buy now'} opens secure checkout at 1 Exam Prep.")
    while words(lead) > 60 and lead.count(". ") > 1:
        lead = lead.rsplit(". ", 1)[0] + "."
    if words(lead) < 40:
        lead += f" Books ship free by USPS Media Mail, and online access arrives by email."
    if words(lead) < 40:
        lead += f" Call {PHONE} with any question first."
    inc = "".join(f"<li>{e(i)}</li>" for i in includes)
    about = " ".join(e(s) for s in sents) or e(tdesc)
    gone = re.search(r"no longer be issued after ([A-Z][a-z]+ \d{1,2}, \d{4})", p["desc"])
    if gone:
        about = (f"Check before you buy: the store notes that the county stopped issuing this license after {gone.group(1)}, "
                 f"under Florida House Bills 735 and 1383, which limited local licensing of some specialty trades. ") + about
    cmp = f'<s>{money(p["compare"])}</s>' if p["compare"] > p["hi"] else ""
    sibs = [s for s in listed[c] if s is not p and s["tkey"] != "demo"][:3]
    sib = "".join(f'<li><a href="{s["url"]}">{e(s["title"])}</a> <span>{money(s["lo"])}</span></li>' for s in sibs)
    part = partner_for(c)
    a = addon(c, "books" if p["tkey"] in ("ht", "books", "combo", "tabs", "book") else "course") if part and p["tkey"] not in ("one-package", "demo", "service", "ce") else None
    pair = ""
    if a:
        pair = (f'<section class="sec"><h2 id="pair-it">What else do you need for the {e(sn)} license?</h2><p>The {e(sn)} license takes {e(" and ".join(exam_list(c)[-2:]))}. '
                f'Most candidates buy the second exam prep at the same time, so the books arrive together. The usual pick is the '
                f'<a href="{a["url"]}">{e(a["title"])}</a> at {money(a["lo"])}, which brings this order to {money(p["lo"] + a["lo"])}.</p>'
                f'<p><a class="btn ghost" href="{p["cart"]},{a["variant"]}:1" rel="nofollow">Buy both for {money(p["lo"] + a["lo"])}</a></p></section>')
    qas = [
        (f"Which exam is the {short} for?", f"The {short} is built for the Florida {sn} exam. {exam_text(c)}"),
        ("Can I bring these books into the exam?", "Florida state exams are open book, but only the references named in the Candidate Information Booklet are allowed. Highlighting and permanent tabs are generally allowed; loose notes are not."),
        ("How much does it cost?", ("The demo is free. You only enter your details at checkout so the demo can be sent to you." if free else
                                    f"The {short} costs {price} before tax{', down from ' + money(p['compare']) if p['compare'] > p['hi'] else ''}. Books ship free by USPS Media Mail.")),
        ("How do I check out?", f"{'Get the free demo' if free else 'Buy now'} opens the secure 1 Exam Prep checkout with this item in the cart. Questions before you order go to {PHONE} or {EMAIL}."),
        ("When should I order?", "Order as soon as you decide on a test date. Books take days to arrive, and the tabs and highlights are worth a full week of practice before the exam."),
        ("Can I return it?", "The 1 Exam Prep store lists all sales as final, so check the package contents with the team before you buy if you are unsure."),
    ]
    crumb = [("Home", "/"), (sn, cls_url(c)), (short, path)]
    offers = {"@type": "Offer", "price": f"{p['lo']:.2f}", "priceCurrency": "USD", "availability": "https://schema.org/InStock",
              "url": SITE + path, "seller": schemakit.STORE_SELLER, "priceValidUntil": "2027-12-31"}
    if p["hi"] > p["lo"]:
        offers = {"@type": "AggregateOffer", "lowPrice": f"{p['lo']:.2f}", "highPrice": f"{p['hi']:.2f}", "priceCurrency": "USD",
                  "offerCount": 2, "availability": "https://schema.org/InStock", "url": SITE + path, "seller": schemakit.STORE_SELLER}
    cond = schemakit.condition(p["title"], p["ptype_raw"])
    if cond:
        offers["itemCondition"] = cond
    offers.update(schemakit.delivery_fields(p["title"], p["ptype_raw"]))
    prod = {"@context": "https://schema.org", "@type": "Product", "name": p["title"], "url": SITE + path, "sku": str(p["sku"]),
            "description": desc, "brand": {"@type": "Brand", "name": "1 Exam Prep"}, "category": f"Florida {sn} exam prep",
            "image": [p["img"]] if p["img"] else [SITE + "/assets/logo.png"], "offers": offers}
    page_ld = {"@context": "https://schema.org", "@type": "WebPage", "url": SITE + path, "name": title, "dateModified": UPDATED, "publisher": PUB}
    body = f"""{header()}<main id="main">
<div class="wrap">
{crumb_html(crumb)}
<div class="pdp">
  <div class="pdp-img reveal">{img_tag(p, 900, eager=True)}</div>
  <div class="pdp-buy">
    <div class="eyebrow">{e(p['tlabel'])}</div>
    <h1>{e(p['title'])}</h1>
    <p class="lead">{e(lead)}</p>
    <p class="bigprice">{cmp} <b>{price}</b></p>
    <a class="btn" href="{p['cart']}" rel="nofollow">{"Get the free demo" if free else "Buy now"}</a>
    <ul class="assure"><li>Secure checkout at 1 Exam Prep</li><li>Questions? Call <a href="tel:{PHONE_TEL}">{PHONE}</a></li><li>Free USPS Media Mail on books</li></ul>
  </div>
</div>
<div class="cols"><div class="main-col">
{takeaways(product_takeaways(p, a))}
<section class="sec"><h2 id="whats-included">What does the {e(short)} include?</h2><p>{about}</p><ul class="ticks">{inc}</ul></section>
<section class="sec"><h2 id="which-exam">Which Florida exam is it for?</h2><p>The <a href="{cls_url(c)}">Florida {e(sn)} license</a> {e(CLASSES[c]['scope'])}. {e(exam_text(c))}</p></section>
{pair}
<section class="sec"><h2 id="how-to-study">How should you study with it?</h2><p>{e(STUDY[p['tkey']])} The <a href="/how-to-get-licensed/">licensing guide</a> lays out the order of the steps, from registering with PTI to booking Pearson VUE.</p></section>
<section class="sec"><h2 id="other-packages">Other {e(sn)} packages</h2><p>Compare these before you buy, or see every option and the ready-made exam paths on the <a href="{cls_url(c)}">{e(sn)} page</a>.</p><ul class="links">{sib}<li><a href="/#exam-path">Build your exam path</a></li></ul></section>
{faq_html(qas)}
{sources_html(group_sources(c))}
</div>{rail_product(p, price)}</div>
</div>
</main>
{footer()}"""
    write(path, head(title, desc, path, [crumbs(crumb), prod, page_ld, faq_ld(qas)], og_img=p["img"] or "/assets/logo.png") + body)


# ---------------------------------------------------------------- finder data for the exam path picker
def finder_json():
    prods, idx = [], {}

    def ref(p):
        if p is None:
            return None
        k = id(p)
        if k not in idx:
            idx[k] = len(prods)
            prods.append({"t": p["title"], "u": p["url"], "p": p["lo"], "c": p["compare"] if p["compare"] > p["hi"] else 0, "v": p["variant"],
                          "k": p["tlabel"], "inc": TYPE_HELP[p["tkey"]][1][:3], "i": (p["img"] + ("&" if "?" in p["img"] else "?") + "width=240") if p["img"] else ""})
        return idx[k]
    lic = []
    for c in live_classes:
        ch = {}
        for key, _, _ in PATH_CHOICES:
            p = pick(c, key)
            if p:
                ch[key] = [ref(p), ref(addon(c, key))]
        part = partner_for(c)
        lic.append({"id": c, "n": short_name(c), "g": CLASSES[c]["group"], "u": cls_url(c), "x": exam_list(c), "count": len(listed[c]), "ch": ch,
                    "pn": short_name(part) if part else ""})
    data = {"updated": UPDATED, "choices": [[k, l] for k, l, _ in PATH_CHOICES], "groups": [[g, n] for g, n, _ in GROUPS], "licenses": lic, "products": prods}
    write("assets/finder.json", json.dumps(data, separators=(",", ":"), ensure_ascii=False))


# ---------------------------------------------------------------- home
HOME_FAQ = [
    ("Who issues contractor licenses in Florida?", "The Florida Department of Business and Professional Regulation (DBPR) issues state licenses through the Construction Industry Licensing Board (CILB) for construction trades and the Electrical Contractors' Licensing Board (ECLB) for electrical work. Counties issue journeyman cards and local certificates."),
    ("How many exams does a Florida contractor take?", "Division I contractors (general, building and residential) pass 3 parts: Contract Administration, Project Management and Business and Finance. Division II trades pass 2: their trade exam and Business and Finance."),
    ("What is the Florida Business and Finance exam?", BF),
    ("Is the Florida contractor exam open book?", "Yes. The CILB and ECLB exams are open book, but you may bring only the references listed in the Candidate Information Booklet for your exam."),
    ("Who gives the Florida contractor exams?", "You register with Professional Testing, Inc. (PTI) and, once approved, schedule your seats with Pearson VUE, which gives the exams on computer."),
    ("Does Florida accept the NASCLA exam?", "Yes. Since March 1, 2019 the CILB has accepted the NASCLA Commercial General Building exam in place of the Florida trade exam. Business and Finance and a Florida Building Code portion are still required."),
    ("Do I need Business and Finance for a second license?", "No. A current, active CILB licensee who tests for a new category is exempt from Business and Finance under rule 61G4-16.0015 of the Florida Administrative Code."),
    ("How do I order?", f"Use the exam path picker to choose your license and package, then press Buy now for secure checkout at 1 Exam Prep. Call {PHONE} for help choosing."),
]


def hero_wall():
    """Three slow rows of real product photos from the store (book sets and packages)."""
    seen, pics = set(), []
    for p in sorted(products, key=lambda x: (x["tkey"] not in ("ht", "books", "one-package", "ultimate", "rental"), x["title"])):
        if p["img"] and p["img"] not in seen and p["tkey"] in ("ht", "books", "one-package", "ultimate", "rental", "accelerator"):
            seen.add(p["img"])
            pics.append(p)
    pics = pics[:36]
    rows = ""
    for r in range(3):
        imgs = "".join(img_tag(p, 240) for p in pics[r::3])
        rows += f'<div class="wall-row r{r + 1}"><div class="wall-track">{imgs}</div></div>'
    return f'<div class="wall" aria-hidden="true">{rows}</div>'


SVG = {
    "target": '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1.5"/>',
    "calendar": '<rect x="4" y="5" width="16" height="15" rx="2"/><path d="M8 3v4M16 3v4M4 10h16M9 14h2M13 14h2M9 17h2"/>',
    "books": '<path d="M4 8l8-4 8 4-8 4z"/><path d="M4 12l8 4 8-4M4 16l8 4 8-4"/>',
    "bolt": '<path d="M13 3L5 14h6l-1 7 8-11h-6z"/>',
    "star": '<path d="M12 4l2.4 4.9 5.4.8-3.9 3.8.9 5.4-4.8-2.5-4.8 2.5.9-5.4L4.2 9.7l5.4-.8z"/>',
    "check": '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
    "phone": '<path d="M6.6 10.8a15 15 0 006.6 6.6l2.2-2.2a1 1 0 011-.25 11.4 11.4 0 003.6.6 1 1 0 011 1V20a1 1 0 01-1 1A17 17 0 013 4a1 1 0 011-1h3.5a1 1 0 011 1c0 1.25.2 2.45.6 3.6a1 1 0 01-.25 1z"/>',
    "chev": '<path d="M6 9l6 6 6-6"/>',
}


def svg(name, cls="i"):
    return f'<svg class="{cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{SVG[name]}</svg>'


STYLES = [("books-course", "Books + course"), ("books", "Books only"), ("course", "Course only"), ("everything", "Everything")]
START_LIC, START_STYLE = "general-contractor", "books-course"


def rec_html(c, choice):
    """The recommendation box, rendered here for the first paint; assets/site.js redraws it on every change."""
    p = pick(c, choice)
    a = addon(c, choice)
    if not p:
        return '<p class="r-empty">Pick a license to see your package.</p>'
    inc = TYPE_HELP[p["tkey"]][1][:3] + ([f"{short_name(partner_for(c))} prep added"] if a else [])
    total = p["lo"] + (a["lo"] if a else 0)
    cart = p["cart"] + (f",{a['variant']}:1" if a else "")
    img = img_tag(p, 240)
    add = (f'<label class="r-add"><input type="checkbox" checked data-add> Include <a href="{a["url"]}">{e(a["title"])}</a> (+{money(a["lo"])})</label>') if a else ""
    lis = "".join(f"<li>{svg('check')}{e(x)}</li>" for x in inc)
    return (f'<div class="r-body"><div class="r-img">{img}</div><ul class="r-list2">{lis}</ul></div>{add}'
            f'<div class="r-foot"><div><p class="r-name"><a href="{p["url"]}">{e(p["title"])}</a></p><p class="r-sub">{e(p["tlabel"])}{" + " + e(short_name(partner_for(c))) if a else ""}</p></div>'
            f'<p class="r-price" data-total>{money(total)}</p></div>'
            f'<a class="btn go" data-buy href="{cart}" rel="nofollow">Get my recommended package</a>')


def picker():
    groups = "".join(f'<option value="{g}"{" selected" if g == "div1" else ""}>{e(n)}</option>' for g, n, _ in GROUPS)
    chips = ""
    for g, _, _ in GROUPS:
        for i, c in enumerate(GROUP_CLASSES[g]):
            on = " on" if c == START_LIC else ""
            hide = "" if g == "div1" else " hidden"
            chips += f'<button type="button" class="lchip{on}" data-g="{g}" data-lic="{c}"{hide}>{svg("check", "i ck")}{e(short_name(c))}</button>'
    styles = "".join(f'<button type="button" class="seg{" on" if k == START_STYLE else ""}" data-choice="{k}">{e(l)}</button>' for k, l in STYLES)
    feats = [("target", "License match"), ("calendar", "Study plan"), ("books", "Book bundle"), ("bolt", "Instant recommendation")]
    feat = "".join(f"<li>{svg(i)}<span>{t}</span></li>" for i, t in feats)
    return f"""<form class="path" id="path-form" action="/#find-your-license" aria-label="Build your exam path" data-start="{START_LIC}">
  <ul class="p-feats">{feat}</ul>
  <div class="p-step">
    <p class="p-h"><span class="p-n">1</span><label for="path-group">Select your license type</label></p>
    <div class="sel">{svg("chev", "i chev")}<select id="path-group" name="group">{groups}</select></div>
  </div>
  <div class="p-step">
    <p class="p-h"><span class="p-n">2</span>Choose your contractor category</p>
    <div class="lchips" data-more-at="5">{chips}</div>
  </div>
  <div class="rec" aria-live="polite">
    <div class="rec-h">{svg("star", "i star")}<div><p class="rec-t">Your personalized recommendation</p><p class="rec-s">The best books and course for your Florida <b data-licname>{e(short_name(START_LIC))}</b> license.</p></div></div>
    <div class="segs" role="group" aria-label="How do you want to study?">{styles}</div>
    <div class="p-result">{rec_html(START_LIC, START_STYLE)}</div>
  </div>
</form>"""


def home():
    path = "/"
    total = len(products)
    ncls = len(live_classes)
    title = "Pass Your Florida Contractor Exam | CILB Exam Prep"
    desc = f"Florida contractor exam prep for {ncls} licenses: tabbed books, courses and Business and Finance prep for the open-book CILB and ECLB exams. {total} packages."
    if len(desc) > 160:
        desc = f"Florida contractor exam prep for {ncls} licenses: tabbed books, courses and Business and Finance prep for the open-book state exams."
    lead = ("We help Florida contractors choose the right books, prep course and license path quickly, so you can study with "
            "confidence and get licensed faster. Most licenses take a trade exam plus the 120-question Business and Finance "
            "exam, and we cover both in one order.")
    groups_html = ""
    gintro = {"div1": "Division I licenses cover whole buildings. Each takes Contract Administration, Project Management and Business and Finance.",
              "div2": "Division II licenses cover one trade. Each takes its own trade knowledge exam plus Business and Finance.",
              "electrical": "The Electrical Contractors' Licensing Board certifies these. Each takes Technical and Safety plus a business exam.",
              "inspectors": "Inspector and plans examiner licenses take an ICC technical exam plus Florida Principles and Practice.",
              "county": "Counties license journeyman electricians and plumbers and issue local certificates. Prov and GITS give the exams.",
              "business": "Start here if you already know your trade, need a single reference or want the paperwork handled."}
    for g, gname, _ in GROUPS:
        cs = GROUP_CLASSES[g]
        if not cs:
            continue
        cards = "".join(f'<a class="ccard reveal" href="{cls_url(c)}" data-name="{e(cls_name(c).lower())}"><span class="c-ic">{icon(c)}</span>'
                        f'<span class="c-n">{e(short_name(c))}</span><span class="c-m">{len(listed[c])} packages, from {money(low(c))}</span></a>' for c in cs)
        groups_html += f'<section class="sec grp" data-group><h2 id="{slugify(gname, 40)}">{e(gname)}</h2><p>{gintro[g]}</p><div class="cgrid">{cards}</div></section>'
    steps = [
        ("Pick your license", f"Match your work to 1 of the {ncls} licenses on this site, from General Contractor to Irrigation."),
        ("Register for the exams", "Register with Professional Testing, Inc. (PTI). Once approved, book your seats with Pearson VUE."),
        ("Pass each part", "Score 70% on every part with your tabbed books, usually Business and Finance plus 1 or 2 trade parts."),
        ("Set up the business", "Register the company with the Florida Division of Corporations and line up insurance."),
        ("Apply to DBPR", "Send the license application with your scores, credit report and proof of experience."),
    ]
    tl = "".join(f'<li class="step reveal"><span class="s-num">{i + 1}</span><h3 id="step-{i + 1}">{e(a)}</h3><p>{e(b)}</p></li>' for i, (a, b) in enumerate(steps))
    trows = [("General, Building, Residential", "CILB", "Business and Finance, Contract Administration, Project Management"),
             ("Division II trades", "CILB", "Business and Finance, trade knowledge"),
             ("NASCLA Commercial General Building", "CILB", "NASCLA exam, Business and Finance, Florida Building Code portion"),
             ("Electrical contractors", "ECLB", "Technical and Safety, Business"),
             ("Inspectors and plans examiners", "BCAIB", "ICC technical exam, Principles and Practice"),
             ("Journeyman and county cards", "County board", "County trade exam, often Business and Law")]
    trows = "".join(f'<tr><th scope="row">{a}</th><td>{b}</td><td>{c}</td></tr>' for a, b, c in trows)
    site_ld = {"@context": "https://schema.org", "@type": "WebSite", "@id": SITE + "/#website", "name": BRAND, "url": SITE + "/", "publisher": {"@id": SITE + "/#org"}, "inLanguage": "en-US"}
    org_ld = dict({"@context": "https://schema.org"}, **ORG)
    page_ld = {"@context": "https://schema.org", "@type": "WebPage", "url": SITE + "/", "name": title, "description": desc, "datePublished": CFG["launched"], "dateModified": UPDATED, "publisher": {"@id": SITE + "/#org"}}
    bf_lo = low("business-and-finance")
    body = f"""{header()}<main id="main">
<section class="hero">
  <picture class="hero-photo"><source media="(max-width: 980px)" type="image/webp" srcset="/assets/img/hero-m-780.webp"><source media="(max-width: 980px)" srcset="/assets/img/hero-m-780.jpg"><source type="image/webp" srcset="/assets/img/hero-1200.webp 1200w, /assets/img/hero-1717.webp 1717w" sizes="70vw"><img src="/assets/img/hero-1200.jpg" srcset="/assets/img/hero-1200.jpg 1200w, /assets/img/hero-1717.jpg 1717w" sizes="70vw" width="1717" height="916" alt="Florida contractor in a white hard hat and safety vest beside exam prep books, with a waterfront skyline at sunset behind him" fetchpriority="high"></picture>
  <div class="wrap hero-in">
    <div class="hero-txt">
      <p class="kicker">Florida contractor license exam prep</p>
      <h1><span class="h-line"><span>Pass your Florida</span></span> <span class="h-line hot"><span>contractor exam.</span></span></h1>
      <p class="lead">{lead}</p>
      <div class="hero-cta"><a class="btn hot" href="#exam-path" data-focus-picker>Get started</a><a class="tlink" href="#find-your-license">See packages</a></div>
    </div>
    <div class="hero-path" id="exam-path">
      {picker()}
    </div>
  </div>
</section>
<section class="stats wrap" aria-label="Key numbers">
  <div class="stat"><b>{ncls}</b><span>Florida licenses covered</span></div>
  <div class="stat"><b>{total}</b><span>prep packages in stock</span></div>
  <div class="stat"><b>120</b><span>Business and Finance questions</span></div>
  <div class="stat"><b>70%</b><span>to pass each part</span></div>
</section>
<div class="wrap">
{takeaways([f"{total} products across {ncls} Florida licenses, from {money(min(p['lo'] for p in products if p['lo'] > 0))} to {money(max(p['hi'] for p in products))}.",
            "Division I licenses (General, Building, Residential) take 3 exam parts; Division II trades take their trade exam plus Business and Finance.",
            "Business and Finance has 120 questions over about 6.5 hours, open book, and every part needs 70%.",
            "Register with Professional Testing, Inc., then book Pearson VUE; in Florida you can pass the exams before you apply.",
            "Every Buy now button goes straight to secure checkout at our fulfillment center, 1 Exam Prep."])}
<section class="sec intro-sec"><h2 id="how-the-exam-path-works">How does the exam path picker work?</h2><p>Florida licenses come with more than one exam, and buying prep for only one of them is the most common mistake. The picker fixes that in 3 taps. Choose your license, choose how you like to study, and it pairs your trade prep with the second exam, such as Business and Finance from {money(bf_lo)}, in a single checkout.</p>
<ol class="mini-steps"><li>Pick a license from the 6 most popular or the full list of {ncls}.</li><li>Pick books, a course, everything done for you or a free demo.</li><li>Press Buy now and both exams are covered in one order.</li></ol></section>
<section class="sec"><h2 id="which-exams">Which exams does each Florida license take?</h2><p>The exams depend on the board that issues your license. The table shows the 6 paths this site covers, with the board and every exam part. All state exams are open book at Pearson VUE.</p>
<div class="tablewrap reveal"><table><caption>Florida contractor exam paths</caption><thead><tr><th scope="col">License</th><th scope="col">Board</th><th scope="col">Exams to pass</th></tr></thead><tbody>{trows}</tbody></table></div></section>
<section class="sec intro-sec"><h2 id="find-your-license">Which Florida license do you need?</h2><p>The CILB sorts contractors into Division I and Division II, the ECLB covers electrical work, and counties handle journeyman cards. Every card below opens the exam facts, a ready-made exam path and every package for that license.</p></section>
{groups_html}
</div>
<section class="band">
  <div class="wrap band-in">
    <div class="band-txt">
      <h2 id="how-do-you-get-licensed">How do you get a Florida contractor license?</h2>
      <p>Getting a Florida state license takes 5 steps, and in Florida you can test before you apply. Pass the exams first, then send DBPR one complete application. The full walkthrough is on the <a href="/how-to-get-licensed/">licensing guide</a>.</p>
      <ol class="timeline" data-timeline>{tl}</ol>
    </div>
  </div>
</section>
<div class="wrap">
<section class="sec split"><div><h2 id="why-tabbed-books">Why do tabbed books matter on an open-book exam?</h2><p>Business and Finance has 120 questions in about 6.5 hours, a little over 3 minutes a question. Candidates who fail usually know the material but lose time hunting through a dozen reference books. Highlighted and tabbed sets put the answer 1 flip away, and the online courses drill the same lookups until they are automatic.</p>
<ul class="ticks"><li>Books matched to the Candidate Information Booklet</li><li>Highlights on the passages exams use most</li><li>Courses that practice with the books open</li></ul></div>
<div class="split-card reveal"><p class="sc-h">Free before you buy</p><p>{len([p for p in products if p['tkey'] == 'demo'])} Florida exams have a free AI tutor demo. Try the questions, then buy the package that fits.</p><a class="btn" href="/general-contractor/#which-package-should-you-buy">See a free demo</a></div></section>
{faq_html(HOME_FAQ)}
{sources_html([SRC_CORE[0], SRC_CORE[1], ("DBPR electrical examinations", DBPR_ELEC), ("NASCLA participating agencies", NASCLA_FL), ("Business and Finance exemption, rule 61G4-16.0015", FAC_BF)])}
</div>
</main>
{footer()}"""
    write(path, head(title, desc, path, [org_ld, site_ld, page_ld, faq_ld(HOME_FAQ)]) + body)


# ---------------------------------------------------------------- guide page
GUIDE_FAQ = [
    ("Can I take the Florida contractor exam before I apply?", "Yes. You register with Professional Testing, Inc. and pass the exams first, then apply to DBPR for the license with your scores."),
    ("How long are Florida exam scores good for?", "Check your score report and the current DBPR rules, since the window to use passing scores can change. Most candidates apply within a few months of passing."),
    ("Do residential and commercial applicants take the same business exam?", "Yes. " + BF),
    ("Does Florida accept NASCLA?", "Yes, for the Division I trade exam. Since March 1, 2019 the CILB accepts NASCLA Commercial General Building scores, and you still pass Business and Finance and a Florida Building Code portion."),
    ("What is the difference between certified and registered?", "A certified license comes from the state exams and lets you work anywhere in Florida. A registered license rests on a local certificate and is limited to the places that issued it."),
    ("Who is the qualifier?", "The qualifier is the licensed person who takes responsibility for a business's contracting work. The license is issued to you, and you qualify the company."),
]


def guide():
    path = "/how-to-get-licensed/"
    title = "How to Get a Florida Contractor License (2026)"
    desc = "How to get a Florida contractor license in 5 steps: CILB divisions, PTI registration, Pearson VUE exams, Business and Finance and the DBPR application."
    lead = ("To get a Florida contractor license, pick your CILB or ECLB license, register with Professional Testing, Inc., pass "
            "the open-book exams at Pearson VUE with 70% on each part, set up the business and apply to DBPR. In Florida you "
            "can pass the exams before you apply.")
    crumb = [("Home", "/"), ("How to get licensed", path)]
    secs = [
        ("certified-or-registered", "Do you need a state license or a county one?",
         "<p>Florida has 2 kinds of contractor license. A <b>certified</b> license comes from the state exams and lets you work anywhere in Florida. A <b>registered</b> license rests on a county or city certificate of competency and is limited to that area. Journeyman electricians and plumbers are always licensed by the county. "
         "<a href=\"/county-exams-gits/\">GITS</a> and <a href=\"/county-exams-prov/\">Prov</a> county exams have their own pages.</p>"
         "<table><caption>Florida license types</caption><thead><tr><th scope=\"col\">License</th><th scope=\"col\">Issued by</th><th scope=\"col\">Where it is good</th></tr></thead><tbody>"
         "<tr><td>Certified contractor</td><td>DBPR (CILB or ECLB)</td><td>Statewide</td></tr><tr><td>Registered contractor</td><td>DBPR, on a local certificate</td><td>The issuing county or city</td></tr>"
         "<tr><td>Journeyman card</td><td>County board</td><td>That county and counties that accept it</td></tr></tbody></table>"),
        ("step-1-license", "Step 1: which license fits your work?",
         f"<p>The CILB splits licenses into 2 divisions. <a href=\"/general-contractor/\">General</a>, <a href=\"/building-contractor/\">Building</a> and <a href=\"/residential-contractor/\">Residential</a> contractors are Division I and pass 3 exam parts. Trades such as <a href=\"/air-a/\">Air A</a>, <a href=\"/roofing/\">Roofing</a> and <a href=\"/plumbing-contractor/\">Plumbing</a> are Division II and pass 2. Electrical work goes to the ECLB, starting with <a href=\"/unlimited-electrical/\">Unlimited Electrical</a>. This site covers {len(live_classes)} licenses.</p>"),
        ("step-2-register", "Step 2: how do you register for the exams?",
         "<p>Register with Professional Testing, Inc. (PTI), which handles CILB exam registration for DBPR. After PTI approves you, schedule each part with Pearson VUE, which gives the exams on computer at testing centers across Florida. Electrical candidates apply to DBPR for the ECLB exam and then book with Pearson VUE.</p>"),
        ("step-3-pass", "Step 3: how do you pass every part?",
         f"<p>Every part is open book, but only the references in the Candidate Information Booklet are allowed. {BF} Division I adds Contract Administration and Project Management. Tabbed, highlighted books and timed practice are what move scores past 70%. Start with <a href=\"/business-and-finance/\">Business and Finance prep</a>, then your trade page.</p>"
         "<ul class=\"ticks\"><li>Read each book's table of contents twice</li><li>Take at least 2 full timed practice exams</li><li>Aim to find any answer in under 3 minutes</li></ul>"),
        ("step-4-business", "Step 4: set up the business",
         f"<p>The license is issued to you, and you qualify your company. Register the business with the <a href=\"{SUNBIZ}\" rel=\"noopener\" target=\"_blank\">Florida Division of Corporations</a>, line up general liability insurance and workers' compensation or an exemption. A <a href=\"/licensing-and-application-services/\">business setup service</a> can handle the filing for you.</p>"),
        ("step-5-apply", "Step 5: apply to DBPR",
         "<p>Send the DBPR application with your passing scores, a credit report, proof of experience and insurance. Division I and Division II applications differ, so use the form for your license. The <a href=\"/licensing-and-application-services/\">application service</a> reviews the file before it goes in, which avoids the most common delay.</p>"),
        ("common-delays", "What delays a Florida license most often?",
         "<p>Most delays come from paperwork, not the exams. Applicants who plan for these 4 problems usually finish faster.</p>"
         "<ol><li>An incomplete DBPR application, which stops review until the missing page arrives.</li>"
         "<li>Waiting to book Pearson VUE until the week you feel ready, when nearby seats may be taken.</li>"
         "<li>Bringing a book that is not in the Candidate Information Booklet, which the proctor will not allow.</li>"
         "<li>Studying only the trade part and skipping Business and Finance, which every certified contractor passes.</li></ol>"),
    ]
    sec_html = "".join(f'<section class="sec"><h2 id="{i}">{e(h)}</h2>{b}</section>' for i, h, b in secs)
    page_ld = {"@context": "https://schema.org", "@type": "WebPage", "name": title, "url": SITE + path, "description": desc, "dateModified": UPDATED, "publisher": PUB}
    howto = {"@context": "https://schema.org", "@type": "HowTo", "name": "How to get a Florida contractor license", "totalTime": "P12W",
             "step": [{"@type": "HowToStep", "position": i + 1, "name": h, "url": SITE + path + "#" + sid, "text": re.sub("<[^>]+>", "", b)[:300]} for i, (sid, h, b) in enumerate(secs[1:6])]}
    body = f"""{header()}<main id="main">
<section class="phero"><div class="wrap">{crumb_html(crumb)}<div class="eyebrow">Licensing guide</div><h1>How to get a Florida contractor license</h1><p class="lead">{lead}</p></div></section>
<div class="wrap cols"><div class="main-col">
{takeaways(["A certified license from the state exams works anywhere in Florida; a registered license works only where the local certificate was issued.",
            "Register with Professional Testing, Inc., then book each exam part at Pearson VUE.",
            "Division I takes 3 parts and Division II takes 2; every part is open book and needs 70%.",
            "Pass the exams first, then send DBPR one complete application with scores, credit report, experience and insurance.",
            f"This site covers {len(live_classes)} Florida licenses, each with its own exam path and prep packages."])}
{sec_html}
{faq_html(GUIDE_FAQ)}
{sources_html([SRC_CORE[0], SRC_CORE[1], ("DBPR electrical examinations", DBPR_ELEC), ("Florida Statutes 489.111", STATUTE_489), ("Florida Division of Corporations", SUNBIZ)])}
</div>{rail_popular("Popular Florida licenses")}</div></main>
{footer()}"""
    write(path, head(title, desc, path, [crumbs(crumb), page_ld, howto, faq_ld(GUIDE_FAQ)]) + body)


# ---------------------------------------------------------------- FAQ page
def faq_page():
    path = "/faq/"
    title = "Florida Contractor Exam FAQ | CILB, ECLB, PTI"
    desc = "Answers on Florida contractor exams: CILB divisions, PTI registration, Pearson VUE, open-book rules, Business and Finance, NASCLA and county cards."
    qas = HOME_FAQ[:4] + GUIDE_FAQ[:2] + [HOME_FAQ[4], HOME_FAQ[5], HOME_FAQ[6], GUIDE_FAQ[4]]
    lead = ("Florida contractors test at Pearson VUE on open-book exams with 70% needed on each part, after registering with "
            "Professional Testing, Inc. The answers below cover the boards, the exam parts, Business and Finance, NASCLA and "
            "county licenses, with links to the official DBPR pages.")
    crumb = [("Home", "/"), ("FAQ", path)]
    half = len(qas) // 2
    body = f"""{header()}<main id="main">
<section class="phero"><div class="wrap">{crumb_html(crumb)}<div class="eyebrow">Questions</div><h1>Florida contractor exam FAQ</h1><p class="lead">{lead}</p></div></section>
<div class="wrap cols"><div class="main-col">
{takeaways(["The CILB licenses construction trades, the ECLB licenses electrical contractors and counties issue journeyman cards.",
            "Business and Finance is 120 questions, open book, and every certified construction contractor passes it once.",
            "The CILB has accepted NASCLA Commercial General Building scores in place of the trade exam since March 1, 2019.",
            "A current, active CILB licensee adding a category skips Business and Finance under rule 61G4-16.0015."])}
{faq_html(qas[:half], "licenses-and-boards", "Licenses and boards")}
{faq_html(qas[half:], "exams-and-scheduling", "Exams and scheduling")}
<section class="sec"><h2 id="exam-facts-at-a-glance">What are the key exam numbers?</h2><p>Florida exam rules come down to a few numbers. The table collects the ones candidates ask about most, from DBPR and published exam outlines.</p>
<table><caption>Florida contractor exam numbers</caption><tbody><tr><th scope="row">Business and Finance</th><td>120 questions, about 6.5 hours, 70% to pass</td></tr><tr><th scope="row">Division I parts</th><td>3: Business and Finance, Contract Administration, Project Management</td></tr><tr><th scope="row">Division II parts</th><td>2: trade knowledge and Business and Finance</td></tr><tr><th scope="row">ECLB Technical and Safety</th><td>100 questions, 5.5 hours</td></tr><tr><th scope="row">ECLB Business</th><td>50 questions</td></tr><tr><th scope="row">NASCLA accepted since</th><td>March 1, 2019</td></tr></tbody></table></section>
<section class="sec"><h2 id="how-to-study-open-book">How should I study for an open-book exam?</h2><p>Open-book exams reward speed with the books more than memory. Business and Finance gives you a little over 3 minutes a question, so the goal is to know where every answer lives.</p>
<ol><li>Tab every approved book the day it arrives, using pre-printed tabs if you have them.</li><li>Read each table of contents twice and note which book covers which topic.</li><li>Take at least 2 full timed practice exams with only the approved books open.</li><li>Look up every missed question and mark the page, so the next lookup takes 1 flip.</li></ol></section>
<section class="sec"><h2 id="which-license-to-pick">Which license page should I start with?</h2><p>Most visitors land on 1 of 6 licenses. Each page lists the exam parts, a ready-made exam path and every package with its price.</p>
<ul class="links"><li><a href="/general-contractor/">General Contractor</a> for unlimited commercial and residential work</li><li><a href="/building-contractor/">Building Contractor</a> for buildings up to 3 stories</li><li><a href="/residential-contractor/">Residential Contractor</a> for homes up to 2 stories</li><li><a href="/air-a/">Class A Air Conditioning</a> for commercial HVAC</li><li><a href="/roofing/">Roofing</a> for roofing contractors</li><li><a href="/unlimited-electrical/">Unlimited Electrical</a> for electrical contractors</li></ul></section>
<section class="sec"><h2 id="still-have-a-question">Still have a question?</h2><p>Call {PHONE} or email <a href="mailto:{EMAIL}">{EMAIL}</a>, and the 1 Exam Prep team will match you with the right books. You can also start from the <a href="/how-to-get-licensed/">licensing guide</a>, the <a href="/business-and-finance/">Business and Finance page</a> or the <a href="/contact/">contact form</a>.</p></section>
{sources_html([SRC_CORE[0], SRC_CORE[1], ("DBPR construction industry FAQ", DBPR_FAQ), ("DBPR electrical examinations", DBPR_ELEC), ("NASCLA participating agencies", NASCLA_FL)])}
</div>{rail_popular("Popular Florida licenses")}</div></main>
{footer()}"""
    write(path, head(title, desc, path, [crumbs(crumb), faq_ld(qas)]) + body)


# ---------------------------------------------------------------- contact page
CONTACT_FAQ = [
    ("How do I contact 1 Exam Prep about a Florida exam?", f"Use the form on this page, call {PHONE} or email {EMAIL}. All 3 reach the same 1 Exam Prep team that ships the orders."),
    ("What should I put in my message?", "Name your license, your Pearson VUE test date if you have one, and which books you already own. That is enough to recommend the right package."),
    ("Can you tell me which license I need?", "The team can walk you through the CILB divisions, the ECLB licenses and county cards. DBPR or your county makes the final call on any application."),
    ("Can I order by phone?", f"Yes. Call {PHONE} and the team can place the order with you, or send you a link to the right package."),
    ("Is help available in Spanish?", "Spanish-language Business and Finance and General, Building and Residential packages are on the site. Mention Spanish in your message and the team will point you to them."),
    ("Does 1 Exam Prep register me for the exam?", "The exam registration and application services can file the PTI registration and DBPR paperwork for you. Pearson VUE still books your seat."),
]


def contact_page():
    path = "/contact/"
    title = "Contact Us | Pass Your Florida Contractor Exam"
    desc = f"Contact 1 Exam Prep about Florida contractor exam prep: send the form, call {PHONE} or email {EMAIL} for help choosing books and courses."
    lead = (f"To reach 1 Exam Prep about a Florida contractor exam, send the form on this page, call {PHONE} or email {EMAIL}. "
            "Tell us your license and your Pearson VUE test date, and the team will point you to the right books, "
            "course or all-in-one package for every exam part.")
    crumb = [("Home", "/"), ("Contact", path)]
    form = (f'<div class="form-card reveal"><div class="form-embed" data-form-id="{FORM_ID}" data-form-name="passyourfloridacontractorexam.com" data-height="560">'
            f'<p class="form-fallback">The contact form is loading. If it does not appear, call <a href="tel:{PHONE_TEL}">{PHONE}</a> '
            f'or email <a href="mailto:{EMAIL}">{EMAIL}</a>.</p></div></div>')
    page_ld = {"@context": "https://schema.org", "@type": ["WebPage", "ContactPage"], "name": title, "url": SITE + path, "description": desc,
               "dateModified": UPDATED, "publisher": PUB, "mainEntity": {"@type": "Organization", "@id": SITE + "/#org", "name": BRAND, "url": SITE + "/",
               "contactPoint": {"@type": "ContactPoint", "contactType": "customer service", "telephone": PHONE_TEL, "email": EMAIL,
                                "areaServed": "US-FL", "availableLanguage": ["English", "Spanish"]}}}
    body = f"""{header()}<main id="main">
<section class="phero"><div class="wrap">{crumb_html(crumb)}<div class="eyebrow">Contact</div><h1>Contact us</h1><p class="lead">{lead}</p></div></section>
<div class="wrap cols"><div class="main-col">
{takeaways([f"Reach 1 Exam Prep by the form on this page, by phone at {PHONE} or by email at {EMAIL}.",
            "Include your license, your Pearson VUE test date and the books you already own for a faster answer.",
            f"The same team that ships every order answers, across {len(products)} Florida products.",
            "DBPR or your county decides every license application; the team helps with products and paperwork."])}
<section class="sec"><h2 id="send-a-message">How do I send a message?</h2><p>Fill in the form below and press submit. Your message goes straight to the 1 Exam Prep team, which handles every order for this site. Include your phone number if you would rather get a call back.</p>{form}</section>
<section class="sec"><h2 id="other-ways-to-reach-us">What are the other ways to reach us?</h2><p>Some questions are faster by phone, especially when a test date is close. Use whichever of the 3 options suits you.</p>
<table><caption>Ways to contact 1 Exam Prep</caption><tbody><tr><th scope="row">Phone</th><td><a href="tel:{PHONE_TEL}">{PHONE}</a></td></tr><tr><th scope="row">Email</th><td><a href="mailto:{EMAIL}">{EMAIL}</a></td></tr><tr><th scope="row">Form</th><td>On this page, answered by the same team</td></tr></tbody></table></section>
<section class="sec"><h2 id="what-to-include">What should you include in your message?</h2><p>A few details let the team recommend the right package on the first reply instead of the third. This site covers {len(live_classes)} Florida licenses, and the approved books differ for each one, so the license matters most of all.</p>
<ul class="ticks"><li>Your license, such as General Contractor, Air A or Unlimited Electrical</li><li>Your Pearson VUE test date, or the month you hope to test</li><li>Which approved books you already own</li><li>Whether you still need Business and Finance or the DBPR application</li></ul></section>
<section class="sec"><h2 id="what-we-help-with">What can the team help with?</h2><p>Most messages fall into 4 groups. The team answers questions about the products and the licensing steps; DBPR and your county decide every application.</p>
<ol><li>Choosing between books, rentals, courses and the all-in-one packages for your license.</li><li>Orders already placed, including shipping and rental returns.</li><li>The PTI registration, the DBPR application and the <a href="/licensing-and-application-services/">application services</a>.</li><li>Preparing for the 120-question <a href="/business-and-finance/">Business and Finance exam</a>.</li></ol>
<p>Before you write, the <a href="/how-to-get-licensed/">licensing guide</a> and the <a href="/faq/">FAQ</a> answer the most common questions about divisions, scheduling and open-book rules.</p></section>
<section class="sec"><h2 id="who-answers">Who answers your message?</h2><p>1 Exam Prep runs this site and fulfils every order on it, so the people who read the form are the same people who pack the books and open course access. The Florida catalog runs from free AI tutor demos to all-inclusive packages at {money(max(p["hi"] for p in products))}, across {len(products)} products. Because the team sees every package, it can compare a book set with a rental or an online course for your exact license and test date. For questions about the law itself, such as whether a job needs a license, the <a href="{DBPR_CILB}" rel="noopener" target="_blank">Florida DBPR</a> has the final word.</p></section>
{faq_html(CONTACT_FAQ)}
{sources_html([SRC_CORE[0], SRC_CORE[1], ("DBPR electrical examinations", DBPR_ELEC)])}
</div>{rail_popular("Popular Florida licenses")}</div></main>
{footer()}"""
    write(path, head(title, desc, path, [crumbs(crumb), page_ld, faq_ld(CONTACT_FAQ)]) + body)


def reviews_page():
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "tools")); import reviewskit as rk
    c = rk.content(BRAND, "Florida contractor exam", PHONE, PHONE_TEL, EMAIL)
    path = rk.PATH
    crumb = [("Home", "/"), ("Reviews", path)]
    secs = "".join(f'<section class="sec"><h2 id="{i}">{h}</h2>{b}</section>\n' for i, h, b in c["sections"])
    body = f"""{header()}<main id="main">
<section class="phero"><div class="wrap">{crumb_html(crumb)}<div class="eyebrow">Reviews</div><h1>{c["h1"]}</h1><p class="lead">{c["lead"]}</p></div></section>
<div class="wrap cols"><div class="main-col">
{takeaways(c["takeaways"])}
{secs}{faq_html(c["faq"])}
{sources_html(c["sources"])}
</div>{rail_popular("Popular Florida licenses")}</div></main>
{footer()}"""
    write(path, head(c["title"], c["desc"], path, [crumbs(crumb), rk.page_ld(SITE, c["title"], c["desc"], UPDATED, SITE + "/#org"), faq_ld(c["faq"])]) + body)


# ---------------------------------------------------------------- agent files
def agent_files():
    urls = ["/", "/how-to-get-licensed/", "/faq/", "/contact/", "/reviews/"] + BLOG_URLS + [cls_url(c) for c in live_classes] + [p["url"] for p in products]
    sm = "".join(f"<url><loc>{SITE}{u}</loc><lastmod>{UPDATED}</lastmod></url>" for u in urls)
    write("sitemap.xml", f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{sm}</urlset>\n')
    write("robots.txt", f"User-agent: *\nAllow: /\n\nUser-agent: GPTBot\nAllow: /\n\nUser-agent: ClaudeBot\nAllow: /\n\nUser-agent: Google-Extended\nAllow: /\n\nUser-agent: PerplexityBot\nAllow: /\n\nUser-agent: Bingbot\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n")
    lic = "\n".join(f"- [{short_name(c)} exam prep]({SITE}{cls_url(c)}): {len(listed[c])} packages from {money(low(c))}" for c in live_classes)
    txt = f"""# {BRAND}

> Exam prep for Florida contractor licenses: CILB Division I and II, ECLB electrical, BCAIB inspectors and county cards. State exams are open book at Pearson VUE after registration with Professional Testing, Inc.; 70% passes each part. Certified construction contractors also pass the 120-question Business and Finance exam. Orders are fulfilled by 1 Exam Prep. Phone {PHONE}, email {EMAIL}. Updated {UPDATED}.

## Key pages
- [Blog]({SITE}/blog/)
- [Exam path picker]({SITE}/#exam-path)
- [How to get a Florida contractor license]({SITE}/how-to-get-licensed/)
- [FAQ]({SITE}/faq/)
- [Contact]({SITE}/contact/)
- [Customer reviews]({SITE}/reviews/)
- [Business and Finance exam prep]({SITE}/business-and-finance/)

## Licenses
{lic}

## Facts
- Division I (General, Building, Residential): Business and Finance, Contract Administration, Project Management. Division II trades: trade knowledge plus Business and Finance.
- A current, active CILB licensee adding a category is exempt from Business and Finance (rule 61G4-16.0015).
- The CILB accepts NASCLA Commercial General Building scores in place of the trade exam since March 1, 2019.
- Counties license journeyman electricians and plumbers; Prov and GITS give county exams.
"""
    write("llms.txt", txt)
    write("agents.md", txt.replace(f"# {BRAND}", f"# {BRAND}: guide for agents") + "\n## How to buy\nEach product page has a Buy now link to `https://1examprep.com/cart/<variant-id>:1`, which opens Shopify checkout with that item. Exam path bundles join two items: `cart/<id>:1,<id>:1`. `/assets/finder.json` lists every license with its recommended packages.\n")


def not_found():
    write("404.html", head("Page not found | Pass Your Florida Contractor Exam", "That page moved or never existed. Find your Florida license exam prep from the home page or the exam path picker.", "/404.html", [{"@context": "https://schema.org", "@type": "WebPage", "name": "Page not found"}]).replace('content="index, follow, max-image-preview:large"', 'content="noindex"') +
          f'{header()}<main id="main"><section class="phero"><div class="wrap"><h1>That page is not here</h1><p class="lead">Start from the <a href="/#exam-path">exam path picker</a>, the <a href="/#find-your-license">list of licenses</a> or the <a href="/faq/">FAQ</a>.</p></div></section></main>{footer()}')


if __name__ == "__main__":
    MAN = ".build-manifest.json"
    if os.path.exists(MAN):
        for d in json.load(open(MAN)):
            if os.path.isdir(d):
                shutil.rmtree(d)
            elif os.path.isfile(d):
                os.remove(d)
    home(); guide(); faq_page(); contact_page(); reviews_page()
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "tools")); import blogpages
    BLOG_URLS = blogpages.build(globals())
    agent_files(); not_found(); finder_json()
    for c in live_classes:
        class_page(c)
    for p in products:
        product_page(p)
    if CFG.get("siteUrl"):
        open("CNAME", "w").write(SITE.split("//")[1] + "\n")
    open(".nojekyll", "w").close()
    gen = ["index.html", "404.html", "sitemap.xml", "robots.txt", "llms.txt", "agents.md", "how-to-get-licensed", "faq", "contact", "reviews", "blog", "assets/finder.json"] + live_classes
    json.dump(gen, open(MAN, "w"), indent=0)
    print(f"Built {len(live_classes)} license pages and {len(products)} product pages into the repo root")
