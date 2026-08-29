# Grim Dawn — Augment Browser (React port)

Web app tra cứu 376 augments Grim Dawn, port từ bản Alpine.js gốc (`/index.html`).

## Stack
- **Vite 5 + React 18** (no Tailwind, no UI lib — chỉ CSS thuần) → đã chuyển sang **Tailwind v4**
- **Không backend** — fetch 1 lần `public/data/augments.json` (~625KB), filter/search bằng JS trong trình duyệt
- **i18n Anh-Việt tách biệt** — `src/i18n/en.js` + `src/i18n/vi.js`, đổi runtime qua nút `VI/EN` ở header
- **Không có ảnh** — grimtools.com không public URL ảnh trực tiếp, card dùng ô viết tắt expansion (`AoM` / `FoG` / `FoA`)

## Cấu trúc
```
web/
├── public/
│   └── data/augments.json    # export từ grimdawn_augments.db (625KB)
├── src/
│   ├── App.jsx               # main, filter logic, pagination
│   ├── main.jsx              # bootstrap
│   ├── index.css             # Tailwind v4 + theme
│   ├── components/
│   │   ├── FilterPanel.jsx
│   │   ├── AugmentCard.jsx
│   │   └── AugmentModal.jsx
│   ├── i18n/
│   │   ├── I18nContext.jsx   # Provider + useT() hook
│   │   ├── en.js
│   │   └── vi.js
│   └── lib/
│       └── humanize.js       # port humanize() build_db.py sang JS (nhãn VI runtime)
├── check.mjs                 # sanity test: data + humanizeVI
├── vite.config.js
└── package.json
```

## Scripts
- `npm run dev` — Vite dev server ở `http://127.0.0.1:5173/`
- `npm run build` — output vào `dist/` (self-contained, thả vào host tĩnh là chạy)
- `node check.mjs` — sanity test (data integrity + humanize samples)

## Rebuild data
```bash
cd /home/bangdigi/workspace/projects/grimdawn
python3 build_db.py                                       # tạo grimdawn_augments.db
python3 -c "import sqlite3,json; ..."                     # export JSON (xem script trong commit trước)
```

## Ảnh
- Hiện không có ảnh. Lý do: grimtools rewrite mọi URL `/db/images/*` thành HTML, không có CDN public.
- Nếu sau này có nguồn ảnh thật, đặt vào `public/images/<path>` rồi thêm lại field `image` vào JSON.

## i18n
- UI string: `src/i18n/{en,vi}.js`
- Stat label: EN dùng sẵn `augment_stats.label` trong DB; VI gọi `humanizeVi(key, value)` runtime
- Đổi ngôn ngữ: nút `VI/EN` ở header (lưu state qua React context, không persist localStorage — nếu cần thêm sau)
