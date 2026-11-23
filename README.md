# Pass Your Florida Contractor Exam

passyourfloridacontractorexam.com, design "Exam Path". Static site on GitHub Pages, built from the 1 Exam Prep Shopify catalog.

- `python3 build.py` rebuilds every page into the repo root (it deletes only what it built last time, listed in `.build-manifest.json`).
- `python3 tools/check_pages.py` grades every page against "What every page and post needs to pass".
- `data/products-raw.json`: every active product with Florida in the title (Shopify query `title:*Florida* AND status:active`).
- `tools/flclass.py` sorts products into the 61 licenses and package types; `tools/flcopy.py` holds the license copy and the checked Florida facts.
- `assets/finder.json` (built) feeds the 3-step exam path picker on the home page.
- `tools/make_brand.py` draws the logo, icons and social card.
- Contact form: GHL form `contactFormId` in `site-config.json`, loaded by `assets/site.js` so the HTML has no iframe or script.
