import { useEffect, useState } from "react";
import api from "../../api";
import { useI18n } from "../../i18n/I18nContext";

export default function Calificaciones() {
  const { t } = useI18n();
  const [datos, setDatos] = useState([]);
  const [cargando, setCargando] = useState(true);

  useEffect(() => {
    api.get("/alumno/calificaciones").then((res) => setDatos(res.data)).finally(() => setCargando(false));
  }, []);

  return (
    <div>
      <div className="page-header">
        <h1>{t("calificaciones_title")}</h1>
        <p>{t("calificaciones_subtitle")}</p>
      </div>

      <div className="card">
        {cargando ? (
          <p>{t("cargando")}</p>
        ) : datos.length === 0 ? (
          <p style={{ color: "var(--ink-soft)" }}>{t("sin_datos")}</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>{t("materia")}</th>
                <th>{t("periodo")}</th>
                <th>{t("calificacion")}</th>
              </tr>
            </thead>
            <tbody>
              {datos.map((d) => (
                <tr key={d.id_calificacion}>
                  <td>{d.materia}</td>
                  <td>{d.periodo || "-"}</td>
                  <td>
                    <span className={`badge ${d.calificacion >= 7 ? "badge-success" : "badge-danger"}`}>
                      {d.calificacion ?? "-"}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
