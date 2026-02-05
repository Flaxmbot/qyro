import React, { useState, useEffect } from 'react';
import axios from 'axios';

export default function Chat() {
  const [msg, setMsg] = useState('');
  const [history, setHistory] = useState([]);

  useEffect(() => {
    const interval = setInterval(() => {
        axios.get('http://localhost:8000/messages')
            .then(res => setHistory(res.data))
            .catch(e => console.error(e));
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  const send = async () => {
    await axios.post('http://localhost:8000/send', { text: msg });
    setMsg('');
  };

  return (
    <div className="p-10">
      <h1 className="text-2xl font-bold mb-4">Qyro Chat</h1>
      <div className="border p-4 h-64 overflow-y-scroll mb-4 bg-gray-100">
        {history.map((h, i) => (
            <div key={i} className="mb-2">
                <span className="font-bold">{h.user}: </span>
                <span>{h.text}</span>
            </div>
        ))}
      </div>
      <div className="flex">
        <input
            className="border p-2 flex-grow mr-2"
            value={msg}
            onChange={e => setMsg(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && send()}
        />
        <button className="bg-blue-500 text-white p-2" onClick={send}>Send</button>
      </div>
    </div>
  );
}