import { useState } from "react";
import api from "../api";
import { useI18n } from "../i18n/I18nContext";
import { useAuth } from "../context/AuthContext";
import AuthenticatedImage from "../components/AuthenticatedImage";

export default function Settings() {
  const { t, lang, setLang } = useI18n();
  const { perfil, actualizarPerfil } = useAuth();
  const [passwordActual, setPasswordActual] = useState("");
  const [passwordNueva, setPasswordNueva] = useState("");
  const [mensaje, setMensaje] = useState("");
  const [error, setError] = useState("");
  const [guardando, setGuardando] = useState(false);
  const [foto, setFoto] = useState(null);
  const [subiendoFoto, setSubiendoFoto] = useState(false);

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

  async function handleFoto(e) {
    e.preventDefault();
    if (!foto) return;
    const formulario = e.currentTarget;
    setMensaje(""); setError(""); setSubiendoFoto(true);
    const data = new FormData();
    data.append("foto", foto);
    try {
      const respuesta = await api.put("/auth/foto", data);
      actualizarPerfil(respuesta.data.perfil);
      setFoto(null);
      formulario.reset();
      setMensaje(t("foto_actualizada"));
    } catch (err) {
      setError(err.response?.data?.msg || "Error");
    } finally {
      setSubiendoFoto(false);
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
          <h3 style={{ marginBottom: 14 }}>{t("foto_perfil")}</h3>
          <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
            <AuthenticatedImage
              archivo={perfil?.foto}
              alt={perfil?.nombre}
              className="avatar avatar-image"
              style={{ width: 72, height: 72 }}
              fallback={<div className="avatar" style={{ width: 72, height: 72, fontSize: 24 }}>{perfil?.nombre?.charAt(0) || "?"}</div>}
            />
            <form onSubmit={handleFoto} style={{ flex: 1 }}>
              <input type="file" accept="image/jpeg,image/png,image/webp" required onChange={(e) => setFoto(e.target.files?.[0] || null)} />
              <button className="btn btn-primary" style={{ marginTop: 10 }} disabled={subiendoFoto}>{subiendoFoto ? t("cargando") : t("subir_foto")}</button>
            </form>
          </div>
        </div>

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
