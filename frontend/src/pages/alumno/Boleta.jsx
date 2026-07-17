import { useState } from "react";
import api from "../../api";
import { useI18n } from "../../i18n/I18nContext";

export default function Boleta() {
  const { t } = useI18n();
  const [descargando, setDescargando] = useState(false);

  async function descargar() {
    setDescargando(true);
    try {
      const res = await api.get("/alumno/boleta", { responseType: "blob" });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", "boleta_calificaciones.pdf");
      document.body.appendChild(link);
      link.click();
      link.remove();
    } finally {
      setDescargando(false);
    }
  }

  return (
    <div>
      <div className="page-header">
        <h1>{t("boleta_title")}</h1>
        <p>{t("boleta_subtitle")}</p>
      </div>

      <div className="card" style={{ maxWidth: 420, textAlign: "center", padding: 40 }}>
        <div style={{ fontSize: 42, marginBottom: 14 }}>📄</div>
        <button className="btn btn-primary" onClick={descargar} disabled={descargando}>
          {descargando ? t("cargando") : t("descargar_boleta")}
        </button>
      </div>
    </div>
  );
}
