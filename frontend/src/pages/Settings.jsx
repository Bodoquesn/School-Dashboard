import { useState } from "react";
import api from "../api";
import { useI18n } from "../i18n/I18nContext";

export default function Settings() {
  const { t, lang, setLang } = useI18n();
  const [passwordActual, setPasswordActual] = useState("");
  const [passwordNueva, setPasswordNueva] = useState("");
  const [mensaje, setMensaje] = useState("");
  const [error, setError] = useState("");
  const [guardando, setGuardando] = useState(false);

  async function cambiarIdioma(nuevo) {
    setLang(nuevo);
    await api.put("/auth/idioma", { idioma: nuevo }).catch(() => {});
  }

  async function handlePassword(e) {
    e.preventDefault();
    setMensaje(""); setError("");
    setGuardando(true);
    try {
      await api.put("/auth/password", { password_actual: passwordActual, password_nueva: passwordNueva });
      setMensaje(t("guardado"));
      setPasswordActual(""); setPasswordNueva("");
    } catch (err) {
      setError(err.response?.data?.msg || "Error");
    } finally {
      setGuardando(false);
    }
  }

  return (
    <div>
      <div className="page-header">
        <h1>{t("settings_title")}</h1>
        <p>{t("settings_subtitle")}</p>
      </div>

      <div className="grid grid-cols-2">
        <div className="card">
          <h3 style={{ marginBottom: 14 }}>{t("idioma")}</h3>
          <div className="lang-switch" style={{ width: "fit-content" }}>
            <button className={lang === "es" ? "active" : ""} onClick={() => cambiarIdioma("es")}>Español</button>
            <button className={lang === "en" ? "active" : ""} onClick={() => cambiarIdioma("en")}>English</button>
          </div>
        </div>

        <div className="card">
          <h3 style={{ marginBottom: 14 }}>{t("cambiar_password")}</h3>
          {mensaje && <div style={{ color: "var(--success)", fontSize: 13, marginBottom: 10 }}>{mensaje}</div>}
          {error && <div className="error-box">{error}</div>}
          <form onSubmit={handlePassword}>
            <div className="field">
              <label>{t("password_actual")}</label>
              <input type="password" required value={passwordActual} onChange={(e) => setPasswordActual(e.target.value)} />
            </div>
            <div className="field">
              <label>{t("password_nueva")}</label>
              <input type="password" required minLength={6} value={passwordNueva} onChange={(e) => setPasswordNueva(e.target.value)} />
            </div>
            <button className="btn btn-primary" type="submit" disabled={guardando}>{t("guardar_cambios")}</button>
          </form>
        </div>
      </div>
    </div>
  );
}
