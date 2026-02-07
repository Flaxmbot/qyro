import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [username, setUsername] = useState('');
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const wsRef = useRef(null);
  const messagesEndRef = useRef(null);

  // Use same host as frontend but API port (8000 maps to 8003 externally)
  const API_PORT = window.location.port === '3000' ? '8000' : '8003';
  const API_URL = `http://${window.location.hostname}:${API_PORT}`;
  const WS_URL = `ws://${window.location.hostname}:${API_PORT}/ws`;

  useEffect(() => {
    if (isLoggedIn) {
      // Connect to WebSocket for real-time updates
      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'messages') {
          setMessages(data.messages);
        } else if (data.type === 'new_message') {
          setMessages(prev => [...prev, data.message]);
        }
      };

      ws.onopen = () => {
        console.log('WebSocket connected');
        ws.send(JSON.stringify({ type: 'get_messages' }));
      };

      ws.onerror = (err) => {
        console.error('WebSocket error, falling back to polling:', err);
        // Fallback to polling if WebSocket fails
        const interval = setInterval(() => {
          axios.get(`${API_URL}/messages`)
            .then(res => setMessages(res.data.messages || []))
            .catch(console.error);
        }, 5000); // 5s polling as fallback
        return () => clearInterval(interval);
      };

      return () => ws.close();
    }
  }, [isLoggedIn]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const login = () => {
    if (username.trim()) setIsLoggedIn(true);
  };

  const sendMessage = async () => {
    if (!input.trim()) return;
    
    // Send via WebSocket if connected
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'send_message',
        username,
        content: input
      }));
    } else {
      // Fallback to REST
      await axios.post(`${API_URL}/send`, { username, content: input });
    }
    setInput('');
  };

  if (!isLoggedIn) {
    return (
      <div style={{
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #030014 0%, #0f0a1e 50%, #1a1433 100%)',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        fontFamily: "'Inter', sans-serif"
      }}>
        <div style={{
          background: 'rgba(99, 102, 241, 0.1)',
          backdropFilter: 'blur(20px)',
          padding: '50px',
          borderRadius: '24px',
          border: '1px solid rgba(99, 102, 241, 0.3)',
          textAlign: 'center',
          boxShadow: '0 0 60px rgba(99, 102, 241, 0.2)'
        }}>
          <h1 style={{
            background: 'linear-gradient(135deg, #6366f1, #06b6d4)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            fontSize: '2.5rem',
            marginBottom: '30px'
          }}>🌀 Qyro Chat</h1>
          <input
            type="text"
            placeholder="Enter your username"
            value={username}
            onChange={e => setUsername(e.target.value)}
            onKeyPress={e => e.key === 'Enter' && login()}
            style={{
              padding: '16px 24px',
              borderRadius: '14px',
              border: '1px solid rgba(99, 102, 241, 0.3)',
              background: 'rgba(255,255,255,0.05)',
              color: '#fff',
              fontSize: '16px',
              width: '280px',
              marginBottom: '20px',
              outline: 'none'
            }}
          />
          <br />
          <button
            onClick={login}
            style={{
              padding: '16px 50px',
              borderRadius: '14px',
              border: 'none',
              background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
              color: '#fff',
              fontSize: '16px',
              fontWeight: '600',
              cursor: 'pointer',
              boxShadow: '0 4px 20px rgba(99, 102, 241, 0.4)'
            }}
          >
            Join Chat
          </button>
        </div>
      </div>
    );
  }

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #030014 0%, #0f0a1e 50%, #1a1433 100%)',
      padding: '30px',
      fontFamily: "'Inter', sans-serif"
    }}>
      <div style={{ maxWidth: '700px', margin: '0 auto' }}>
        <h1 style={{
          background: 'linear-gradient(135deg, #6366f1, #06b6d4)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          textAlign: 'center',
          marginBottom: '5px'
        }}>🌀 Qyro Chat</h1>
        <p style={{ color: '#9d9aaf', textAlign: 'center', marginBottom: '20px' }}>
          Welcome, <span style={{ color: '#06b6d4' }}>{username}</span>!
        </p>
        
        <div style={{
          background: 'rgba(15, 10, 30, 0.6)',
          backdropFilter: 'blur(20px)',
          borderRadius: '20px',
          border: '1px solid rgba(99, 102, 241, 0.2)',
          padding: '20px',
          minHeight: '450px',
          maxHeight: '450px',
          overflowY: 'auto',
          marginBottom: '20px'
        }}>
          {messages.length === 0 && (
            <p style={{ color: '#666', textAlign: 'center', marginTop: '180px' }}>
              No messages yet. Start the conversation!
            </p>
          )}
          {messages.map((msg, i) => (
            <div key={i} style={{
              display: 'flex',
              justifyContent: msg.username === username ? 'flex-end' : 'flex-start',
              marginBottom: '12px'
            }}>
              <div style={{
                padding: '12px 18px',
                borderRadius: '16px',
                background: msg.username === username 
                  ? 'linear-gradient(135deg, #6366f1, #8b5cf6)'
                  : 'rgba(255,255,255,0.08)',
                color: '#fff',
                maxWidth: '70%',
                boxShadow: msg.username === username 
                  ? '0 4px 15px rgba(99, 102, 241, 0.3)' 
                  : 'none'
              }}>
                {msg.username !== username && (
                  <div style={{ fontSize: '0.75rem', color: '#06b6d4', marginBottom: '4px' }}>
                    {msg.username}
                  </div>
                )}
                {msg.content}
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        <div style={{ display: 'flex', gap: '12px' }}>
          <input
            type="text"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyPress={e => e.key === 'Enter' && sendMessage()}
            placeholder="Type a message..."
            style={{
              flex: 1,
              padding: '16px 24px',
              borderRadius: '14px',
              border: '1px solid rgba(99, 102, 241, 0.2)',
              background: 'rgba(255,255,255,0.05)',
              color: '#fff',
              fontSize: '16px',
              outline: 'none'
            }}
          />
          <button
            onClick={sendMessage}
            style={{
              padding: '16px 35px',
              borderRadius: '14px',
              border: 'none',
              background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
              color: '#fff',
              fontWeight: '600',
              cursor: 'pointer',
              boxShadow: '0 4px 15px rgba(99, 102, 241, 0.3)'
            }}
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}

export default App;