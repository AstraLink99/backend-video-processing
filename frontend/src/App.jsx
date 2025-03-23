import { useState, useEffect } from "react";
import axios from "axios";

const API_BASE_URL = "http://127.0.0.1:8000"; // FastAPI Backend
const WS_URL = "ws://127.0.0.1:8000/ws/test_client"; // WebSocket URL

function App() {
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState("Waiting...");
  const [metadata, setMetadata] = useState(null);
  const [processedVideo, setProcessedVideo] = useState(null);

  const handleFileChange = (event) => {
    setFile(event.target.files[0]);
  };

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

  useEffect(() => {
    const connectWebSocket = () => {
      const ws = new WebSocket(WS_URL);

      ws.onopen = () => {
        console.log("Connected to WebSocket!");
        setStatus("Connected! Waiting for updates...");
      };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log("Received from WebSocket:", data);

        if (data.status === "enhancement_done") {
          setStatus(`✅ Video Enhanced: ${data.filename}`);
          setProcessedVideo(`${API_BASE_URL}/storage/processed/enhanced_${data.filename}`);
        } else if (data.status === "metadata_done") {
          console.log("✅ Metadata received:", data.metadata);
          setMetadata(data.metadata);
          setStatus(`📊 Metadata Extracted for ${data.filename}`);
        }
      };

      ws.onerror = (error) => {
        console.error("WebSocket Error:", error);
      };

      ws.onclose = () => {
        console.log("WebSocket disconnected. Reconnecting...");
        setTimeout(connectWebSocket, 3000); // Auto-reconnect after 3 seconds
      };
    };

    connectWebSocket();
  }, []);

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-900 text-white">
      <h2 className="text-2xl font-bold mb-4">🎥 Video Upload & Processing</h2>

      <div className="bg-gray-800 p-6 rounded-lg shadow-lg w-96">
        <input
          type="file"
          onChange={handleFileChange}
          className="block w-full text-sm text-gray-300
            file:mr-4 file:py-2 file:px-4
            file:rounded-lg file:border-0
            file:text-sm file:font-semibold
            file:bg-indigo-600 file:text-white
            hover:file:bg-indigo-700"
        />
        <button
          onClick={handleUpload}
          className="mt-4 px-6 py-2 w-full bg-blue-500 hover:bg-blue-600 rounded-lg text-white font-semibold"
        >
          Upload
        </button>
      </div>

      <h3 className="mt-6 text-xl font-semibold bg-gray-800 p-3 rounded-lg shadow-md">
        {status}
      </h3>

      {metadata && (
        <div className="mt-6 p-4 bg-gray-800 rounded-lg shadow-md w-96">
          <h4 className="text-lg font-semibold mb-2">📊 Metadata:</h4>
          <p><strong>Filename:</strong> {metadata.filename}</p>
          <p><strong>Duration:</strong> {metadata.duration} sec</p>
          <p><strong>Resolution:</strong> {metadata.resolution}</p>
          <p><strong>Codec:</strong> {metadata.codec}</p>
        </div>
      )}

      {processedVideo && (
        <div className="mt-6">
          <h4 className="text-lg font-semibold">🎥 Processed Video:</h4>
          <video controls className="mt-2 w-96">
            <source src={processedVideo} type="video/mp4" />
            Your browser does not support the video tag.
          </video>
        </div>
      )}
    </div>
  );
}

export default App;
