# Grim Dawn — Augment Browser

Fan-made reference tool for browsing 376 augments in Grim Dawn.

🌐 **Live site:** https://bangrobe.github.io/gd-augments-filter/

## Repo layout
- `web/` — Vite + React 18 + Tailwind v4 source code
- `web/public/data/augments.json` — exported DB (625KB, generated from `build_db.py`)
- `.github/workflows/deploy.yml` — auto-build & deploy to GitHub Pages on push to `main`
- `build_db.py` (gitignored) — script to rebuild the SQLite DB from raw grimtools data
- `itemdb.js`, `augments_parsed.json` (gitignored) — raw scrape inputs, ~17MB total

## Local dev
```bash
cd web
npm install
npm run dev       # http://localhost:5173
npm run build     # output to web/dist/
node check.mjs    # sanity test
```

## Rebuild data
The web app reads `web/public/data/augments.json`. To regenerate:
1. Update raw data in project root (`itemdb.js`, `augments_parsed.json`)
2. Run `python3 build_db.py` → produces `grimdawn_augments.db`
3. Run the JSON export script (see `web/README.md` for the snippet)
4. `cp` the new JSON into `web/public/data/`

## Disclaimer
Grim Dawn and all related content are trademarks of Crate Entertainment.
This site is a fan-made, non-commercial reference tool. Data sourced from
[grimtools.com](https://www.grimtools.com/) and community contributions on the
[Crate Entertainment forum](https://forums.crateentertainment.com/).
Not affiliated with or endorsed by Crate Entertainment.
