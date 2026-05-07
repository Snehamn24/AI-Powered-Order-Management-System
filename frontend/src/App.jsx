import { useState } from "react";
import axios from "axios";

function App() {
  const [message, setMessage] = useState("");
  const [reply, setReply] = useState("");

  const sendMessage = async () => {
    try {
      const res = await axios.post("http://127.0.0.1:8000/chat", {
        message: message
      });

      console.log("Backend response:", res.data);

      setReply(res.data.reply);

    } catch (err) {
      console.log(err);
      setReply("Error connecting to backend");
    }
  };

  return (
    <div style={{ padding: 20 }}>
      <h2>AI Manufacturing Chat</h2>

      <input
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        placeholder="Type your order..."
        style={{ width: "300px" }}
      />

      <button onClick={sendMessage}>Send</button>

      <p><b>AI Reply:</b> {reply}</p>
    </div>
  );
}

export default App;