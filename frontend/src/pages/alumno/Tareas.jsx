import { useEffect, useState } from "react";
import api from "../../api";
import { useI18n } from "../../i18n/I18nContext";

function estatusBadge(tarea, t) {
  if (!tarea.mi_entrega) {
    const vencida = new Date(tarea.fecha_entrega) < new Date();
    return <span className={`badge ${vencida ? "badge-danger" : "badge-warning"}`}>{t("pendiente")}</span>;
  }
  if (tarea.mi_entrega.estatus === "calificada") return <span className="badge badge-success">{t("calificada")}</span>;
  if (tarea.mi_entrega.estatus === "atrasada") return <span className="badge badge-danger">{t("atrasada")}</span>;
  return <span className="badge badge-info">{t("entregada")}</span>;
}

export default function Tareas() {
  const { t } = useI18n();
  const [tareas, setTareas] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [activa, setActiva] = useState(null);
  const [archivo, setArchivo] = useState(null);
  const [comentario, setComentario] = useState("");
  const [enviando, setEnviando] = useState(false);

  function cargar() {
    setCargando(true);
    api.get("/alumno/tareas").then((res) => setTareas(res.data)).finally(() => setCargando(false));
  }

  useEffect(cargar, []);

  async function handleEntregar(e) {
    e.preventDefault();
    if (!activa) return;
    setEnviando(true);
    const form = new FormData();
    if (archivo) form.append("archivo", archivo);
    form.append("comentario", comentario);
    try {
      await api.post(`/alumno/tareas/${activa.id_tarea}/entregar`, form, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setActiva(null);
      setArchivo(null);
      setComentario("");
      cargar();
    } finally {
      setEnviando(false);
    }
  }

  return (
    <div>
      <div className="page-header">
        <h1>{t("tareas_title")}</h1>
        <p>{t("tareas_subtitle")}</p>
      </div>

      {cargando ? (
        <p>{t("cargando")}</p>
      ) : (
        <div className="grid grid-cols-2">
          {tareas.map((tarea) => (
            <div key={tarea.id_tarea} className="card">
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                <h3 style={{ fontSize: 16 }}>{tarea.titulo}</h3>
                {estatusBadge(tarea, t)}
              </div>
              <p style={{ color: "var(--ink-soft)", fontSize: 13, margin: "8px 0" }}>{tarea.descripcion}</p>
              <p style={{ fontSize: 12, color: "var(--ink-soft)" }}>
                {t("fecha_entrega")}: {new Date(tarea.fecha_entrega).toLocaleString()}
              </p>
              {!tarea.mi_entrega && (
                <button className="btn btn-accent" style={{ marginTop: 12 }} onClick={() => setActiva(tarea)}>
                  {t("entregar")}
                </button>
              )}
              {tarea.mi_entrega?.calificacion != null && (
                <p style={{ marginTop: 10, fontSize: 13 }}>
                  <strong>{t("calificacion")}:</strong> {tarea.mi_entrega.calificacion}
                </p>
              )}
            </div>
          ))}
        </div>
      )}

      {activa && (
        <div style={overlayStyle}>
          <form className="card" style={{ width: 420 }} onSubmit={handleEntregar}>
            <h3 style={{ marginBottom: 14 }}>{activa.titulo}</h3>
            <div className="field">
              <label>{t("subir_archivo")}</label>
              <input type="file" onChange={(e) => setArchivo(e.target.files[0])} />
            </div>
            <div className="field">
              <label>{t("comentario_opcional")}</label>
              <textarea rows={3} value={comentario} onChange={(e) => setComentario(e.target.value)} />
            </div>
            <div style={{ display: "flex", gap: 10, justifyContent: "flex-end" }}>
              <button type="button" className="btn btn-outline" onClick={() => setActiva(null)}>Cancel</button>
              <button type="submit" className="btn btn-primary" disabled={enviando}>{t("enviar")}</button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}

const overlayStyle = {
  position: "fixed", inset: 0, background: "rgba(10,15,35,0.45)",
  display: "flex", alignItems: "center", justifyContent: "center", zIndex: 50,
};
