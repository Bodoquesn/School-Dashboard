import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useI18n } from "../i18n/I18nContext";
import logo from "../assets/logo.jpg";

export default function Login() {
  const { t, lang, setLang } = useI18n();
  const { login } = useAuth();
  const navigate = useNavigate();

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [enviando, setEnviando] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setEnviando(true);
    try {
      await login(username, password);
      navigate("/");
    } catch (err) {
      setError(t("login_error"));
    } finally {
      setEnviando(false);
    }
  }

  return (
    <div className="login-screen">
      <div className="login-hero">
        <img src={logo} alt="Universidad SABES" />
        <h1>{t("hero_title")}</h1>
        <p>{t("hero_subtitle")}</p>
      </div>

      <div className="login-form-wrap">
        <form className="login-form" onSubmit={handleSubmit}>
          <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: 18 }}>
            <div className="lang-switch">
              <button type="button" className={lang === "es" ? "active" : ""} onClick={() => setLang("es")}>ES</button>
              <button type="button" className={lang === "en" ? "active" : ""} onClick={() => setLang("en")}>EN</button>
            </div>
          </div>

          <h2>{t("login_title")}</h2>
          <p className="hint">{t("login_subtitle")}</p>

          {error && <div className="error-box">{error}</div>}

          <div className="field">
            <label>{t("username")}</label>
            <input value={username} onChange={(e) => setUsername(e.target.value)} autoFocus required />
          </div>

          <div className="field">
            <label>{t("password")}</label>
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
          </div>

          <button type="submit" className="btn btn-primary" style={{ width: "100%" }} disabled={enviando}>
            {enviando ? t("cargando") : t("login_button")}
          </button>
        </form>
      </div>
    </div>
  );
}
