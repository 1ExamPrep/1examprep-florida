"""Sort Florida products into license classes and package types by title.

The first rule that matches the lowercased title wins, so the order below matters:
licensing services, continuing education and code books first, then inspector and county exams,
then the electrical licenses, then the CILB trades, and Business and Finance last.
Products that match nothing land in "code-books-and-references" and build.py prints them.
"""
import re

R = re.compile


def has(*words):
    return lambda t: all(w in t for w in words)


def rx(pat):
    p = R(pat)
    return lambda t: bool(p.search(t))


INSPECT = r"(inspector|plans examiner|examiner)"
CLASS_RULES = [
    ("licensing-and-application-services", [has("application processing"), has("application service"), has("application and business filing"),
                                            has("corporation or llc"), has("(fro) application"), has("business formation"),
                                            has("exam registration")]),
    ("continuing-education", [has("continuing education"), has("pre-licensing education"), has("1 hour ceu"), has("financial responsibility and stability")]),
    ("code-books-and-references", [has("florida building code -"), rx(r"\bchapter (489|64e|455)"), has("statutes chapter"), has("energy efficient building construction")]),
    # building code administrators and inspectors (BCAIB): ICC technical exam + Florida Principles and Practice
    ("principles-and-practice", [has("principles and practice"), has("principle and practice"), has("(p&p)")]),
    ("residential-building-inspector-1b", [rx(r"\b1b\b.*" + INSPECT), rx(INSPECT + r".*\b1b\b"), rx(r"residential building inspector")]),
    ("residential-electrical-inspector-1e", [rx(r"residential electrical inspector")]),
    ("residential-plumbing-inspector-1p", [rx(r"residential plumbing inspector")]),
    ("residential-mechanical-inspector-1m", [rx(r"residential mechanical inspector")]),
    ("coastal-floodplain-inspector-1c", [has("coastal and floodplain")]),
    ("commercial-building-inspector-2b", [rx(r"commercial building inspector")]),
    ("commercial-electrical-inspector-2e", [rx(r"commercial electrical inspector")]),
    ("commercial-mechanical-inspector-2m", [rx(r"commercial mechanical inspector")]),
    ("commercial-plumbing-inspector-2p", [rx(r"commercial plumbing inspector")]),
    ("modular-building-inspector-fl", [has("modular building inspector")]),
    ("modular-plans-examiner-fp", [has("modular building plans examiner")]),
    ("building-plans-examiner-3b", [has("building plans examiner")]),
    ("electrical-plans-examiner-3e", [has("electrical plans examiner")]),
    ("mechanical-plans-examiner-3m", [has("mechanical plans examiner")]),
    ("plumbing-plans-examiner-3p", [has("plumbing plans examiner")]),
    ("roofing-inspector-fr", [has("roofing inspector")]),
    ("other-icc-certifications", [has("code enforcement"), has("permit technician"), has("zoning inspector"), has("property maintenance"),
                                  rx(r"icc .*module"), has("management module"), has("building official")]),
    # electricians and plumbers licensed by counties
    ("journeyman-electrician", [has("journeyman electric"), has("journeyman's electric")]),
    ("master-electrician", [has("master electrician"), has("master electrical")]),
    ("journeyman-and-master-plumber", [has("journeyman plumber"), has("master plumber"), has("plumbing maintenance")]),
    # county certificates of competency (GITS and Prov exams)
    ("county-exams-gits", [rx(r"^gits "), has("(county - florida)") ]),
    ("county-exams-prov", [rx(r"^prov "), has("florida prov "), has("florida counties nascla"), has("florida county (prov)"), has("(county")]),
    # electrical contractors (ECLB)
    ("nascla-residential-electrician", [has("nascla residential electric")]),
    ("electrical-business", [has("electrical business"), has("negocios eléctricos")]),
    ("alarm-system-ii", [rx(r"alarm systems? (ii|2)\b")]),
    ("alarm-system-i", [rx(r"alarm systems? (i|1)\b")]),
    ("limited-energy", [has("limited energy")]),
    ("lighting-maintenance", [has("lighting maintenance")]),
    ("residential-electrical", [has("residential electrical")]),
    ("unlimited-electrical", [has("unlimited electrical")]),
    # NASCLA commercial general building (accepted by the CILB in place of the GC trade exam)
    ("nascla-commercial-general-building", [has("nascla commercial general"), has("florida nascla general"), has("florida nascla contractors guide")]),
    # pools before residential, so "residential pool" never lands on the residential contractor page
    ("commercial-pool", [has("commercial pool")]),
    ("residential-pool", [has("residential pool")]),
    ("service-pool", [has("service pool")]),
    # Division I
    ("general-contractor", [has("general contractor"), has("general, building"), has("contratista general"), has("florida general")]),
    ("building-contractor", [has("building contractor")]),
    ("residential-contractor", [has("residential contractor")]),
    # Division II
    ("air-a", [rx(r"\bair a\b"), has('class "a" air')]),
    ("air-b", [rx(r"\bair b\b")]),
    ("mechanical", [has("mechanical")]),
    ("plumbing-contractor", [has("plumbing")]),
    ("roofing", [has("roofing")]),
    ("sheet-metal", [has("sheet metal")]),
    ("underground-utility", [has("underground utility"), has("utility line")]),
    ("solar", [has("solar")]),
    ("pollutant-storage", [has("pollutant")]),
    ("gas-line", [has("gas line")]),
    ("glass-and-glazing", [has("glass")]),
    ("gypsum", [has("gypsum")]),
    ("irrigation", [has("irrigation")]),
    ("marine-specialty", [has("marine")]),
    ("specialty-structure", [has("specialty structure"), has("structural"), has("screen enclosure")]),
    ("garage-door", [has("garage door")]),
    ("window-and-door", [has("window and door")]),
    ("plaster-and-lath", [has("plaster and lath")]),
    ("sign-specialty", [has("sign specialty")]),
    ("business-and-finance", [has("business and finance"), has("business & finance"), has("negocios y finanzas"), has("contractors manual")]),
]

# Products that are sold for more than one license also appear (as cards) on these pages.
ALSO = [
    (rx(r"air a (or|and|/) ?(air )?b\b|air a/b"), ["air-b"]),
    (rx(r"general, building (and|&) residential|gc, bc, rc|general, de edificio"), ["building-contractor", "residential-contractor"]),
]


def classify(title):
    t = title.lower().replace("–", "-").replace("’", "'")
    for slug, tests in CLASS_RULES:
        if any(f(t) for f in tests):
            return slug
    return "code-books-and-references"


def also(title, cls):
    t = title.lower()
    out = []
    for f, cs in ALSO:
        if f(t):
            out += [c for c in cs if c != cls]
    return out


# Package types: (key, label, sort order, tests)
TYPE_RULES = [
    ("demo", "Free AI tutor demo", 0, [has("free demo")]),
    ("one-package", "The 1 Package (all-inclusive)", 1, [has("the 1 package")]),
    ("ultimate", "Ultimate rental package", 2, [has("ultimate exam prep"), rx(r"\bultimate (package|combo)\b"), has("the ultimate")]),
    ("live", "Live virtual + self study", 3, [has("live virtual"), has("refresher class")]),
    ("instructor", "Study package with instructor-led course", 3, [has("instructor led")]),
    ("rental", "Book and course rental", 4, [has("rental"), has("alquiler")]),
    ("accelerator", "Books + Application Accelerator", 5, [has("application accelerator")]),
    ("ht", "Highlighted and tabbed book set", 6, [has("highlighted & tabbed"), has("highlighted and tabbed"), has("highlighted &tabbed")]),
    ("service", "Licensing service", 5, [has("application processing"), has("application service"), has("corporation or llc"), has("business formation"),
                                         has("application and business filing"), has("(fro) application")]),
    ("ce", "Continuing education course", 8, [has("continuing education"), has("pre-licensing education"), has("ceu"), has("14 hours")]),
    ("intro", "Introduction webinar", 8, [has("introduction to becoming")]),
    ("practice", "Online practice questions", 8, [has("practice questions"), has("practice exam")]),
    ("course", "Online exam prep course", 7, [has("online exam prep"), has("online course"), has("online exam course"), has("curso de preparación"), has("webinar"), has("online review"), has("--online")]),
    ("flash", "Flash cards", 8, [has("flash card")]),
    ("combo", "Study guide and code book combo", 5, [has("combo"), has("study package"), has("complete books, tabs")]),
    ("tabs", "Pre-printed tabs", 9, [has("tabs only"), has("pre-printed tabs"), has("pre printed tabs"), rx(r"\btabs\b(?!.*book)")]),
    ("books", "Exam book package", 6, [has("book package"), has("book set"), has("books package"), has("complete pass package"), has("budget friendly"),
                                       has("book pack"), has("books for")]),
    ("book", "Single book or study guide", 9, [lambda t: True]),
]


def ptype(title):
    t = title.lower().replace("–", "-")
    for key, label, order, tests in TYPE_RULES:
        if any(f(t) for f in tests):
            return key, label, order
    return "book", "Single book or study guide", 9


OTHER_STATES = ["Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado", "Connecticut", "Delaware",
                "Georgia", "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky",
                "Louisiana", "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota", "Mississippi", "Missouri", "Montana",
                "Nebraska", "Nevada", "New Hampshire", "New Jersey", "New Mexico", "New York", "North Carolina",
                "North Dakota", "Ohio", "Oklahoma", "Oregon", "Pennsylvania", "Rhode Island", "South Carolina",
                "South Dakota", "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington", "West Virginia",
                "Wisconsin", "Wyoming", "MSBOC", "PSI"]
PHONE_RX = R(r"\(?\b\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}\b")
EMAIL_RX = R(r"[\w.+-]+@[\w-]+\.[\w.]+")
HYPE = R(r"\b(comprehensive|seamless|unlock|robust|delve|navigate the|landscape|game[- ]changer|elevate)\b", re.I)


def clean_sentences(desc, title, limit=3):
    """First full sentences of a Shopify description, minus the repeated title, other states, phone numbers and hype."""
    if not desc:
        return []
    d = desc.replace("...", "").replace("…", "").strip()
    if d.lower().startswith(title.lower()):
        d = d[len(title):].strip()
    d = re.sub(r"^[A-Z0-9 \-&;,:+()\[\]'’/]{25,}?(?=[A-Z][a-z])", "", d)
    out = []
    for p in re.split(r"(?<=[.!?])\s+", d):
        p = p.strip().replace("—", ", ").replace("–", "-")
        if not p or p[-1:] not in ".!?":
            continue
        if any(re.search(r"\b%s\b" % re.escape(s), p) for s in OTHER_STATES) or PHONE_RX.search(p) or EMAIL_RX.search(p) or HYPE.search(p):
            continue
        if len(p.split()) > 40 or len(p.split()) < 6:
            continue
        if not out and re.match(r"(this|that|these|those|it|they|such|here)\b", p, re.I):
            continue  # a section may not open on a back-reference
        out.append(p)
        if len(out) >= limit:
            break
    return out
