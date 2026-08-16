import AuthenticatedImage from "./AuthenticatedImage";

export default function ListaPersonas({ titulo, personas, cargando, t }) {
  return (
    <div>
      <div className="page-header">
        <h1>{titulo}</h1>
      </div>

      {cargando ? (
        <p>{t("cargando")}</p>
      ) : personas.length === 0 ? (
        <p style={{ color: "var(--ink-soft)" }}>{t("sin_datos")}</p>
      ) : (
        <div className="grid grid-cols-3">
          {personas.map((p) => {
            const id = p.id_profesor ?? p.id_alumno;
            const inicial = p.nombre?.charAt(0)?.toUpperCase();
            return (
              <div key={id} className="card" style={{ display: "flex", gap: 14, alignItems: "center" }}>
                <AuthenticatedImage
                  archivo={p.foto}
                  alt={p.nombre}
                  className="avatar avatar-image"
                  style={{ width: 46, height: 46, fontSize: 17 }}
                  fallback={<div className="avatar" style={{ width: 46, height: 46, fontSize: 17 }}>{inicial}</div>}
                />
                <div>
                  <p style={{ fontWeight: 600, fontSize: 14 }}>{p.nombre}</p>
                  <p style={{ fontSize: 12, color: "var(--ink-soft)" }}>{p.email}</p>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
