import { useEffect, useMemo, useState } from "react";
import api from "../api";
import { useI18n } from "../i18n/I18nContext";
import { useAuth } from "../context/AuthContext";
import ListaPersonas from "../components/ListaPersonas";

export default function Academia() {
  const { t } = useI18n();
  const { usuario } = useAuth();
  const [datos, setDatos] = useState(null);
  const [filtro, setFiltro] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    api.get("/academia/resumen")
      .then(({ data }) => setDatos(data))
      .catch((err) => setError(err.response?.data?.msg || t("error_cargar_reporte")));
  }, [t]);

  const filas = useMemo(() => {
    const texto = filtro.trim().toLocaleLowerCase();
    if (!texto) return datos?.asignaciones || [];
    return (datos?.asignaciones || []).filter((fila) =>
      [fila.profesor, fila.grupo, fila.carrera, fila.materia, fila.cuatrimestre]
        .some((valor) => String(valor || "").toLocaleLowerCase().includes(texto))
    );
  }, [datos, filtro]);

  if (error) return <div className="error-box">{error}</div>;
  if (!datos) return <p>{t("cargando")}</p>;

  const totales = datos.totales;
  const esAdmin = usuario?.tipo_usuario === "admin";

  return (
    <div>
      <div className="page-header">
        <h1>{t("academia_title")}</h1>
        <p>{esAdmin ? t("academia_subtitle_admin") : t("academia_subtitle_profesor")}</p>
      </div>

      <div className="grid grid-cols-4" style={{ marginBottom: 18 }}>
        <Total label={t("profesores_title")} value={totales.profesores} />
        <Total label={t("grupo")} value={totales.grupos} />
        <Total label={t("nav_materias")} value={totales.materias} />
        <Total label={t("reporte_estudiantes")} value={totales.alumnos} />
      </div>

      <div className="card" style={{ marginBottom: 18 }}>
        <div style={{ display: "flex", gap: 14, alignItems: "center", justifyContent: "space-between", marginBottom: 14 }}>
          <h3>{t("asignaciones_academicas")}</h3>
          <input style={{ maxWidth: 320 }} value={filtro} onChange={(e) => setFiltro(e.target.value)} placeholder={t("buscar_academia")} />
        </div>
        <div style={{ overflowX: "auto" }}>
          <table>
            <thead><tr>
              {esAdmin && <th>{t("role_profesor")}</th>}
              <th>{t("grupo")}</th><th>{t("carrera")}</th><th>{t("cuatrimestre")}</th>
              <th>{t("materia")}</th><th>{t("reporte_estudiantes")}</th>
            </tr></thead>
            <tbody>{filas.map((fila) => (
              <tr key={`${fila.id_profesor}-${fila.id_grupo}-${fila.id_materia}`}>
                {esAdmin && <td>{fila.profesor}</td>}
                <td>{fila.grupo}</td><td>{fila.carrera}</td><td>{fila.cuatrimestre ?? "—"}</td>
                <td>{fila.materia}</td><td>{fila.alumnos}</td>
              </tr>
            ))}</tbody>
          </table>
          {filas.length === 0 && <p style={{ padding: 16 }}>{t("sin_datos")}</p>}
        </div>
      </div>

      {!esAdmin && <ListaPersonas titulo={t("companeros_area")} personas={datos.companeros_area || []} cargando={false} t={t} />}
    </div>
  );
}

function Total({ label, value }) {
  return <div className="card"><p style={{ color: "var(--ink-soft)", fontSize: 12 }}>{label}</p><strong style={{ display: "block", fontSize: 28, marginTop: 8 }}>{value}</strong></div>;
}
