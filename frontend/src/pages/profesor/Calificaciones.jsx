import { useEffect, useState } from "react";
import api from "../../api";
import { useI18n } from "../../i18n/I18nContext";

export default function CalificacionesProfesor() {
  const { t } = useI18n();
  const [grupos, setGrupos] = useState([]);
  const [grupoSel, setGrupoSel] = useState("");
  const [alumnos, setAlumnos] = useState([]);
  const [periodo, setPeriodo] = useState("Parcial 1");
  const [valores, setValores] = useState({});
  const [guardandoId, setGuardandoId] = useState(null);

  useEffect(() => {
    api.get("/profesor/grupos").then((res) => setGrupos(res.data));
  }, []);

  useEffect(() => {
    if (!grupoSel) { setAlumnos([]); return; }
    api.get(`/profesor/grupos/${grupoSel}/alumnos`).then((res) => setAlumnos(res.data));
  }, [grupoSel]);

  async function guardar(idAlumno) {
    const calificacion = valores[idAlumno];
    if (calificacion === undefined || calificacion === "") return;
    setGuardandoId(idAlumno);
    try {
      await api.post("/profesor/calificaciones", {
        id_alumno: idAlumno,
        id_materia: null,
        periodo,
        calificacion: parseFloat(calificacion),
      });
    } finally {
      setGuardandoId(null);
    }
  }

  return (
    <div>
      <div className="page-header">
        <h1>{t("profesor_calificaciones_title")}</h1>
        <p>{t("profesor_calificaciones_subtitle")}</p>
      </div>

      <div className="card" style={{ marginBottom: 18 }}>
        <div className="grid grid-cols-2">
          <div className="field" style={{ marginBottom: 0 }}>
            <label>{t("grupo")}</label>
            <select value={grupoSel} onChange={(e) => setGrupoSel(e.target.value)}>
              <option value="">--</option>
              {grupos.map((g) => (
                <option key={g.id_grupo} value={g.id_grupo}>{g.grupo || `Grupo ${g.id_grupo}`}</option>
              ))}
            </select>
          </div>
          <div className="field" style={{ marginBottom: 0 }}>
            <label>{t("periodo")}</label>
            <input value={periodo} onChange={(e) => setPeriodo(e.target.value)} />
          </div>
        </div>
      </div>

      {alumnos.length > 0 && (
        <div className="card">
          <table>
            <thead>
              <tr>
                <th>{t("alumno")}</th>
                <th>{t("calificacion")}</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {alumnos.map((a) => (
                <tr key={a.id_alumno}>
                  <td>{a.nombre}</td>
                  <td style={{ maxWidth: 120 }}>
                    <input
                      type="number" min="0" max="10" step="0.1"
                      value={valores[a.id_alumno] ?? ""}
                      onChange={(e) => setValores({ ...valores, [a.id_alumno]: e.target.value })}
                    />
                  </td>
                  <td>
                    <button className="btn btn-primary" onClick={() => guardar(a.id_alumno)} disabled={guardandoId === a.id_alumno}>
                      {guardandoId === a.id_alumno ? t("guardado") : t("guardar")}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
