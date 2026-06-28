import React, { useState } from 'react';

export default function LoginPage({ onLoginSuccess }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [mode, setMode] = useState('login'); // 'login' or 'signup'
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const API_URL = 'http://localhost:8000';

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const endpoint = mode === 'login' ? '/user/login' : '/user/signup';
      
      let fetchOptions = {
        method: 'POST',
      };
      
      if (mode === 'login') {
        const formData = new URLSearchParams();
        formData.append('username', email);
        formData.append('password', password);
        fetchOptions.headers = { 'Content-Type': 'application/x-www-form-urlencoded' };
        fetchOptions.body = formData.toString();
      } else {
        fetchOptions.headers = { 'Content-Type': 'application/json' };
        fetchOptions.body = JSON.stringify({ email, password });
      }

      const response = await fetch(`${API_URL}${endpoint}`, fetchOptions);

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to authenticate');
      }

      if (mode === 'login') {
        onLoginSuccess(data.access_token);
      } else {
        // After signup, auto login
        setMode('login');
        setPassword('');
        alert('Signup successful! Now login.');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h2>{mode === 'login' ? 'Login' : 'Sign Up'}</h2>
        
        {error && <div className="error">{error}</div>}
        
        <form onSubmit={handleSubmit}>
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          <button type="submit" disabled={loading}>
            {loading ? 'Loading...' : (mode === 'login' ? 'Login' : 'Sign Up')}
          </button>
        </form>

        <p>
          {mode === 'login' ? "Don't have account? " : 'Already have account? '}
          <button
            type="button"
            onClick={() => {
              setMode(mode === 'login' ? 'signup' : 'login');
              setError('');
            }}
            className="link-btn"
          >
            {mode === 'login' ? 'Sign Up' : 'Login'}
          </button>
        </p>
      </div>
    </div>
  );
}
