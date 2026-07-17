import { useEffect, useState } from "react";
import api from "../../api";
import { useI18n } from "../../i18n/I18nContext";
import ListaPersonas from "../../components/ListaPersonas";

export default function Profesores() {
  const { t } = useI18n();
  const [personas, setPersonas] = useState([]);
  const [cargando, setCargando] = useState(true);

  useEffect(() => {
    api.get("/alumno/profesores").then((res) => setPersonas(res.data)).finally(() => setCargando(false));
  }, []);

  return <ListaPersonas titulo={t("profesores_title")} personas={personas} cargando={cargando} t={t} />;
}
