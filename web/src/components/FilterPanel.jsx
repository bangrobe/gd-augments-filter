import { useT } from '../i18n/I18nContext.jsx';

function CheckList({ options, value, onChange, getLabel }) {
  const toggle = (k) => onChange(value.includes(k) ? value.filter((x) => x !== k) : [...value, k]);
  return (
    <div className="space-y-0.5">
      {options.map((o) => {
        const k = o.k ?? o;
        const label = getLabel ? getLabel(o) : (o.v ?? o);
        return (
          <label key={k} className="flex items-center gap-2 py-0.5 text-sm cursor-pointer hover:text-grim-accent">
            <input
              type="checkbox"
              checked={value.includes(k)}
              onChange={() => toggle(k)}
              className="accent-grim-accent"
            />
            <span className="truncate">{label}</span>
          </label>
        );
      })}
    </div>
  );
}

function Section({ title, children, last = false }) {
  return (
    <div className={`pb-3 ${last ? '' : 'mb-3 border-b border-grim-border'}`}>
      <h3 className="text-[11px] uppercase tracking-wider text-grim-accent font-semibold mb-1.5">{title}</h3>
      {children}
    </div>
  );
}

export default function FilterPanel({ f, setF, opts, onClose }) {
  const { t } = useT();
  const update = (k) => (e) => setF({ ...f, [k]: e.target.value });
  const reset = () => {
    setF({ q: '', slot: [], rarity: [], exp: [], faction: [], ilvl: '', stat: '', type: [], dir: [] });
    onClose?.();
  };
  const toggleDir = (d) => setF({ ...f, dir: f.dir.includes(d) ? f.dir.filter((x) => x !== d) : [...f.dir, d] });
  return (
    <aside className="bg-grim-card border border-grim-border rounded-lg p-3.5">
      <Section title={t('group.search')}>
        <input
          className="w-full px-2.5 py-1.5 bg-zinc-950 border border-grim-border rounded-md text-sm focus:outline-none focus:border-grim-accent"
          type="text"
          placeholder={t('group.searchName')}
          value={f.q}
          onChange={update('q')}
        />
      </Section>
      <Section title={t('group.slot')}>
        <CheckList options={opts.slot} value={f.slot} onChange={(v) => setF({ ...f, slot: v })} />
      </Section>
      <Section title={t('group.rarity')}>
        <CheckList options={opts.rarity} value={f.rarity} onChange={(v) => setF({ ...f, rarity: v })} getLabel={(o) => t(`rarity.${o}`)} />
      </Section>
      <Section title={t('group.expansion')}>
        <CheckList options={opts.exp} value={f.exp} onChange={(v) => setF({ ...f, exp: v })} />
      </Section>
      <Section title={t('group.faction')}>
        <CheckList options={opts.faction} value={f.faction} onChange={(v) => setF({ ...f, faction: v })} />
      </Section>
      <Section title={t('group.dmgType')}>
        <CheckList options={opts.dmgType} value={f.type} onChange={(v) => setF({ ...f, type: v })} getLabel={(o) => t(`dmgt.${o}`)} />
      </Section>
      <Section title={t('group.dir')}>
        <div className="space-y-0.5">
          {['damage', 'resist', 'retaliation', 'pet'].map((d) => (
            <label key={d} className="flex items-center gap-2 py-0.5 text-sm cursor-pointer hover:text-grim-accent">
              <input type="checkbox" checked={f.dir.includes(d)} onChange={() => toggleDir(d)} className="accent-grim-accent" />
              <span>{t(`dir.${d}`)}</span>
            </label>
          ))}
        </div>
      </Section>
      <Section title={t('group.ilvl')}>
        <select
          value={f.ilvl}
          onChange={update('ilvl')}
          className="w-full px-2.5 py-1.5 bg-zinc-950 border border-grim-border rounded-md text-sm focus:outline-none focus:border-grim-accent"
        >
          <option value="">All</option>
          {opts.ilvl.map((o) => <option key={o} value={o}>{o}</option>)}
        </select>
      </Section>
      <Section title={t('group.stat')} last>
        <input
          className="w-full px-2.5 py-1.5 bg-zinc-950 border border-grim-border rounded-md text-sm focus:outline-none focus:border-grim-accent"
          type="text"
          placeholder={t('group.statPh')}
          value={f.stat}
          onChange={update('stat')}
        />
      </Section>
      <button
        onClick={reset}
        className="w-full mt-1 px-2.5 py-1.5 rounded-md border border-grim-border bg-zinc-950 text-sm hover:border-grim-accent transition"
      >
        {t('app.reset')}
      </button>
    </aside>
  );
}
