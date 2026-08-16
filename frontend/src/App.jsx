import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import { I18nProvider } from "./i18n/I18nContext";
import { ProtectedLayout, RoleRoute } from "./components/ProtectedLayout";
import { useAuth } from "./context/AuthContext";

import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Settings from "./pages/Settings";
import Reportes from "./pages/Reportes";

import CalificacionesAlumno from "./pages/alumno/Calificaciones";
import TareasAlumno from "./pages/alumno/Tareas";
import Boleta from "./pages/alumno/Boleta";
import Materias from "./pages/alumno/Materias";
import Profesores from "./pages/alumno/Profesores";
import Companeros from "./pages/alumno/Companeros";

import CalificacionesProfesor from "./pages/profesor/Calificaciones";
import TareasProfesor from "./pages/profesor/Tareas";
import Asistencia from "./pages/profesor/Asistencia";
import Argos from "./pages/profesor/Argos";

export default function App() {
  return (
    <I18nProvider>
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            <Route path="/login" element={<Login />} />

            <Route element={<ProtectedLayout />}>
              <Route path="/" element={<Dashboard />} />
              <Route path="/configuracion" element={<Settings />} />
              <Route path="/reportes" element={<Reportes />} />

              {/* Calificaciones y Tareas cambian de componente según el rol */}
              <Route
                path="/calificaciones"
                element={
                  <RoleAware alumno={<CalificacionesAlumno />} profesor={<CalificacionesProfesor />} />
                }
              />
              <Route
                path="/tareas"
                element={<RoleAware alumno={<TareasAlumno />} profesor={<TareasProfesor />} />}
              />

              {/* Solo alumno */}
              <Route path="/boleta" element={<RoleRoute roles={["alumno"]}><Boleta /></RoleRoute>} />
              <Route path="/materias" element={<RoleRoute roles={["alumno"]}><Materias /></RoleRoute>} />
              <Route path="/profesores" element={<RoleRoute roles={["alumno"]}><Profesores /></RoleRoute>} />
              <Route path="/companeros" element={<RoleRoute roles={["alumno"]}><Companeros /></RoleRoute>} />

              {/* Solo profesor */}
              <Route path="/asistencia" element={<RoleRoute roles={["profesor"]}><Asistencia /></RoleRoute>} />
              <Route path="/argos" element={<RoleRoute roles={["profesor", "admin"]}><Argos /></RoleRoute>} />
            </Route>
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </I18nProvider>
  );
}

function RoleAware({ alumno, profesor }) {
  const { usuario } = useAuth();
  if (usuario?.tipo_usuario === "profesor") return profesor;
  return alumno;
}
