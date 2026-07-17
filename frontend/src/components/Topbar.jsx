import { useI18n } from "../i18n/I18nContext";
import { useAuth } from "../context/AuthContext";
import api from "../api";

export default function Topbar() {
  const { t, lang, setLang } = useI18n();
  const { usuario, perfil } = useAuth();

  async function cambiarIdioma(nuevo) {
    setLang(nuevo);
    try {
      await api.put("/auth/idioma", { idioma: nuevo });
    } catch (e) {
      // si falla la sincronización con el backend, el idioma local ya cambió
    }
  }

  const nombre = perfil?.nombre || usuario?.username || "";
  const inicial = nombre.charAt(0).toUpperCase();
  const rol = usuario?.tipo_usuario === "profesor" ? t("role_profesor") : t("role_alumno");

  return (
    <header className="topbar">
      <div className="topbar-title">{t("app_name")}</div>

      <div className="topbar-right">
        <div className="lang-switch">
          <button className={lang === "es" ? "active" : ""} onClick={() => cambiarIdioma("es")}>ES</button>
          <button className={lang === "en" ? "active" : ""} onClick={() => cambiarIdioma("en")}>EN</button>
        </div>

        <div className="user-chip">
          <div className="avatar">{inicial || "?"}</div>
          <div>
            <div style={{ fontSize: 13, fontWeight: 600 }}>{nombre}</div>
            <div style={{ fontSize: 11, color: "var(--ink-soft)" }}>{rol}</div>
          </div>
        </div>
      </div>
    </header>
  );
}
