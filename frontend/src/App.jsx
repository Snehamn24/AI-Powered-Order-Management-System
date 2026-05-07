import { useState, useEffect } from "react";
import axios from "axios";
import "./App.css";

function App() {
  const [message, setMessage] = useState("");
  const [chat, setChat] = useState([]);
  const [orders, setOrders] = useState([]);

  // =========================
  // SEND MESSAGE TO BACKEND
  // =========================
  const sendMessage = async () => {
    if (!message.trim()) return;

    // user message UI
    setChat((prev) => [...prev, { role: "user", text: message }]);

    try {
      const res = await axios.post("http://127.0.0.1:8000/chat", {
        message: message,
      });

      // bot response UI
      setChat((prev) => [
        ...prev,
        { role: "bot", text: res.data.reply },
      ]);

      // refresh orders after creation/update
      fetchOrders();

    } catch (err) {
      setChat((prev) => [
        ...prev,
        { role: "bot", text: err.response?.data?.reply || "❌ Server Error" },
      ]);
    }

    setMessage("");
  };

  // =========================
  // FETCH ORDERS DASHBOARD
  // =========================
  const fetchOrders = async () => {
    try {
      const res = await axios.get("http://127.0.0.1:8000/orders");
      setOrders(res.data);
    } catch (err) {
      console.log("Fetch Orders Error:", err);
    }
  };

  // =========================
  // AUTO REFRESH DASHBOARD
  // =========================
  useEffect(() => {
    fetchOrders();

    const interval = setInterval(() => {
      fetchOrders();
    }, 3000); // every 3 sec

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="container">

      {/* ================= CHAT SECTION ================= */}
      <div className="chatBox">
        <h2 style={{ color: "white" }}>AI Manufacturing Chat</h2>

        <div className="messages">
          {chat.map((c, i) => (
            <div key={i} className={c.role}>
              {c.text}
            </div>
          ))}
        </div>

        <div className="inputBox">
          <input
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Type order..."
          />
          <button onClick={sendMessage}>Send</button>
        </div>
      </div>

      {/* ================= DASHBOARD SECTION ================= */}
      <div className="dashboard">
        <h2 style={{ color: "white" }}>Orders Dashboard</h2>

        {orders.length === 0 ? (
          <p>No orders yet</p>
        ) : (
          orders.map((o) => (
            <div key={o.id} className="card">
              <p><b>ID:</b> {o.id}</p>
              <p><b>Part:</b> {o.part_name}</p>
              <p><b>Material:</b> {o.material}</p>
              <p><b>Qty:</b> {o.quantity}</p>
              <p><b>Status:</b> {o.status}</p>
            </div>
          ))
        )}
      </div>

    </div>
  );
}

export default App;