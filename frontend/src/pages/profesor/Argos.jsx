import { useEffect, useState } from "react";
import api from "../../api";
import CameraCapture from "../../components/CameraCapture";
import { useI18n } from "../../i18n/I18nContext";

const resumenInicial = { alumnos_activos: 0, presentes_hoy: 0, ausentes_estimados: 0, eventos_hoy: 0 };

export default function Argos() {
  const { t } = useI18n();
  const [resumen, setResumen] = useState(resumenInicial);
  const [alumnos, setAlumnos] = useState([]);
  const [eventos, setEventos] = useState([]);
  const [alumnoSeleccionado, setAlumnoSeleccionado] = useState("");
  const [capturaEnrolamiento, setCapturaEnrolamiento] = useState(null);
  const [capturaReconocimiento, setCapturaReconocimiento] = useState(null);
  const [camara, setCamara] = useState("Cámara principal");
  const [tipoEvento, setTipoEvento] = useState("entrada");
  const [resultado, setResultado] = useState(null);
  const [mensaje, setMensaje] = useState("");
  const [error, setError] = useState("");
  const [procesando, setProcesando] = useState(false);

  async function cargar() {
    const [resumenRes, alumnosRes, eventosRes] = await Promise.all([
      api.get("/biometria/resumen"),
      api.get("/biometria/alumnos"),
      api.get("/biometria/eventos"),
    ]);
    setResumen(resumenRes.data);
    setAlumnos(alumnosRes.data);
    setEventos(eventosRes.data);
    setAlumnoSeleccionado((actual) => actual || alumnosRes.data[0]?.id_alumno?.toString() || "");
  }

  useEffect(() => { cargar().catch(mostrarError); }, []);

  function mostrarError(reason) {
    setError(reason?.response?.data?.msg || reason?.message || "Ocurrió un error.");
  }

  async function enrolar() {
    if (!alumnoSeleccionado || !capturaEnrolamiento) { setError(t("argos_capture_required")); return; }
    setProcesando(true); setError(""); setMensaje("");
    const form = new FormData();
    form.append("file", capturaEnrolamiento, "rostro.jpg");
    try {
      const { data } = await api.post(`/biometria/alumnos/${alumnoSeleccionado}/enrolar`, form);
      setMensaje(data.msg);
      setCapturaEnrolamiento(null);
      await cargar();
    } catch (reason) { mostrarError(reason); }
    finally { setProcesando(false); }
  }

  async function reconocer() {
    if (!capturaReconocimiento) { setError(t("argos_capture_required")); return; }
    setProcesando(true); setError(""); setMensaje(""); setResultado(null);
    const form = new FormData();
    form.append("file", capturaReconocimiento, "captura.jpg");
    form.append("camara", camara);
    form.append("tipo_evento", tipoEvento);
    try {
      const { data } = await api.post("/biometria/reconocer", form);
      setResultado(data);
      await cargar();
    } catch (reason) { mostrarError(reason); }
    finally { setProcesando(false); }
  }

  return (
    <div>
      <div className="page-header">
        <h1>ARGOS</h1>
        <p>{t("argos_subtitle")}</p>
      </div>

      <div className="grid grid-cols-3 argos-stats">
        <Stat label={t("argos_active_students")} value={resumen.alumnos_activos} />
        <Stat label={t("argos_present_today")} value={resumen.presentes_hoy} />
        <Stat label={t("argos_absent_estimate")} value={resumen.ausentes_estimados} />
        <Stat label={t("argos_events_today")} value={resumen.eventos_hoy} />
      </div>

      <div className="card argos-notice">{t("argos_academic_notice")}</div>
      {mensaje && <div className="badge badge-success" style={{ marginBottom: 14 }}>{mensaje}</div>}
      {error && <div className="error-box">{error}</div>}

      <div className="grid grid-cols-2 argos-workspace">
        <section className="card">
          <h3>{t("argos_enroll")}</h3>
          <div className="field">
            <label>{t("alumno")}</label>
            <select value={alumnoSeleccionado} onChange={(event) => setAlumnoSeleccionado(event.target.value)}>
              <option value="">--</option>
              {alumnos.map((alumno) => (
                <option key={alumno.id_alumno} value={alumno.id_alumno}>
                  {alumno.nombre}{alumno.rostro_registrado ? ` — ${t("argos_registered")}` : ""}
                </option>
              ))}
            </select>
          </div>
          <CameraCapture onCapture={(blob) => setCapturaEnrolamiento(blob)} />
          {capturaEnrolamiento && <p className="argos-ready">{t("argos_capture_ready")}</p>}
          <button className="btn btn-primary" onClick={enrolar} disabled={procesando}>{t("argos_save_face")}</button>
        </section>

        <section className="card">
          <h3>{t("argos_recognize")}</h3>
          <div className="field">
            <label>{t("argos_event")}</label>
            <select value={tipoEvento} onChange={(event) => setTipoEvento(event.target.value)}>
              <option value="entrada">{t("argos_entry")}</option>
              <option value="salida">{t("argos_exit")}</option>
            </select>
          </div>
          <CameraCapture onCapture={(blob, nombreCamara) => { setCapturaReconocimiento(blob); setCamara(nombreCamara); setResultado(null); }} />
          {capturaReconocimiento && <p className="argos-ready">{t("argos_capture_ready")}</p>}
          <button className="btn btn-primary" onClick={reconocer} disabled={procesando}>{t("argos_identify")}</button>
          {resultado && (
            <div className={`argos-result ${resultado.coincidencia ? "matched" : ""}`}>
              <h3>{resultado.coincidencia ? t("argos_match") : t("argos_no_match")}</h3>
              {resultado.alumno && <strong>{resultado.alumno}</strong>}
              {typeof resultado.confianza === "number" && <p>{t("argos_similarity")}: {(resultado.confianza * 100).toFixed(1)}%</p>}
              <p>{resultado.msg}</p>
            </div>
          )}
        </section>
      </div>

      <section className="card argos-history">
        <h3>{t("argos_history")}</h3>
        {eventos.length === 0 ? <p>{t("sin_datos")}</p> : (
          <table>
            <thead><tr><th>{t("fecha")}</th><th>{t("alumno")}</th><th>Campus</th><th>{t("argos_event")}</th><th>{t("argos_similarity")}</th></tr></thead>
            <tbody>{eventos.map((evento) => (
              <tr key={evento.id_evento}>
                <td>{new Date(evento.reconocido_en).toLocaleString()}</td><td>{evento.alumno}</td><td>{evento.campus || "—"}</td><td>{t(`argos_${evento.tipo_evento === "entrada" ? "entry" : "exit"}`)}</td><td>{(evento.confianza * 100).toFixed(1)}%</td>
              </tr>
            ))}</tbody>
          </table>
        )}
      </section>
    </div>
  );
}

function Stat({ label, value }) {
  return <div className="card"><p style={{ color: "var(--ink-soft)", fontSize: 12 }}>{label}</p><strong style={{ display: "block", fontSize: 28, marginTop: 8 }}>{value}</strong></div>;
}
