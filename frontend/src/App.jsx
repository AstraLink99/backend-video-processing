import { useState, useEffect } from "react";
import axios from "axios";

const API_BASE_URL = "http://127.0.0.1:8000"; // FastAPI Backend
const WS_URL = "ws://127.0.0.1:8000/ws/test_client"; // WebSocket URL

function App() {
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState("Waiting...");
  const [metadata, setMetadata] = useState(null);

  // Handle file selection
  const handleFileChange = (event) => {
    setFile(event.target.files[0]);
  };

  // Upload file to FastAPI
  const handleUpload = async () => {
    if (!file) {
      alert("Please select a file first!");
      return;
    }
    setStatus("Uploading...");
    
    const formData = new FormData();
    formData.append("file", file);

    try {
      await axios.post(`${API_BASE_URL}/upload`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setStatus("Upload successful! Processing...");
    } catch (error) {
      console.error("Upload error:", error);
      setStatus("Upload failed.");
    }
  };

  // WebSocket Connection
  useEffect(() => {
    const ws = new WebSocket(WS_URL);

    ws.onopen = () => {
      console.log("Connected to WebSocket!");
      setStatus("Connected! Waiting for updates...");
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log("Received:", data);

      if (data.status === "enhancement_done") {
        setStatus(`Video Enhanced: ${data.filename}`);
      } else if (data.status === "metadata_done") {
        setMetadata(data.metadata);
        setStatus(`Metadata Extracted for ${data.filename}`);
      }
    };

    ws.onclose = () => {
      console.log("WebSocket disconnected.");
      setStatus("Disconnected.");
    };

    return () => ws.close();
  }, []);

  return (
    <div style={{ textAlign: "center", marginTop: "50px" }}>
      <h2>Video Upload & Processing</h2>
      
      <input type="file" onChange={handleFileChange} />
      <button onClick={handleUpload} style={{ marginLeft: "10px" }}>Upload</button>
      
      <h3>Status: {status}</h3>

      {metadata && (
        <div>
          <h4>Metadata:</h4>
          <p>Filename: {metadata.filename}</p>
          <p>Duration: {metadata.duration} sec</p>
          <p>Resolution: {metadata.resolution}</p>
          <p>Codec: {metadata.codec}</p>
        </div>
      )}
    </div>
  );
}

export default App;
