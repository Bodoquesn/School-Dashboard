import { NavLink, useNavigate } from "react-router-dom";
import { useI18n } from "../i18n/I18nContext";
import { useAuth } from "../context/AuthContext";
import logo from "../assets/logo.jpg";

const linksAlumno = [
  { to: "/", key: "nav_dashboard", icon: "🏠", end: true },
  { to: "/calificaciones", key: "nav_calificaciones", icon: "📊" },
  { to: "/tareas", key: "nav_tareas", icon: "📝" },
  { to: "/boleta", key: "nav_boleta", icon: "📄" },
  { to: "/materias", key: "nav_materias", icon: "📚" },
  { to: "/profesores", key: "nav_profesores", icon: "🧑‍🏫" },
  { to: "/companeros", key: "nav_companeros", icon: "👥" },
  { to: "/reportes", key: "nav_reportes", icon: "📈" },
];

const linksProfesor = [
  { to: "/", key: "nav_dashboard", icon: "🏠", end: true },
  { to: "/academia", key: "nav_academia", icon: "🏫" },
  { to: "/calificaciones", key: "nav_calificaciones", icon: "📊" },
  { to: "/tareas", key: "nav_tareas", icon: "📝" },
  { to: "/asistencia", key: "nav_asistencia", icon: "✅" },
  { to: "/reportes", key: "nav_reportes", icon: "📈" },
  { to: "/argos", key: "nav_argos", icon: "📷" },
];

const linksAdmin = [
  { to: "/", key: "nav_dashboard", icon: "🏠", end: true },
  { to: "/academia", key: "nav_academia", icon: "🏫" },
  { to: "/reportes", key: "nav_reportes", icon: "📈" },
  { to: "/argos", key: "nav_argos", icon: "📷" },
];

export default function Sidebar() {
  const { t } = useI18n();
  const { usuario, logout } = useAuth();
  const navigate = useNavigate();
  const links = usuario?.tipo_usuario === "admin"
    ? linksAdmin
    : usuario?.tipo_usuario === "profesor" ? linksProfesor : linksAlumno;

  function handleLogout() {
    if (window.confirm(t("logout_confirm"))) {
      logout();
      navigate("/login");
    }
  }

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <img src={logo} alt="Universidad SABES" />
        <div>
          <div className="name">SABES</div>
          <div className="sub">San José Iturbide</div>
        </div>
      </div>

      <nav className="sidebar-nav">
        {links.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            end={link.end}
            className={({ isActive }) => "sidebar-link" + (isActive ? " active" : "")}
          >
            <span className="icon">{link.icon}</span>
            <span className="label">{t(link.key)}</span>
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-footer">
        <NavLink to="/configuracion" className={({ isActive }) => "sidebar-link" + (isActive ? " active" : "")}>
          <span className="icon">⚙️</span>
          <span className="label">{t("nav_settings")}</span>
        </NavLink>
        <button className="sidebar-link" onClick={handleLogout} style={{ border: "none", width: "100%", textAlign: "left", background: "transparent" }}>
          <span className="icon">🚪</span>
          <span className="label">{t("nav_logout")}</span>
        </button>
      </div>
    </aside>
  );
}
