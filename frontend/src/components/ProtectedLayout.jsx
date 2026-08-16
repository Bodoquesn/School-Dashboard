import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import Sidebar from "./Sidebar";
import Topbar from "./Topbar";
import { useI18n } from "../i18n/I18nContext";

export function ProtectedLayout() {
  const { usuario, cargando } = useAuth();
  const { t } = useI18n();

  if (cargando) {
    return (
      <div style={{ display: "flex", height: "100vh", alignItems: "center", justifyContent: "center" }}>
        {t("cargando")}
      </div>
    );
  }

  if (!usuario) return <Navigate to="/login" replace />;

  return (
    <div className="app-shell">
      <Sidebar />
      <Topbar />
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
}

/** Restringe una ruta a uno o varios roles ('alumno' | 'profesor' | 'admin') */
export function RoleRoute({ roles, children }) {
  const { usuario } = useAuth();
  if (!usuario) return <Navigate to="/login" replace />;
  if (!roles.includes(usuario.tipo_usuario)) return <Navigate to="/" replace />;
  return children;
}
