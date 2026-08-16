import { useEffect, useState } from "react";
import api from "../api";

export default function AuthenticatedImage({ archivo, alt = "", className, style, fallback }) {
  const [src, setSrc] = useState(null);

  useEffect(() => {
    let activa = true;
    let objectUrl = null;
    if (!archivo) {
      setSrc(null);
      return () => { activa = false; };
    }

    api.get(`/archivos/${encodeURI(archivo)}`, { responseType: "blob" })
      .then(({ data }) => {
        if (!activa) return;
        objectUrl = URL.createObjectURL(data);
        setSrc(objectUrl);
      })
      .catch(() => activa && setSrc(null));

    return () => {
      activa = false;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [archivo]);

  if (!src) return fallback ?? null;
  return <img src={src} alt={alt} className={className} style={style} />;
}
