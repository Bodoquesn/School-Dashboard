import { useEffect, useState } from "react";
import api from "../../api";
import { useI18n } from "../../i18n/I18nContext";

export default function Materias() {
  const { t } = useI18n();
  const [materias, setMaterias] = useState([]);
  const [cargando, setCargando] = useState(true);

  useEffect(() => {
    api.get("/alumno/materias").then((res) => setMaterias(res.data)).finally(() => setCargando(false));
  }, []);

  return (
    <div>
      <div className="page-header">
        <h1>{t("materias_title")}</h1>
      </div>

      {cargando ? (
        <p>{t("cargando")}</p>
      ) : (
        <div className="grid grid-cols-4">
          {materias.map((m) => (
            <div key={m.id_materias} className="card" style={{ textAlign: "center" }}>
              <div style={{
                width: 56, height: 56, margin: "0 auto 10px", borderRadius: 14,
                background: "var(--sabes-blue)", color: "white", display: "flex",
                alignItems: "center", justifyContent: "center", fontSize: 22, fontWeight: 700,
              }}>
                {m.nombre?.charAt(0)}
              </div>
              <p style={{ fontSize: 13, fontWeight: 600 }}>{m.nombre}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
