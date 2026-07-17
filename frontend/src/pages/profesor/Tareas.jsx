import { useEffect, useState } from "react";
import api from "../../api";
import { useI18n } from "../../i18n/I18nContext";

export default function TareasProfesor() {
  const { t } = useI18n();
  const [tareas, setTareas] = useState([]);
  const [grupos, setGrupos] = useState([]);
  const [mostrarForm, setMostrarForm] = useState(false);
  const [entregasVisibles, setEntregasVisibles] = useState(null);
  const [entregas, setEntregas] = useState([]);
  const [form, setForm] = useState({ titulo: "", descripcion: "", id_materia: "", id_grupo: "", fecha_entrega: "" });
  const [enviando, setEnviando] = useState(false);

  function cargarTareas() {
    api.get("/profesor/tareas").then((res) => setTareas(res.data));
  }

  useEffect(() => {
    cargarTareas();
    api.get("/profesor/grupos").then((res) => setGrupos(res.data));
  }, []);

  async function crearTarea(e) {
    e.preventDefault();
    setEnviando(true);
    const data = new FormData();
    Object.entries(form).forEach(([k, v]) => data.append(k, v));
    try {
      await api.post("/profesor/tareas", data, { headers: { "Content-Type": "multipart/form-data" } });
      setMostrarForm(false);
      setForm({ titulo: "", descripcion: "", id_materia: "", id_grupo: "", fecha_entrega: "" });
      cargarTareas();
    } finally {
      setEnviando(false);
    }
  }

  async function verEntregas(tarea) {
    setEntregasVisibles(tarea);
    const res = await api.get(`/profesor/tareas/${tarea.id_tarea}/entregas`);
    setEntregas(res.data);
  }

  async function calificar(idEntrega, calificacion, retro) {
    await api.put(`/profesor/entregas/${idEntrega}/calificar`, { calificacion: parseFloat(calificacion), retroalimentacion: retro });
    verEntregas(entregasVisibles);
  }

  return (
    <div>
      <div className="page-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end" }}>
        <div>
          <h1>{t("profesor_tareas_title")}</h1>
          <p>{t("profesor_tareas_subtitle")}</p>
        </div>
        <button className="btn btn-accent" onClick={() => setMostrarForm(true)}>{t("nueva_tarea")}</button>
      </div>

      <div className="grid grid-cols-2">
        {tareas.map((tarea) => (
          <div key={tarea.id_tarea} className="card">
            <h3 style={{ fontSize: 16 }}>{tarea.titulo}</h3>
            <p style={{ color: "var(--ink-soft)", fontSize: 13, margin: "8px 0" }}>{tarea.descripcion}</p>
            <p style={{ fontSize: 12, color: "var(--ink-soft)" }}>
              {t("fecha_entrega")}: {new Date(tarea.fecha_entrega).toLocaleString()}
            </p>
            <button className="btn btn-outline" style={{ marginTop: 12 }} onClick={() => verEntregas(tarea)}>
              {t("ver_entregas")}
            </button>
          </div>
        ))}
      </div>

      {mostrarForm && (
        <div style={overlayStyle}>
          <form className="card" style={{ width: 460 }} onSubmit={crearTarea}>
            <h3 style={{ marginBottom: 14 }}>{t("nueva_tarea")}</h3>
            <div className="field">
              <label>{t("titulo")}</label>
              <input required value={form.titulo} onChange={(e) => setForm({ ...form, titulo: e.target.value })} />
            </div>
            <div className="field">
              <label>{t("descripcion")}</label>
              <textarea rows={3} value={form.descripcion} onChange={(e) => setForm({ ...form, descripcion: e.target.value })} />
            </div>
            <div className="grid grid-cols-2">
              <div className="field">
                <label>{t("grupo")}</label>
                <select required value={form.id_grupo} onChange={(e) => setForm({ ...form, id_grupo: e.target.value })}>
                  <option value="">--</option>
                  {grupos.map((g) => <option key={g.id_grupo} value={g.id_grupo}>{g.grupo || `Grupo ${g.id_grupo}`}</option>)}
                </select>
              </div>
              <div className="field">
                <label>{t("nav_materias") /* id_materia numérico */}</label>
                <input required type="number" value={form.id_materia} onChange={(e) => setForm({ ...form, id_materia: e.target.value })} />
              </div>
            </div>
            <div className="field">
              <label>{t("fecha_entrega")}</label>
              <input required type="datetime-local" value={form.fecha_entrega} onChange={(e) => setForm({ ...form, fecha_entrega: e.target.value })} />
            </div>
            <div style={{ display: "flex", gap: 10, justifyContent: "flex-end" }}>
              <button type="button" className="btn btn-outline" onClick={() => setMostrarForm(false)}>Cancel</button>
              <button type="submit" className="btn btn-primary" disabled={enviando}>{t("guardar")}</button>
            </div>
          </form>
        </div>
      )}

      {entregasVisibles && (
        <div style={overlayStyle}>
          <div className="card" style={{ width: 560, maxHeight: "80vh", overflowY: "auto" }}>
            <h3 style={{ marginBottom: 14 }}>{entregasVisibles.titulo}</h3>
            {entregas.length === 0 ? (
              <p style={{ color: "var(--ink-soft)" }}>{t("sin_datos")}</p>
            ) : (
              entregas.map((e) => <FilaEntrega key={e.id_entrega} entrega={e} onCalificar={calificar} t={t} />)
            )}
            <div style={{ textAlign: "right", marginTop: 14 }}>
              <button className="btn btn-outline" onClick={() => setEntregasVisibles(null)}>Cerrar</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function FilaEntrega({ entrega, onCalificar, t }) {
  const [cal, setCal] = useState(entrega.calificacion ?? "");
  const [retro, setRetro] = useState(entrega.retroalimentacion ?? "");

  return (
    <div style={{ borderBottom: "1px solid var(--border)", padding: "12px 0" }}>
      <p style={{ fontWeight: 600, fontSize: 14 }}>{entrega.alumno}</p>
      <p style={{ fontSize: 12, color: "var(--ink-soft)" }}>{entrega.comentario}</p>
      <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
        <input type="number" min="0" max="10" step="0.1" style={{ width: 90 }} value={cal} onChange={(e) => setCal(e.target.value)} />
        <input placeholder={t("retroalimentacion")} value={retro} onChange={(e) => setRetro(e.target.value)} />
        <button className="btn btn-primary" onClick={() => onCalificar(entrega.id_entrega, cal, retro)}>{t("calificar")}</button>
      </div>
    </div>
  );
}

const overlayStyle = {
  position: "fixed", inset: 0, background: "rgba(10,15,35,0.45)",
  display: "flex", alignItems: "center", justifyContent: "center", zIndex: 50,
};
