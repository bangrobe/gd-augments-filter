import { useEffect } from 'react';
import { useT } from '../i18n/I18nContext.jsx';
import { humanizeVi } from '../lib/humanize.js';

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

export default function AugmentModal({ a, onClose }) {
  const { t, lang } = useT();
  useEffect(() => {
    const onKey = (e) => { if (e.key === 'Escape') onClose(); };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [onClose]);
  const slots = (a.slots || '').split(',').filter(Boolean);
  const stats = (a.stats || []).map((s) => (lang === 'en' ? s.label : humanizeVi(s.key, s.value)));
  return (
    <div className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-4" onClick={onClose}>
      <div
        onClick={(e) => e.stopPropagation()}
        className="bg-grim-card border border-grim-border rounded-xl w-full max-w-[640px] max-h-[90vh] overflow-hidden flex flex-col"
      >
        <div className="p-5 overflow-y-auto">
          <button onClick={onClose} aria-label={t('modal.close')} className="float-right text-grim-muted text-xl leading-none hover:text-grim-fg">×</button>
          <h2 className="text-lg font-semibold m-0 mb-1 break-words pr-8">{a.name || a.id}</h2>
          <div className="flex flex-wrap gap-1 mb-3">
            <span className="text-[11px] px-1.5 py-0.5 rounded-full bg-zinc-950 border border-grim-border text-grim-r border-[color:var(--color-grim-r)]">{a.rarity}</span>
            <span className="text-[11px] px-1.5 py-0.5 rounded-full bg-zinc-950 border border-grim-border text-grim-s border-[color:var(--color-grim-s)]">{a.slot_group}</span>
            <span className="text-[11px] px-1.5 py-0.5 rounded-full bg-zinc-950 border border-grim-border text-grim-muted">iLvl {a.item_level}</span>
            {a.expansion_names && <span className="text-[11px] px-1.5 py-0.5 rounded-full bg-zinc-950 border border-grim-border text-grim-f border-[color:var(--color-grim-f)]">{a.expansion_names}</span>}
          </div>
          <p className="text-grim-muted m-0 mb-2">{a.description}</p>
          <div className="flex flex-wrap gap-1 mb-3">
            {slots.map((s) => <span key={s} className="text-[11px] px-1.5 py-0.5 rounded-full bg-zinc-950 border border-grim-border text-grim-muted">{s}</span>)}
          </div>
          <div className="text-xs text-grim-muted mb-3">
            {a.faction_names && <div>{t('modal.faction')}: <b className="text-grim-fg">{a.faction_names}</b> ({a.rep_tier_name})</div>}
            {a.untradeable ? <div className="text-grim-warm">{t('modal.untradeable')}</div> : null}
            {a.sold_by && a.sold_by.length > 0 && (
              <div className="mt-1">
                {t('modal.soldBy')}:{' '}
                <span className="text-grim-fg">
                  {a.sold_by.map((v, i) => (
                    <span key={i}>
                      {i > 0 && ', '}
                      <b>{v.name}</b>{v.location ? ` (${v.location})` : ''}
                    </span>
                  ))}
                </span>
              </div>
            )}
          </div>
          <h3 className="text-grim-accent text-xs uppercase tracking-wider font-semibold mt-3 mb-1.5">{t('modal.dmgTypeHdr')}</h3>
          <div className="flex flex-wrap gap-1 mb-3">
            {(a.effects || []).map((e) => (
              <span key={e} className={`text-[11px] px-1.5 py-0.5 rounded-full bg-zinc-950 border ${effClass(e)}`}>{effLabel(e, t)}</span>
            ))}
            {!(a.effects || []).length && <span className="text-xs text-grim-muted">{t('modal.noDmg')}</span>}
          </div>
          <h3 className="text-grim-accent text-xs uppercase tracking-wider font-semibold mt-3 mb-1.5">{t('modal.statsHdr')}</h3>
          <div className="text-sm text-grim-fg space-y-0.5">
            {stats.map((s, i) => <div key={i}>{s}</div>)}
          </div>
        </div>
      </div>
    </div>
  );
}
