import { createContext, useContext, useState, useCallback, useEffect } from "react";
import api from "../api";
import { useI18n } from "../i18n/I18nContext";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [usuario, setUsuario] = useState(null);
  const [perfil, setPerfil] = useState(null);
  const [cargando, setCargando] = useState(true);
  const { setLang } = useI18n();

  const cargarSesion = useCallback(async () => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      setCargando(false);
      return;
    }
    try {
      const { data } = await api.get("/auth/me");
      setUsuario(data.usuario);
      setPerfil(data.perfil);
      if (data.usuario?.idioma_preferido) setLang(data.usuario.idioma_preferido);
    } catch (e) {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
    } finally {
      setCargando(false);
    }
  }, [setLang]);

  useEffect(() => {
    cargarSesion();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const login = useCallback(async (username, password) => {
    const { data } = await api.post("/auth/login", { username, password });
    localStorage.setItem("access_token", data.access_token);
    localStorage.setItem("refresh_token", data.refresh_token);
    setUsuario(data.usuario);
    setPerfil(data.perfil);
    if (data.usuario?.idioma_preferido) setLang(data.usuario.idioma_preferido);
    return data;
  }, [setLang]);

  const logout = useCallback(() => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    setUsuario(null);
    setPerfil(null);
  }, []);

  return (
    <AuthContext.Provider value={{ usuario, perfil, cargando, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth debe usarse dentro de AuthProvider");
  return ctx;
}
