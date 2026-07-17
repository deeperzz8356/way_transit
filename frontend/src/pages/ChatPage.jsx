import { useState, useRef, useEffect } from 'react';
import axios from 'axios';

const ChatPage = () => {
  const [messages, setMessages] = parseInt(useState([]));
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage = { sender: 'user', text: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        'http://localhost:8000/agent/chat',
        { message: userMessage.text },
        {
          headers: {
            Authorization: `Bearer ${token}`
          }
        }
      );

      const agentMessage = {
        sender: 'agent',
        text: response.data.response,
        agentName: response.data.agent // RAG dynamic agent name attribution
      };
      
      setMessages((prev) => [...prev, agentMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
      setMessages((prev) => [
        ...prev,
        { sender: 'system', text: 'Error: Could not reach the WAY Transit Agent.' }
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.container}>
      <h2 style={styles.header}>WAY AI Assistant</h2>
      <div style={styles.chatBox}>
        {messages.length === 0 && (
          <p style={styles.placeholder}>Hello! I am your WAY Transit AI Assistant. Ask me anything about your bookings or transit routes!</p>
        )}
        {messages.map((msg, idx) => (
          <div
            key={idx}
            style={{
              ...styles.messageWrapper,
              justifyContent: msg.sender === 'user' ? 'flex-end' : 'flex-start'
            }}
          >
            <div
              style={{
                ...styles.messageBubble,
                backgroundColor: msg.sender === 'user' ? '#007bff' : (msg.sender === 'system' ? '#ff4d4f' : '#f1f0f0'),
                color: msg.sender === 'user' || msg.sender === 'system' ? '#fff' : '#000',
              }}
            >
              {msg.sender === 'agent' && (
                <div style={styles.agentAttribution}>
                  🤖 <strong>{msg.agentName}</strong>
                </div>
              )}
              <div>{msg.text}</div>
            </div>
          </div>
        ))}
        {loading && <div style={styles.loading}>Agent is typing...</div>}
        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSend} style={styles.inputArea}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your message..."
          style={styles.inputField}
        />
        <button type="submit" style={styles.sendButton} disabled={loading}>
          Send
        </button>
      </form>
    </div>
  );
};

const styles = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    height: '80vh',
    maxWidth: '600px',
    margin: '0 auto',
    padding: '20px',
    border: '1px solid #ccc',
    borderRadius: '10px',
    backgroundColor: '#fff',
    boxShadow: '0 4px 10px rgba(0,0,0,0.1)'
  },
  header: {
    textAlign: 'center',
    marginBottom: '20px',
    color: '#333'
  },
  chatBox: {
    flex: 1,
    overflowY: 'auto',
    padding: '10px',
    border: '1px solid #ddd',
    borderRadius: '5px',
    marginBottom: '15px',
    backgroundColor: '#fafafa',
    display: 'flex',
    flexDirection: 'column'
  },
  placeholder: {
    textAlign: 'center',
    color: '#888',
    marginTop: 'auto',
    marginBottom: 'auto'
  },
  messageWrapper: {
    display: 'flex',
    marginBottom: '10px',
    width: '100%'
  },
  messageBubble: {
    maxWidth: '75%',
    padding: '12px',
    borderRadius: '8px',
    lineHeight: '1.4',
    wordWrap: 'break-word',
    position: 'relative'
  },
  agentAttribution: {
    fontSize: '0.8em',
    marginBottom: '5px',
    paddingBottom: '5px',
    borderBottom: '1px solid #ccc',
    color: '#555'
  },
  loading: {
    fontSize: '0.9em',
    color: '#777',
    fontStyle: 'italic',
    marginBottom: '10px'
  },
  inputArea: {
    display: 'flex',
    gap: '10px'
  },
  inputField: {
    flex: 1,
    padding: '10px',
    borderRadius: '5px',
    border: '1px solid #ccc',
    fontSize: '1em'
  },
  sendButton: {
    padding: '10px 20px',
    borderRadius: '5px',
    border: 'none',
    backgroundColor: '#28a745',
    color: 'white',
    fontSize: '1em',
    cursor: 'pointer'
  }
};

export default ChatPage;
