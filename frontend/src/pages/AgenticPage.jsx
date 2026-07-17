import React, { useState, useEffect, useRef } from 'react';
import './AgenticPage.css';

const API_URL = 'http://localhost:8000';

function useAgenticChat() {
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      sender: 'assistant',
      text: 'Hello! I am WAY Agent, the agentic AI layer for WAY Transit. How can I help you today?',
      agent: 'Supervisor'
    }
  ]);
  const [isLoading, setIsLoading] = useState(false);

  const fetchChat = async (message) => {
    const token = localStorage.getItem('token');
    const res = await fetch(`${API_URL}/agent/chat`, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ message })
    });
    if (!res.ok) throw new Error('API error');
    return res.json();
  };

  const submitMessage = async (text) => {
    const userMsg = { id: Date.now().toString(), sender: 'user', text };
    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);
    try {
      const response = await fetchChat(text);
      setMessages((prev) => [...prev, {
        id: (Date.now() + 1).toString(),
        sender: 'assistant',
        text: response.response,
        agent: response.agent
      }]);
    } catch (err) {
      setMessages((prev) => [...prev, {
        id: (Date.now() + 1).toString(),
        sender: 'assistant',
        text: 'Sorry, I encountered an error. Please try again.',
        agent: 'System'
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  return { messages, isLoading, submitMessage };
}

export default function AgenticPage() {
  const { messages, isLoading, submitMessage } = useAgenticChat();
  const [inputValue, setInputValue] = useState('');
  const scrollRef = useRef(null);

  useEffect(() => {
    const initialMsg = window.initialAgenticMessage;
    if (initialMsg) {
      window.initialAgenticMessage = null;
      submitMessage(initialMsg);
    }
  }, []);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isLoading]);

  const handleSend = (e) => {
    e.preventDefault();
    if (!inputValue.trim() || isLoading) return;
    const textToSend = inputValue;
    setInputValue('');
    submitMessage(textToSend);
  };

  return (
    <div className="agentic-page-container">
      <div className="chat-window">
        <ChatHeader />
        <MessagesArea messages={messages} isLoading={isLoading} scrollRef={scrollRef} />
        <ChatInput
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onSubmit={handleSend}
          disabled={isLoading}
        />
      </div>
    </div>
  );
}

function ChatHeader() {
  return (
    <div className="chat-header-area">
      <div className="chat-title-group">
        <h2>WAY Agentic AI</h2>
        <p className="chat-subtitle">Transit Assistant & Route Planner</p>
      </div>
    </div>
  );
}

function MessagesArea({ messages, isLoading, scrollRef }) {
  return (
    <div className="messages-list">
      {messages.map((msg) => (
        <MessageBubble key={msg.id} msg={msg} />
      ))}
      {isLoading && <TypingBubble />}
      <div ref={scrollRef} />
    </div>
  );
}

function MessageBubble({ msg }) {
  const isUser = msg.sender === 'user';
  return (
    <div className={`message-bubble ${msg.sender}`}>
      {!isUser && msg.agent && <span className="agent-tag">{msg.agent}</span>}
      <div>{msg.text}</div>
    </div>
  );
}

function TypingBubble() {
  return (
    <div className="typing-indicator">
      <span className="dot-anim" />
      <span className="dot-anim" />
      <span className="dot-anim" />
    </div>
  );
}

function ChatInput({ value, onChange, onSubmit, disabled }) {
  return (
    <div className="chat-input-area">
      <form onSubmit={onSubmit} className="chat-input-form">
        <input
          type="text"
          className="chat-text-input"
          placeholder="Ask about journeys, tickets, real-time status..."
          value={value}
          onChange={onChange}
          disabled={disabled}
        />
        <button type="submit" className="chat-submit-btn" disabled={disabled || !value.trim()}>
          ➔
        </button>
      </form>
    </div>
  );
}
