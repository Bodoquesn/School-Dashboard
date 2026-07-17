import { useEffect, useState } from "react";
import api from "../../api";
import { useI18n } from "../../i18n/I18nContext";
import ListaPersonas from "../../components/ListaPersonas";

export default function Companeros() {
  const { t } = useI18n();
  const [personas, setPersonas] = useState([]);
  const [cargando, setCargando] = useState(true);

  useEffect(() => {
    api.get("/alumno/companeros").then((res) => setPersonas(res.data)).finally(() => setCargando(false));
  }, []);

  return <ListaPersonas titulo={t("companeros_title")} personas={personas} cargando={cargando} t={t} />;
}
