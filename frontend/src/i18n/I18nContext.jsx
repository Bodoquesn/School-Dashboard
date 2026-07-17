import { createContext, useContext, useState, useCallback, useMemo } from "react";
import translations from "./translations";

const I18nContext = createContext(null);

export function I18nProvider({ children }) {
  const [lang, setLang] = useState(localStorage.getItem("idioma") || "es");

  const changeLang = useCallback((newLang) => {
    setLang(newLang);
    localStorage.setItem("idioma", newLang);
  }, []);

  const t = useCallback((key) => translations[lang]?.[key] ?? key, [lang]);

  const value = useMemo(() => ({ lang, setLang: changeLang, t }), [lang, changeLang, t]);

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n() {
  const ctx = useContext(I18nContext);
  if (!ctx) throw new Error("useI18n debe usarse dentro de I18nProvider");
  return ctx;
}
