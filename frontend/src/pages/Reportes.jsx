import { useEffect, useState } from "react";
import api from "../api";
import { useI18n } from "../i18n/I18nContext";
import { useAuth } from "../context/AuthContext";

export default function Reportes() {
  const { t } = useI18n();
  const { usuario } = useAuth();
  const [reporte, setReporte] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.get("/reportes/resumen")
      .then(({ data }) => setReporte(data))
      .catch((err) => setError(err.response?.data?.msg || t("error_cargar_reporte")));
  }, [t]);

  if (error) return <div className="error-box">{error}</div>;
  if (!reporte) return <p>{t("cargando")}</p>;

  const asistenciaAgrupada = usuario?.tipo_usuario !== "alumno";
  const asistencia = asistenciaAgrupada
    ? reporte.asistencia_grupo || []
    : reporte.asistencia || [];

  return (
    <div>
      <div className="page-header">
        <h1>{t("reportes_title")}</h1>
        <p>{t("reportes_subtitle")}</p>
      </div>

      <div className="grid grid-cols-3" style={{ marginBottom: 18 }}>
        {reporte.tarjetas.map((tarjeta) => (
          <div className="card" key={tarjeta.clave}>
            <p style={{ color: "var(--ink-soft)", fontSize: 12 }}>{t(`reporte_${tarjeta.clave}`)}</p>
            <strong style={{ display: "block", fontSize: 28, marginTop: 8 }}>{tarjeta.valor}</strong>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-2">
        <TablaPromedios filas={reporte.promedios_materia || []} t={t} />
        <TablaAsistencia filas={asistencia} esProfesor={asistenciaAgrupada} t={t} />
      </div>
    </div>
  );
}

function TablaPromedios({ filas, t }) {
  return (
    <div className="card">
      <h3 style={{ marginBottom: 14 }}>{t("promedio_por_materia")}</h3>
      {filas.length === 0 ? <p>{t("sin_datos")}</p> : (
        <table>
          <thead><tr><th>{t("materia")}</th><th>{t("promedio")}</th></tr></thead>
          <tbody>{filas.map((fila) => <tr key={fila.materia}><td>{fila.materia}</td><td>{fila.promedio}</td></tr>)}</tbody>
        </table>
      )}
    </div>
  );
}

function TablaAsistencia({ filas, esProfesor, t }) {
  return (
    <div className="card">
      <h3 style={{ marginBottom: 14 }}>{t("resumen_asistencia")}</h3>
      {filas.length === 0 ? <p>{t("sin_datos")}</p> : (
        <table>
          <thead><tr>{esProfesor && <th>{t("grupo")}</th>}<th>{t("estatus")}</th><th>{t("total")}</th></tr></thead>
          <tbody>{filas.map((fila, index) => (
            <tr key={`${fila.id_grupo || "alumno"}-${fila.estatus}-${index}`}>
              {esProfesor && <td>{fila.grupo}</td>}<td>{t(fila.estatus)}</td><td>{fila.total}</td>
            </tr>
          ))}</tbody>
        </table>
      )}
    </div>
  );
}
