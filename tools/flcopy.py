"""Florida license copy and the facts behind it.

Facts checked November 22, 2026:
- DBPR construction examinations page: candidates register with Professional Testing, Inc. (PTI), then schedule at Pearson VUE.
- DBPR: Division I (General, Building, Residential) exams have 3 parts: Business and Finance, Contract Administration and
  Project Management. Every other CILB category has 2 parts: trade knowledge and Business and Finance.
- DBPR electrical examinations page: ECLB state certification exams come in 2 parts, technical/safety and business.
- Florida Administrative Code 61G4-16.0015 and the DBPR construction FAQ: a current, active CILB licensee who tests for a
  new category is exempt from Business and Finance.
- NASCLA participating agencies page: since March 1, 2019 the CILB accepts the NASCLA Commercial General Building exam in
  place of the Florida trade exam; Florida Business and Finance and a Florida Building Code portion are still required.
- ICC / DBPR bulletin: building code administrator and inspector candidates pass an ICC technical exam and the Florida
  Principles and Practice exam (Pearson VUE).
- Business and Finance: 120 questions, about 6.5 hours, open book, as published by Florida prep schools. Confirm in the
  current Candidate Information Booklet before changing.
Re-check these before changing any number.
"""

UPDATED = "2026-11-22"
UPDATED_TEXT = "November 22, 2026"

DBPR_CILB = "https://www2.myfloridalicense.com/construction-industry/"
DBPR_EXAMS = "https://www2.myfloridalicense.com/examination-information/construction-examinations/"
DBPR_ELEC = "https://www2.myfloridalicense.com/examination-information/electrical-examinations/"
DBPR_FAQ = "https://www2.myfloridalicense.com/construction-industry/faqs/"
FAC_BF = "https://www.law.cornell.edu/regulations/florida/Fla-Admin-Code-Ann-R-61G4-16-0015"
NASCLA_FL = "https://www.nascla.org/page/ParticipatingAgencies"
ICC_FL = "https://iccsafe.org/wp-content/uploads/DBPR_EIB.pdf"
STATUTE_489 = "https://www.flsenate.gov/Laws/Statutes/2022/489.111"
SUNBIZ = "https://dos.fl.gov/sunbiz/"

BF = ("The Florida Business and Finance exam has 120 questions over about 6.5 hours, open book, and you need 70% to pass. "
      "Every certified construction contractor takes it once; a current, active CILB licensee adding a category is exempt.")

GROUPS = [
    ("div1", "Division I: general, building and residential", "The 3 broad CILB licenses. Each takes 3 exam parts."),
    ("div2", "Division II: specialty trades", "CILB trade licenses. Each takes a trade exam plus Business and Finance."),
    ("electrical", "Electrical contractors", "ECLB licenses. Each takes a Technical and Safety exam plus a business exam."),
    ("inspectors", "Building inspectors and plans examiners", "BCAIB licenses. An ICC exam plus Florida Principles and Practice."),
    ("county", "County licenses and local trades", "Journeyman cards and county certificates of competency, tested by Prov or GITS."),
    ("business", "Business and Finance, books and licensing help", "The exam every state contractor takes, plus references and application help."),
]

# What each group has to pass, and which page sells the second exam.
PATH = {
    "div1": dict(exams=["Business and Finance", "Contract Administration", "Project Management"], partner="business-and-finance",
                 board="the Construction Industry Licensing Board (CILB)", short="CILB"),
    "div2": dict(exams=["Business and Finance", "Trade knowledge"], partner="business-and-finance",
                 board="the Construction Industry Licensing Board (CILB)", short="CILB"),
    "electrical": dict(exams=["Business", "Technical and Safety"], partner="electrical-business",
                       board="the Electrical Contractors' Licensing Board (ECLB)", short="ECLB"),
    "inspectors": dict(exams=["ICC technical exam", "Florida Principles and Practice"], partner="principles-and-practice",
                       board="the Building Code Administrators and Inspectors Board (BCAIB)", short="BCAIB"),
    "county": dict(exams=["County trade exam", "County Business and Law"], partner=None,
                   board="your county or city licensing board", short="county board"),
    "business": dict(exams=[], partner=None, board="DBPR", short="DBPR"),
}


def C(name, group, scope, who, icon, **kw):
    return dict(name=name, group=group, scope=scope, who=who, icon=icon, **kw)


CLASSES = {
    # Division I
    "general-contractor": C("General Contractor (CGC)", "div1",
        "has no limit on the type or size of building, so it covers high-rises, hospitals and every structure a building or residential contractor can do",
        "builders who want to bid any commercial or residential job in Florida", "building-construction", code="CGC"),
    "building-contractor": C("Building Contractor (CBC)", "div1",
        "covers commercial buildings and single- or multiple-family homes up to 3 stories tall",
        "commercial builders who stay at 3 stories or under", "building-construction", code="CBC"),
    "residential-contractor": C("Residential Contractor (CRC)", "div1",
        "covers one-, two- and three-family homes and their accessory buildings, up to 2 stories",
        "home builders and remodelers", "residential-builder", code="CRC"),
    "nascla-commercial-general-building": C("NASCLA Commercial General Building", "div1",
        "uses the NASCLA Accredited Examination for Commercial General Building Contractors, which the CILB has accepted in place of the Florida trade exam since March 1, 2019",
        "builders licensed in other NASCLA states, or who plan to be", "nascla-commercial-general-building", code="NASCLA"),
    # Division II
    "air-a": C("Class A Air Conditioning (Air A)", "div2", "covers air conditioning, heating and ventilation systems of any tonnage",
               "HVAC contractors who handle commercial systems", "hvac", code="Air A"),
    "air-b": C("Class B Air Conditioning (Air B)", "div2", "covers air conditioning and heating up to 25 tons of cooling and 500,000 BTU of heat",
               "residential and light commercial HVAC contractors", "residential-hvac", code="Air B"),
    "mechanical": C("Mechanical Contractor (CMC)", "div2", "covers HVAC, refrigeration, duct, process piping and other mechanical systems with no tonnage limit",
                    "commercial mechanical and HVAC firms", "mechanical", code="CMC"),
    "plumbing-contractor": C("Plumbing Contractor (CFC)", "div2", "covers plumbing, drainage, water supply and gas piping in all types of buildings",
                             "plumbing company owners and master plumbers going statewide", "plumbing-contractor", code="CFC"),
    "roofing": C("Roofing Contractor (CCC)", "div2", "covers installing, repairing and replacing roofs of every type, including Florida's high-wind requirements",
                 "roofing company owners", "residential-roofer", code="CCC"),
    "sheet-metal": C("Sheet Metal Contractor", "div2", "covers fabricating and installing sheet metal duct, flashing and architectural metal",
                     "sheet metal and duct shops", "ductwork"),
    "commercial-pool": C("Commercial Pool/Spa Contractor (CPC)", "div2", "covers public and commercial swimming pools and spas of any size",
                         "pool builders working on hotels, condos and public pools", "swimming-pools", code="CPC"),
    "residential-pool": C("Residential Pool/Spa Contractor", "div2", "covers swimming pools and spas at one-, two- and three-family homes",
                          "residential pool builders", "swimming-pools"),
    "service-pool": C("Swimming Pool/Spa Servicing Contractor", "div2", "covers repairing and servicing pools and spas, but not building new ones",
                      "pool service and repair companies", "swimming-pools"),
    "underground-utility": C("Underground Utility and Excavation (CUC)", "div2", "covers main sanitary sewer, storm, water and other underground utility lines and the excavation for them",
                             "site work and utility contractors", "underground-utilities", code="CUC"),
    "solar": C("Solar Contractor (CVC)", "div2", "covers solar energy systems, including solar water heating and photovoltaic installations",
               "solar installers who want to qualify their own company", "transmission-and-distribution-lines", code="CVC"),
    "pollutant-storage": C("Pollutant Storage Systems Specialty", "div2", "covers installing and removing underground and aboveground tanks for fuel and other pollutants",
                           "tank and fueling system contractors", "fueling-systems"),
    "gas-line": C("Gas Line Specialty", "div2", "covers natural gas and LP gas piping from the meter or tank to the appliance",
                  "gas piping contractors", "process-piping"),
    "glass-and-glazing": C("Glass and Glazing Specialty", "div2", "covers storefronts, curtain wall, windows and other glass and glazing systems",
                           "glazing contractors", "glass-and-glazing"),
    "gypsum": C("Gypsum Drywall Specialty", "div2", "covers gypsum drywall, framing for drywall and related ceiling systems",
                "drywall contractors", "lathing-plastering-stucco"),
    "irrigation": C("Irrigation Specialty", "div2", "covers lawn and landscape irrigation systems and their backflow and pump connections",
                    "irrigation and landscape contractors", "irrigation-systems"),
    "marine-specialty": C("Marine Specialty", "div2", "covers docks, seawalls, bulkheads, piles and other marine structures, with separate bulkhead, dock, pile and seawall options",
                          "marine construction firms along Florida's coasts and waterways", "marine-construction"),
    "specialty-structure": C("Specialty Structure and Structural Specialties", "div2", "covers screen enclosures, aluminum structures and the structural carpentry, concrete, masonry and steel specialties",
                             "screen enclosure, aluminum and structural trade contractors", "structural-steel"),
    "garage-door": C("Garage Door Installation Specialty", "div2", "covers installing and repairing garage doors and their openers, including wind-load ratings",
                     "garage door companies", "carpentry"),
    "window-and-door": C("Window and Door Installation Specialty", "div2", "covers installing windows and exterior doors, including impact-rated products",
                         "window and door installers", "carpentry"),
    "plaster-and-lath": C("Plaster and Lath Specialty", "div2", "covers lath, plaster and stucco systems", "stucco and plaster contractors", "lathing-plastering-stucco"),
    "sign-specialty": C("Sign Specialty", "div2", "covers erecting and installing signs that need structural review", "sign companies", "sign-erection"),
    # Electrical (ECLB)
    "unlimited-electrical": C("Unlimited Electrical Contractor (EC)", "electrical", "covers all electrical work with no limit on building type or size",
                              "electrical contractors who want to qualify a company statewide", "master-electrician-contractor", code="EC"),
    "residential-electrical": C("Residential Electrical Contractor", "electrical", "covers electrical work on one- and two-family homes and similar residential buildings",
                                "residential electricians starting their own company", "residential-electrical-contractor"),
    "alarm-system-i": C("Alarm System Contractor I", "electrical", "covers fire and burglar alarm systems, including fire alarm installation",
                        "fire and security alarm contractors", "alarm-systems"),
    "alarm-system-ii": C("Alarm System Contractor II", "electrical", "covers burglar and security alarm systems, but not fire alarms",
                         "security system installers", "alarm-systems"),
    "limited-energy": C("Limited Energy Specialty", "electrical", "covers low-voltage systems such as data, telephone, sound and other limited energy wiring",
                        "low-voltage and structured cabling firms", "communication-systems"),
    "lighting-maintenance": C("Lighting Maintenance Specialty", "electrical", "covers maintaining and repairing lighting fixtures and their ballasts and lamps",
                              "lighting service companies", "master-electrician"),
    "nascla-residential-electrician": C("NASCLA Residential Electrical", "electrical", "uses the NASCLA Accredited Examination for Residential Electrical Contractors; confirm with the ECLB that it fits your application before you book",
                                        "residential electricians who work in more than one state", "nascla-residential-electrician"),
    "electrical-business": C("Electrical Contractor Business Exam", "electrical", "is the business part of every ECLB certification, built on the Florida Contractors Manual",
                             "every ECLB applicant", "business-and-law"),
    # Inspectors and plans examiners (BCAIB)
    "principles-and-practice": C("Florida Principles and Practice (P&P)", "inspectors", "is the Florida law and administration exam every building code administrator, inspector and plans examiner passes",
                                 "every BCAIB applicant", "business-and-law"),
    "residential-building-inspector-1b": C("Residential Building Inspector (ICC 1B)", "inspectors", "covers residential building inspection under the Florida Building Code", "building department inspectors", "residential-builder"),
    "residential-electrical-inspector-1e": C("Residential Electrical Inspector (ICC 1E)", "inspectors", "covers residential electrical inspection", "electrical inspectors", "residential-electrical-contractor"),
    "residential-plumbing-inspector-1p": C("Residential Plumbing Inspector (ICC 1P)", "inspectors", "covers residential plumbing inspection", "plumbing inspectors", "residential-plumbing"),
    "residential-mechanical-inspector-1m": C("Residential Mechanical Inspector (ICC 1M)", "inspectors", "covers residential mechanical inspection", "mechanical inspectors", "residential-hvac"),
    "coastal-floodplain-inspector-1c": C("Coastal and Floodplain Inspector (ICC 1C)", "inspectors", "covers construction in coastal and flood hazard areas", "inspectors in coastal counties", "marine-construction"),
    "commercial-building-inspector-2b": C("Commercial Building Inspector (ICC 2B)", "inspectors", "covers commercial building inspection", "building inspectors moving up to commercial work", "building-construction"),
    "commercial-electrical-inspector-2e": C("Commercial Electrical Inspector (ICC 2E)", "inspectors", "covers commercial electrical inspection", "electrical inspectors", "master-electrician-contractor"),
    "commercial-mechanical-inspector-2m": C("Commercial Mechanical Inspector (ICC 2M)", "inspectors", "covers commercial mechanical inspection", "mechanical inspectors", "mechanical"),
    "commercial-plumbing-inspector-2p": C("Commercial Plumbing Inspector (ICC 2P)", "inspectors", "covers commercial plumbing inspection", "plumbing inspectors", "plumbing-contractor"),
    "building-plans-examiner-3b": C("Building Plans Examiner (ICC 3B)", "inspectors", "covers reviewing building plans for code compliance", "plan reviewers", "code-books-and-courses"),
    "electrical-plans-examiner-3e": C("Electrical Plans Examiner (ICC 3E)", "inspectors", "covers reviewing electrical plans", "electrical plan reviewers", "code-books-and-courses"),
    "mechanical-plans-examiner-3m": C("Mechanical Plans Examiner (ICC 3M)", "inspectors", "covers reviewing mechanical plans", "mechanical plan reviewers", "code-books-and-courses"),
    "plumbing-plans-examiner-3p": C("Plumbing Plans Examiner (ICC 3P)", "inspectors", "covers reviewing plumbing plans", "plumbing plan reviewers", "code-books-and-courses"),
    "modular-building-inspector-fl": C("Modular Building Inspector (ICC FL)", "inspectors", "covers inspecting factory-built modular buildings", "modular building inspectors", "building-construction"),
    "modular-plans-examiner-fp": C("Modular Plans Examiner (ICC FP)", "inspectors", "covers reviewing plans for factory-built modular buildings", "modular plan reviewers", "code-books-and-courses"),
    "roofing-inspector-fr": C("Roofing Inspector (ICC FR)", "inspectors", "covers roofing inspection under Florida's high-wind provisions", "roofing inspectors", "residential-roofer"),
    "other-icc-certifications": C("Other ICC Certifications", "inspectors", "covers code enforcement, permit technician, zoning, property maintenance, the ICC modules and the building official management course",
                                  "code enforcement and permitting staff", "code-books-and-courses"),
    # County
    "journeyman-electrician": C("Journeyman Electrician", "county", "is issued by Florida counties and cities, not the state, and is usually tested by Prov or GITS on the National Electrical Code",
                                "electricians who work under a licensed contractor", "journeyman-electrician"),
    "master-electrician": C("Master Electrician", "county", "is a county license for electricians who supervise work, tested on the National Electrical Code",
                            "electricians qualifying for a county master or contractor card", "master-electrician"),
    "journeyman-and-master-plumber": C("Journeyman and Master Plumber", "county", "is issued by counties, which test on the plumbing code through Prov or GITS",
                                       "plumbers testing for a county card", "journeyman-plumber"),
    "county-exams-gits": C("County Exams by GITS", "county", "covers the county certificates of competency that GITS tests, such as the Palm Beach, Broward and Miami-Dade contractor categories",
                           "contractors who only need a county certificate", "licensing-and-business-setup"),
    "county-exams-prov": C("County Exams by Prov and County Business and Law", "county", "covers the county contractor exams Prov gives and the county Business and Law exam built on the Florida Counties NASCLA guide",
                           "contractors testing for a county certificate", "business-and-law"),
    # Business
    "business-and-finance": C("Business and Finance", "business", "is the business exam every certified construction contractor passes, built on the Florida Contractors Manual",
                              "every CILB applicant", "business-and-law"),
    "licensing-and-application-services": C("Licensing and Application Services", "business", "covers help with the DBPR application, exam registration, endorsement, qualifying a second business and forming your company",
                                            "applicants who want the paperwork handled for them", "licensing-and-business-setup"),
    "continuing-education": C("Continuing Education", "business", "covers the 14-hour CILB renewal course and short pool and financial responsibility courses",
                              "licensed contractors renewing", "code-books-and-courses"),
    "code-books-and-references": C("Florida Code Books and References", "business", "covers the Florida Building Code volumes, Florida statutes and rule chapters that exams list as references",
                                   "candidates replacing or adding a single reference", "code-books-and-courses"),
}

POPULAR = ["general-contractor", "building-contractor", "residential-contractor", "air-a", "roofing", "plumbing-contractor",
           "unlimited-electrical", "business-and-finance"]

TYPE_HELP = {
    "demo": ("A free demo of the personal AI tutor for this exam. Try the questions before you buy a package.",
             ["Sample questions for this exam", "AI explanations of each answer", "No charge, delivered online"]),
    "one-package": ("Everything in one order: highlighted and tabbed books, the trade and Business and Finance courses, live classes, "
                    "the DBPR application service and business setup.", ["Highlighted and tabbed books", "Trade and Business and Finance courses",
                    "Live classes", "DBPR application service", "Business entity setup"]),
    "ultimate": ("Rental books that arrive highlighted and tabbed, the online course and live training, in one rental.",
                 ["Highlighted and tabbed rental books", "Online exam prep course", "Live or recorded instruction"]),
    "live": ("Live virtual classes with an instructor, plus self-study between sessions.", ["Live virtual instruction", "Self-study course access", "Practice with the approved references"]),
    "instructor": ("Study guides, the code book and an instructor-led NEC course in one package.", ["Study guides and practice exams", "Code book with tabs", "Instructor-led NEC course"]),
    "rental": ("The approved reference books on loan for the months you study, usually with the online course.", ["The listed reference books, rented", "Online course access", "Return shipping after the exam"]),
    "accelerator": ("The exam books plus the Application Accelerator, which organizes your DBPR application.", ["The listed exam books", "Application Accelerator support", "Highlighting where listed"]),
    "ht": ("Your own copy of every listed book, highlighted and tabbed so you find answers fast on an open-book exam.", ["Every listed reference book", "Exam-focused highlighting", "Permanent pre-printed tabs"]),
    "course": ("Self-paced online exam prep you can work through on a phone or laptop.", ["Online lessons by exam topic", "Practice questions with answers", "Book-navigation drills"]),
    "practice": ("Online practice questions that mirror the exam topics.", ["Timed practice tests", "Answer explanations", "Score tracking"]),
    "flash": ("Printed flash cards for the facts and formulas the exam asks most.", ["Flash cards by topic", "Pocket size for daily review", "Ships from 1 Exam Prep"]),
    "combo": ("Study guides paired with the code book, tabs or flash cards.", ["Study guide with practice exams", "Code book", "Tabs or flash cards, by version"]),
    "books": ("The reference books listed for the exam, new, in one shipment.", ["The listed exam reference books", "Shipped together", "Upgrade options at checkout"]),
    "tabs": ("Pre-printed adhesive tabs cut to the approved books.", ["Labeled tabs for each book", "Placement guide", "Sized for open-book testing"]),
    "service": ("Help preparing and filing your Florida license application or business entity.", ["Application review", "Document checklist", "Filing support"]),
    "ce": ("An online course that counts toward Florida contractor education hours.", ["Online, self-paced", "Certificate on completion", "Reported as the course describes"]),
    "intro": ("A short introduction to the license, the exams and the steps to apply.", ["The exam parts explained", "The application steps", "What to buy and when"]),
    "book": ("A single reference book or study guide.", ["One book or guide", "Practice exams where listed", "Ships from 1 Exam Prep"]),
}

STUDY = {
    "demo": "Work through the demo questions in one sitting, then note which topics felt slow. Those are the topics to buy books or a course for first.",
    "one-package": "Plan on 8 to 10 weeks. Start the DBPR application in week 1, study Business and Finance in weeks 1 to 3, then take one trade topic a week and finish with 2 timed practice runs.",
    "ultimate": "Plan on 6 to 8 weeks. Work one course module a week with the matching tabbed book open, then return the rental books after the exam.",
    "live": "Attend every live session, then spend 5 to 7 hours a week on self-study between classes. Sit the exam within 2 weeks of the last class.",
    "instructor": "Give the NEC course 2 to 3 sessions a week. Between sessions, work 1 practice exam from the study guide and look up every miss in the tabbed code book.",
    "rental": "Rentals run for a set number of months, so book the exam first and study backward from the date. Aim for 1 book a week and 2 timed practice runs.",
    "accelerator": "Send the application paperwork in week 1 so DBPR review runs while you study. Then read 1 book a week and practice finding answers in under 3 minutes.",
    "ht": "Skim every highlighted passage once, then drill lookups. On a 6.5-hour open-book exam, fast tab use matters more than memorizing.",
    "course": "Spend 30 to 60 minutes a day for 4 to 6 weeks. Keep the approved books open while you practice so the course trains your lookups.",
    "practice": "Take 1 timed set every other day for 2 weeks. Review each miss in the book and write the page number on a tab.",
    "flash": "Review 20 cards a day and set aside the ones you miss. After 2 weeks, the stack you set aside is your final review list.",
    "combo": "Read 1 study guide chapter a day, then take its practice exam with the code book open. Most candidates finish in about 4 weeks.",
    "books": "Order early, because the books are the exam. Tab each book on arrival, read each table of contents twice and practice lookups with a timer.",
    "tabs": "Set aside about 2 hours to place the tabs with the guide, then run 20 practice lookups so you learn where each tab sends you.",
    "service": "Collect your documents in week 1. DBPR has to approve the application before Pearson VUE lets you schedule, so filing early protects your test date.",
    "ce": "Finish the course before your renewal deadline and keep the certificate with your renewal records.",
    "intro": "Watch it before you buy anything else, then pick the package that matches the exam parts it describes.",
    "book": "Read the book once for structure, then use it for lookups during practice exams. Mark the pages you return to most with tabs.",
}

# Exam path step 2 choices, in the order shown, and which package types each one picks from.
PATH_CHOICES = [
    ("everything", "Everything done for me", ["one-package", "ultimate"]),
    ("books-course", "Books plus a course", ["rental", "ultimate", "live", "instructor", "accelerator"]),
    ("books", "Just the books", ["ht", "books", "combo"]),
    ("course", "Online course only", ["course", "live", "practice"]),
    ("free", "Try it free first", ["demo", "intro"]),
]
