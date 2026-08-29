import { useT } from '../i18n/I18nContext.jsx';
import { humanizeVi } from '../lib/humanize.js';

const MAX_PREVIEW_STATS = 4;

function effLabel(e, t) {
  const [type, dir] = e.split(':');
  return `${t(`dmgt.${type}`)} ${t(`dirShort.${dir}`) || ''}`;
}
function effClass(e) {
  const d = e.split(':')[1];
  if (d === 'damage') return 'text-grim-r border-[color:var(--color-grim-r)]';
  if (d === 'resist') return 'text-grim-s border-[color:var(--color-grim-s)]';
  return 'text-grim-f border-[color:var(--color-grim-f)]';
}

// Card body background tint by expansion (priority: FoA > AoM > FoG > base)
function cardTint(expStr) {
  if (!expStr) return 'bg-grim-card border-grim-border';
  const exps = expStr.split(',');
  if (exps.includes('gdx3')) return 'bg-[color:var(--color-foa-bg)] border-[color:var(--color-foa-border)]';
  if (exps.includes('gdx1')) return 'bg-[color:var(--color-aom-bg)] border-[color:var(--color-aom-border)]';
  if (exps.includes('gdx2')) return 'bg-[color:var(--color-fog-bg)] border-[color:var(--color-fog-border)]';
  return 'bg-grim-card border-grim-border';
}

// Placeholder box style by rarity (Grim Dawn in-game colors)
function rarityBox(rarity) {
  switch (rarity) {
    case 'Magical':
      return {
        bg: 'bg-[color:var(--color-rarity-magical-bg)] border-[color:var(--color-rarity-magical-border)]',
        fg: 'text-[color:var(--color-rarity-magical-fg)]',
      };
    case 'Rare':
      return {
        bg: 'bg-[color:var(--color-rarity-rare-bg)] border-[color:var(--color-rarity-rare-border)]',
        fg: 'text-[color:var(--color-rarity-rare-fg)]',
      };
    case 'Epic':
      return {
        bg: 'bg-[color:var(--color-rarity-epic-bg)] border-[color:var(--color-rarity-epic-border)]',
        fg: 'text-[color:var(--color-rarity-epic-fg)]',
      };
    case 'Legendary':
      return {
        bg: 'bg-[color:var(--color-rarity-legendary-bg)] border-[color:var(--color-rarity-legendary-border)]',
        fg: 'text-[color:var(--color-rarity-legendary-fg)]',
      };
    default:
      return { bg: 'bg-zinc-950 border-grim-border', fg: 'text-grim-muted' };
  }
}

export default function AugmentCard({ a, onClick }) {
  const { t, lang } = useT();
  const expNames = (a.expansion_names || '').split(',').filter(Boolean);
  const allStats = a.stats || [];
  const hidden = allStats.length - MAX_PREVIEW_STATS;
  const statPreview = allStats.slice(0, MAX_PREVIEW_STATS).map((s) =>
    lang === 'en' ? s.label : humanizeVi(s.key, s.value)
  );
  const box = rarityBox(a.rarity);
  return (
    <div
      onClick={onClick}
      className={`group relative border rounded-lg p-3 cursor-pointer flex gap-3 items-start transition hover:border-grim-accent hover:-translate-y-0.5 ${cardTint(a.expansions)}`}
    >
      <div
        className={`flex-none w-14 h-14 border rounded-md flex flex-col items-center justify-center text-center leading-none p-1 ${box.bg}`}
        title={t('card.reqLevel', { n: a.item_level })}
      >
        <span className={`text-[8px] uppercase tracking-wider font-semibold ${box.fg} opacity-70`}>
          {t('card.lvlShort')}
        </span>
        <span className={`text-xl font-bold ${box.fg}`}>{a.item_level}</span>
      </div>
      <div className="flex-1 min-w-0">
        <div className="font-semibold text-[15px] mb-0.5 break-words">{a.name || a.id}</div>
        <div className="flex flex-wrap gap-1 mb-1.5">
          <span className={`text-[11px] px-1.5 py-0.5 rounded-full bg-zinc-950 border ${box.fg}`}>{a.rarity}</span>
          <span className="text-[11px] px-1.5 py-0.5 rounded-full bg-zinc-950 border border-grim-border text-grim-s border-[color:var(--color-grim-s)]">{a.slot_group}</span>
          {expNames.map((e) => (
            <span key={e} className="text-[11px] px-1.5 py-0.5 rounded-full bg-zinc-950 border border-grim-border text-grim-f border-[color:var(--color-grim-f)]">{e}</span>
          ))}
        </div>
        <div className="flex flex-wrap gap-1 mb-1.5">
          {(a.effects || []).slice(0, 5).map((e) => (
            <span key={e} className={`text-[11px] px-1.5 py-0.5 rounded-full bg-zinc-950 border ${effClass(e)}`}>{effLabel(e, t)}</span>
          ))}
        </div>
        <div className="text-xs text-grim-muted max-h-12 overflow-hidden leading-snug">
          {statPreview.map((s, i) => <div key={i}>{s}</div>)}
        </div>
      </div>
      {hidden > 0 && (
        <div
          className="absolute top-1.5 right-1.5 inline-flex items-center gap-0.5 text-[10px] text-grim-accent bg-zinc-950/80 border border-grim-border rounded-full px-1.5 py-0.5"
          title={t('card.moreStats', { n: hidden })}
        >
          <span>+{hidden}</span>
          <span aria-hidden="true">⤢</span>
        </div>
      )}
    </div>
  );
}
