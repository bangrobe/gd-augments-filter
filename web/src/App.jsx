import { useEffect, useMemo, useState } from 'react';
import { useT } from './i18n/I18nContext.jsx';
import FilterPanel from './components/FilterPanel.jsx';
import AugmentCard from './components/AugmentCard.jsx';
import AugmentModal from './components/AugmentModal.jsx';

const PAGE_SIZE = 60;
// Faction ID → display name. Single source of truth in build_db.py: FACTION.
// Kept in sync with grimtools l10n_en.js tagFactionUser<N> / tagFactionSurvivors.
const FACTION_NAME = {
  f1: "The Black Legion", f2: "Rovers", f3: "The Outcast", f4: "Homestead",
  f5: "Kymon's Chosen", f6: "Order of Death's Vigil", f7: "Devil's Crossing",
  f8: "Coven of Ugdenbog", f9: "Barrowholm", f10: "Malmouth Resistance",
  f11: "Cult of Bysmiel", f12: "Cult of Dreeg", f13: "Cult of Solael",
  f14: "Shrine of the Dread", f15: "Kurn",
};
const DMG_TYPES = ['Physical', 'Fire', 'Cold', 'Lightning', 'Poison', 'Aether', 'Chaos', 'Pierce', 'Vitality', 'Elemental', 'Bleeding'];
const DEFAULT_FILTER = { q: '', slot: [], rarity: [], exp: [], faction: [], ilvl: '', stat: '', type: [], dir: [] };

export default function App() {
  const { t, lang, setLang } = useT();
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [f, setF] = useState(DEFAULT_FILTER);
  const [page, setPage] = useState(1);
  const [sel, setSel] = useState(null);
  const [showFilters, setShowFilters] = useState(false);

  useEffect(() => {
    fetch('./data/augments.json')
      .then((r) => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); })
      .then(setData)
      .catch((e) => setErr(e.message || String(e)));
  }, []);

  const opts = useMemo(() => {
    if (!data) return null;
    const all = data.augments;
    const uniqSplit = (k) => [...new Set(all.map((a) => a[k]).filter(Boolean).flatMap((v) => String(v).split(',')))];
    const slot = uniqSplit('slot_group').sort();
    const exp = ['base', 'gdx1', 'gdx2', 'gdx3']
      .map((k) => ({ k, v: t(`expansionName.${k}`) }))
      .filter((e) => e.k === 'base'
        ? all.some((a) => !a.expansions)
        : all.some((a) => (a.expansions || '').split(',').includes(e.k)));
    const faction = uniqSplit('factions').map((k) => ({ k, v: FACTION_NAME[k] || k })).sort((a, b) => a.v.localeCompare(b.v));
    const ilvl = [...new Set(all.map((a) => a.item_level))].sort((a, b) => a - b);
    return { slot, rarity: ['Magical', 'Rare', 'Epic', 'Legendary'], exp, faction, ilvl, dmgType: DMG_TYPES };
  }, [data, t]);

  const filtered = useMemo(() => {
    if (!data) return [];
    const q = f.q.toLowerCase();
    return data.augments.filter((a) => {
      if (q && !(a.name || '').toLowerCase().includes(q) && !a.id.includes(q)) return false;
      if (f.slot.length && !(a.slot_group || '').split(',').some((s) => f.slot.includes(s))) return false;
      if (f.rarity.length && !f.rarity.includes(a.rarity)) return false;
      if (f.exp.length && !f.exp.some((e) => e === 'base' ? !a.expansions : (a.expansions || '').split(',').includes(e))) return false;
      if (f.faction.length && !(a.factions || '').split(',').some((x) => f.faction.includes(x))) return false;
      if (f.ilvl && Number(a.item_level) !== Number(f.ilvl)) return false;
      if (f.stat && !(a.raw || '').includes(f.stat)) return false;
      if (f.type.length || f.dir.length) {
        const eff = a.effects || [];
        if (f.type.length && f.dir.length) {
          if (!eff.some((e) => { const [t1, d1] = e.split(':'); return f.type.includes(t1) && f.dir.includes(d1); })) return false;
        } else if (f.type.length) {
          if (!eff.some((e) => f.type.includes(e.split(':')[0]))) return false;
        } else if (!eff.some((e) => f.dir.includes(e.split(':')[1]))) return false;
      }
      return true;
    });
  }, [data, f]);

  useEffect(() => { setPage(1); }, [f]);
  const shown = filtered.slice(0, page * PAGE_SIZE);

  if (err) return <div className="p-16 text-center text-grim-muted">{t('app.dbError', { msg: err })}</div>;
  if (!data || !opts) return <div className="p-16 text-center text-grim-muted">{t('app.loading')}</div>;

  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-grim-border bg-zinc-950/95 sticky top-0 z-30 backdrop-blur">
        <div className="max-w-[1400px] mx-auto px-4 md:px-5 py-3 flex items-center gap-3 flex-wrap">
          <div className="flex-1 min-w-[200px]">
            <h1 className="text-base md:text-lg font-semibold leading-tight">{t('app.title')}</h1>
            <div className="text-[11px] md:text-xs text-grim-muted leading-snug mt-0.5">
              {t('app.subtitle', { count: data.count, version: data.game_version })}
            </div>
          </div>
          <button
            className="md:hidden px-3 py-1.5 rounded-md border border-grim-border bg-grim-card text-sm"
            onClick={() => setShowFilters((s) => !s)}
          >
            {showFilters ? '✕' : '☰ Filter'}
          </button>
          <button
            className="px-3 py-1.5 rounded-md border border-grim-border bg-grim-card font-semibold hover:border-grim-accent transition"
            onClick={() => setLang(lang === 'vi' ? 'en' : 'vi')}
            title={t('app.switchLang')}
          >
            {t('app.lang')}
          </button>
        </div>
      </header>

      <div className="max-w-[1400px] mx-auto px-4 md:px-5 py-4 flex gap-4 w-full flex-1 items-start">
        {/* Sidebar: mobile drawer / desktop sticky */}
        <div className={`${showFilters ? 'block' : 'hidden'} md:block w-full md:w-64 md:flex-none md:self-start md:sticky md:top-20 md:max-h-[calc(100vh-5.5rem)] md:overflow-y-auto`}>
          <FilterPanel f={f} setF={setF} opts={opts} onClose={() => setShowFilters(false)} />
        </div>

        <main className="flex-1 min-w-0">
          <div className="text-xs text-grim-muted mb-3">
            {t('app.matches', { count: filtered.length })}
            {shown.length < filtered.length && ` (${t('app.pageOf', { shown: shown.length, total: filtered.length })})`}
          </div>
          <div className="grid gap-3 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {shown.map((a) => (
              <AugmentCard key={a.id} a={a} onClick={() => setSel(a)} />
            ))}
          </div>
          {filtered.length === 0 && <div className="py-10 text-center text-grim-muted">{t('app.noResults')}</div>}
          {shown.length < filtered.length && (
            <div className="mt-4 text-center">
              <button
                className="px-4 py-1.5 rounded-md border border-grim-border bg-grim-card hover:border-grim-accent transition text-sm"
                onClick={() => setPage((p) => p + 1)}
              >
                {t('app.loadMore')}
              </button>
            </div>
          )}
        </main>
      </div>

      {sel && <AugmentModal a={sel} onClose={() => setSel(null)} />}

      <footer className="border-t border-grim-border bg-zinc-950/95 mt-8">
        <div className="max-w-[1400px] mx-auto px-4 md:px-5 py-4">
          <p className="text-[11px] text-grim-muted leading-relaxed text-center max-w-3xl mx-auto">
            {t('footer.disclaimer')}
          </p>
        </div>
      </footer>
    </div>
  );
}
