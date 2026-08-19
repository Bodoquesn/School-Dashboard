import { useI18n } from "../i18n/I18nContext";
import { useAuth } from "../context/AuthContext";

export default function Dashboard() {
  const { t } = useI18n();
  const { usuario, perfil } = useAuth();
  const esProfesor = usuario?.tipo_usuario === "profesor";
  const esAdmin = usuario?.tipo_usuario === "admin";

  return (
    <div>
      <div className="page-header">
        <h1>{t("welcome")}, {perfil?.nombre?.split(" ")[0] || usuario?.username} 👋</h1>
        <p>{esAdmin ? t("dashboard_subtitle_admin") : esProfesor ? t("dashboard_subtitle_profesor") : t("dashboard_subtitle_alumno")}</p>
      </div>

      <div className="grid grid-cols-3">
        {esAdmin ? (
          <>
            <ResumenCard icono="🏫" titulo={t("nav_academia")} texto={t("academia_subtitle_admin")} />
            <ResumenCard icono="📈" titulo={t("nav_reportes")} texto={t("reportes_subtitle")} />
            <ResumenCard icono="📷" titulo={t("nav_argos")} texto={t("argos_subtitle")} />
          </>
        ) : esProfesor ? (
          <>
            <ResumenCard icono="📊" titulo={t("nav_calificaciones")} texto={t("profesor_calificaciones_subtitle")} />
            <ResumenCard icono="📝" titulo={t("nav_tareas")} texto={t("profesor_tareas_subtitle")} />
            <ResumenCard icono="✅" titulo={t("nav_asistencia")} texto={t("asistencia_subtitle")} />
          </>
        ) : (
          <>
            <ResumenCard icono="📊" titulo={t("nav_calificaciones")} texto={t("calificaciones_subtitle")} />
            <ResumenCard icono="📝" titulo={t("nav_tareas")} texto={t("tareas_subtitle")} />
            <ResumenCard icono="📄" titulo={t("nav_boleta")} texto={t("boleta_subtitle")} />
          </>
        )}
      </div>
    </div>
  );
}

function ResumenCard({ icono, titulo, texto }) {
  return (
    <div className="card">
      <div style={{ fontSize: 28, marginBottom: 10 }}>{icono}</div>
      <h3 style={{ fontSize: 16, marginBottom: 6 }}>{titulo}</h3>
      <p style={{ color: "var(--ink-soft)", fontSize: 13 }}>{texto}</p>
    </div>
  );
}
