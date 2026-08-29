import { createContext, useContext, useState, useCallback, useMemo } from 'react';
import en from './en.js';
import vi from './vi.js';

const DICTS = { en, vi };
const I18nCtx = createContext(null);

function format(str, vars) {
  if (!vars) return str;
  return str.replace(/\{(\w+)\}/g, (_, k) => (k in vars ? String(vars[k]) : `{${k}}`));
}

export function I18nProvider({ children }) {
  const [lang, setLang] = useState('vi');
  const t = useCallback(
    (path, vars) => {
      const parts = path.split('.');
      let v = DICTS[lang];
      for (const p of parts) v = v?.[p];
      return typeof v === 'string' ? format(v, vars) : path;
    },
    [lang]
  );
  const value = useMemo(() => ({ lang, setLang, t }), [lang, t]);
  return <I18nCtx.Provider value={value}>{children}</I18nCtx.Provider>;
}

export const useT = () => useContext(I18nCtx);
