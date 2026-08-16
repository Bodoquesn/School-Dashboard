import { useEffect, useRef, useState } from "react";

export default function CameraCapture({ onCapture }) {
  const videoRef = useRef(null);
  const streamRef = useRef(null);
  const [cameras, setCameras] = useState([]);
  const [selectedCamera, setSelectedCamera] = useState("");
  const [started, setStarted] = useState(false);
  const [error, setError] = useState("");

  function detener() {
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
    if (videoRef.current) videoRef.current.srcObject = null;
    setStarted(false);
  }

  async function cargarCamaras() {
    try {
      setError("");
      if (!navigator.mediaDevices?.getUserMedia) throw new Error("El navegador no permite acceder a cámaras.");
      const dispositivos = await navigator.mediaDevices.enumerateDevices();
      const video = dispositivos.filter((device) => device.kind === "videoinput");
      setCameras(video);
      setSelectedCamera((actual) => video.some((camera) => camera.deviceId === actual) ? actual : video[0]?.deviceId || "");
      if (!video.length) setError("No se encontraron cámaras disponibles.");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "No se pudieron detectar las cámaras.");
    }
  }

  async function abrir(deviceId = selectedCamera) {
    if (!deviceId) { setError("Selecciona una cámara."); return; }
    try {
      detener();
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { deviceId: { exact: deviceId }, width: { ideal: 1280 }, height: { ideal: 720 } },
        audio: false,
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
      setStarted(true);
      setError("");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "No se pudo abrir la cámara.");
    }
  }

  async function cambiar(deviceId) {
    setSelectedCamera(deviceId);
    if (started) await abrir(deviceId);
  }

  function capturar() {
    const video = videoRef.current;
    if (!video?.videoWidth || !video?.videoHeight) { setError("La cámara aún no está lista."); return; }
    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext("2d")?.drawImage(video, 0, 0, canvas.width, canvas.height);
    canvas.toBlob((blob) => {
      if (!blob) return;
      const camera = cameras.find((item) => item.deviceId === selectedCamera);
      onCapture(blob, camera?.label || "Cámara principal");
      setError("");
    }, "image/jpeg", 0.9);
  }

  useEffect(() => {
    cargarCamaras();
    return detener;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="argos-camera">
      <div className="field">
        <label>Cámara</label>
        <select value={selectedCamera} onChange={(event) => cambiar(event.target.value)}>
          {!cameras.length && <option value="">No hay cámaras disponibles</option>}
          {cameras.map((camera, index) => <option key={camera.deviceId} value={camera.deviceId}>{camera.label || `Cámara ${index + 1}`}</option>)}
        </select>
      </div>
      <video ref={videoRef} autoPlay playsInline muted />
      <div className="argos-actions">
        {!started ? (
          <button type="button" className="btn btn-primary" onClick={() => abrir()} disabled={!cameras.length}>Abrir cámara</button>
        ) : (
          <>
            <button type="button" className="btn btn-primary" onClick={capturar}>Capturar</button>
            <button type="button" className="btn btn-outline" onClick={detener}>Cerrar</button>
          </>
        )}
        <button type="button" className="btn btn-outline" onClick={cargarCamaras}>Actualizar cámaras</button>
      </div>
      {error && <div className="error-box">{error}</div>}
    </div>
  );
}
