import { useEffect, useState } from "react";
import api from "../../api";
import { useI18n } from "../../i18n/I18nContext";

const ESTATUS = ["presente", "ausente", "retardo", "justificado"];

export default function Asistencia() {
  const { t } = useI18n();
  const [grupos, setGrupos] = useState([]);
  const [grupoSel, setGrupoSel] = useState("");
  const [alumnos, setAlumnos] = useState([]);
  const [fecha, setFecha] = useState(new Date().toISOString().slice(0, 10));
  const [idHorario, setIdHorario] = useState("");
  const [horarios, setHorarios] = useState([]);
  const [estatusPorAlumno, setEstatusPorAlumno] = useState({});
  const [guardando, setGuardando] = useState(false);
  const [guardadoOk, setGuardadoOk] = useState(false);

  useEffect(() => {
    api.get("/profesor/grupos").then((res) => setGrupos(res.data));
  }, []);

  useEffect(() => {
    if (!grupoSel) { setAlumnos([]); setHorarios([]); setIdHorario(""); return; }
    Promise.all([
      api.get(`/profesor/grupos/${grupoSel}/alumnos`),
      api.get(`/profesor/grupos/${grupoSel}/horarios`),
    ]).then(([alumnosRes, horariosRes]) => {
      setAlumnos(alumnosRes.data);
      setHorarios(horariosRes.data);
      setIdHorario(horariosRes.data[0]?.id_horario?.toString() || "");
      const inicial = {};
      alumnosRes.data.forEach((a) => { inicial[a.id_alumno] = "presente"; });
      setEstatusPorAlumno(inicial);
    });
  }, [grupoSel]);

  async function guardarAsistencia() {
    if (!idHorario) return;
    setGuardando(true);
    setGuardadoOk(false);
    try {
      const registros = Object.entries(estatusPorAlumno).map(([id_alumno, estatus]) => ({
        id_alumno: parseInt(id_alumno), estatus,
      }));
      await api.post("/profesor/asistencia", { id_horario: parseInt(idHorario), fecha, registros });
      setGuardadoOk(true);
    } finally {
      setGuardando(false);
    }
  }

  return (
    <div>
      <div className="page-header">
        <h1>{t("asistencia_title")}</h1>
        <p>{t("asistencia_subtitle")}</p>
      </div>

      <div className="card" style={{ marginBottom: 18 }}>
        <div className="grid grid-cols-3">
          <div className="field" style={{ marginBottom: 0 }}>
            <label>{t("grupo")}</label>
            <select value={grupoSel} onChange={(e) => setGrupoSel(e.target.value)}>
              <option value="">--</option>
              {grupos.map((g) => <option key={g.id_grupo} value={g.id_grupo}>{g.grupo || `Grupo ${g.id_grupo}`}</option>)}
            </select>
          </div>
          <div className="field" style={{ marginBottom: 0 }}>
            <label>{t("horario")}</label>
            <select value={idHorario} onChange={(e) => setIdHorario(e.target.value)} disabled={!grupoSel}>
              <option value="">--</option>
              {horarios.map((horario) => (
                <option key={horario.id_horario} value={horario.id_horario}>
                  {horario.materia} (#{horario.id_horario})
                </option>
              ))}
            </select>
          </div>
          <div className="field" style={{ marginBottom: 0 }}>
            <label>{t("fecha")}</label>
            <input type="date" value={fecha} onChange={(e) => setFecha(e.target.value)} />
          </div>
        </div>
      </div>

      {alumnos.length > 0 && (
        <div className="card">
          <table>
            <thead>
              <tr>
                <th>{t("alumno")}</th>
                <th>{t("asistencia_title")}</th>
              </tr>
            </thead>
            <tbody>
              {alumnos.map((a) => (
                <tr key={a.id_alumno}>
                  <td>{a.nombre}</td>
                  <td>
                    <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                      {ESTATUS.map((s) => (
                        <button
                          key={s}
                          type="button"
                          className="btn"
                          style={{
                            padding: "6px 12px", fontSize: 12,
                            background: estatusPorAlumno[a.id_alumno] === s ? "var(--sabes-blue)" : "var(--paper)",
                            color: estatusPorAlumno[a.id_alumno] === s ? "white" : "var(--ink)",
                            border: "1px solid var(--border)",
                          }}
                          onClick={() => setEstatusPorAlumno({ ...estatusPorAlumno, [a.id_alumno]: s })}
                        >
                          {t(s)}
                        </button>
                      ))}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          <div style={{ marginTop: 16, display: "flex", alignItems: "center", gap: 12 }}>
            <button className="btn btn-primary" onClick={guardarAsistencia} disabled={guardando || !idHorario}>
              {guardando ? t("cargando") : t("guardar_asistencia")}
            </button>
            {guardadoOk && <span className="badge badge-success">{t("guardado")}</span>}
          </div>
        </div>
      )}
    </div>
  );
}
