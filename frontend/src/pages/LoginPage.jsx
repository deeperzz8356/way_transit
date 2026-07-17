import React, { useState, useEffect } from 'react';
import './LoginPage.css';

export default function LoginPage({ onLoginSuccess }) {
  const [step, setStep] = useState('splash');
  
  // State for the various form steps
  const [phone, setPhone] = useState('');
  const [otp, setOtp] = useState(['', '', '', '', '', '']);
  const [profile, setProfile] = useState({ name: '', age: '', gender: '', profession: '' });
  
  const allPreferences = [
    'Solo Traveller', 'Group Traveller', 'Adventure', 'Explorer', 
    'Metro', 'Walking', 'Bus', 'Train', 'Fastest Route', 
    'Shortest Route', 'Carpool', 'Multimodal', 'Single Trips', 
    'Budget Trips', 'Comfort Trips'
  ];
  const [selectedPrefs, setSelectedPrefs] = useState([]);

  useEffect(() => {
    if (step === 'splash') {
      const timer = setTimeout(() => {
        setStep('start');
      }, 2000);
      return () => clearTimeout(timer);
    }
  }, [step]);

  const handleOtpChange = (index, value) => {
    if (value.length > 1) return; // Only 1 digit per box
    const newOtp = [...otp];
    newOtp[index] = value;
    setOtp(newOtp);
    // Auto-focus next input (simple logic for now)
    if (value && index < 5) {
      const nextInput = document.getElementById(`otp-${index + 1}`);
      if (nextInput) nextInput.focus();
    }
  };

  const togglePref = (pref) => {
    setSelectedPrefs(prev => 
      prev.includes(pref) ? prev.filter(p => p !== pref) : [...prev, pref]
    );
  };

  const renderStep = () => {
    switch (step) {
      case 'splash':
        return (
          <div className="step-splash">
            <h1 className="way-logo">WAY</h1>
          </div>
        );

      case 'start':
        return (
          <div className="step-start slide-up">
            <div className="illustration-box">
               <img src="/login_screen_image.png" alt="Illustration" className="start-img" />
            </div>
            <h1 className="step-title">Get started</h1>
            <p className="step-subtitle">Designed for seamless journeys ahead.<br/>Begin the way you prefer.</p>
            
            <div className="social-buttons">
              <button className="btn-primary" onClick={() => setStep('phone')}>
                Continue with Phone
              </button>
              <button className="btn-secondary" onClick={() => setStep('phone')}>
                Continue with Gmail
              </button>
              <div className="icon-buttons">
                <button className="btn-icon"></button>
                <button className="btn-icon">G</button>
              </div>
            </div>

            <div className="auth-links">
              <a href="#" onClick={(e) => { e.preventDefault(); setStep('phone'); }}>Already a user? Sign in</a>
              <a href="#" onClick={(e) => { e.preventDefault(); onLoginSuccess('mock-token'); }}>Skip Sign in</a>
            </div>
          </div>
        );

      case 'phone':
        return (
          <div className="step-phone slide-up">
            <h1 className="step-title">Secure Your Account</h1>
            
            <div className="input-group">
              <label>Add Your Phone no.</label>
              <div className="phone-input-row">
                <select className="country-code">
                  <option>+91</option>
                  <option>+1</option>
                </select>
                <input 
                  type="tel" 
                  value={phone} 
                  onChange={(e) => setPhone(e.target.value)} 
                  className="full-input" 
                  placeholder="000 000 0000"
                />
              </div>
            </div>

            <div className="input-group">
              <label>Enter Otp</label>
              <div className="otp-grid">
                {otp.map((digit, i) => (
                  <input
                    key={i}
                    id={`otp-${i}`}
                    type="text"
                    inputMode="numeric"
                    className="otp-box"
                    value={digit}
                    onChange={(e) => handleOtpChange(i, e.target.value)}
                  />
                ))}
              </div>
            </div>

            <button className="btn-primary mt-auto" onClick={() => setStep('profile')}>Confirm</button>
            <button className="btn-text-only" onClick={() => setStep('start')}>Continue with Google</button>
          </div>
        );

      case 'profile':
        return (
          <div className="step-profile slide-up">
            <h1 className="step-title">Create your Profile</h1>
            
            <div className="input-group">
              <label>Your Name</label>
              <input 
                type="text" 
                className="full-input" 
                value={profile.name}
                onChange={(e) => setProfile({...profile, name: e.target.value})}
              />
            </div>

            <div className="row-inputs">
              <div className="input-group half">
                <label>Age</label>
                <input 
                  type="number" 
                  className="full-input" 
                  value={profile.age}
                  onChange={(e) => setProfile({...profile, age: e.target.value})}
                />
              </div>
              <div className="input-group half">
                <label>Gender</label>
                <select 
                  className="full-input"
                  value={profile.gender}
                  onChange={(e) => setProfile({...profile, gender: e.target.value})}
                >
                  <option value="">Select</option>
                  <option value="Male">Male</option>
                  <option value="Female">Female</option>
                  <option value="Other">Other</option>
                </select>
              </div>
            </div>

            <div className="input-group">
              <label>Your Profession</label>
              <input 
                type="text" 
                className="full-input" 
                value={profile.profession}
                onChange={(e) => setProfile({...profile, profession: e.target.value})}
              />
            </div>

            <div className="input-group">
              <label>Upload concession proof (if any)</label>
              <div className="upload-row">
                <div className="upload-box">+</div>
                <div className="upload-box">+</div>
                <div className="upload-box">+</div>
              </div>
            </div>

            <button className="btn-primary mt-auto" onClick={() => setStep('preferences')}>Confirm</button>
          </div>
        );

      case 'preferences':
        return (
          <div className="step-preferences slide-up">
            <h1 className="step-title">Select Travel Preferences</h1>
            <div className="pills-container">
              {allPreferences.map(pref => (
                <button 
                  key={pref} 
                  className={`pill-btn ${selectedPrefs.includes(pref) ? 'active' : ''}`}
                  onClick={() => togglePref(pref)}
                >
                  {pref}
                </button>
              ))}
            </div>
            <button className="btn-primary mt-auto" onClick={() => setStep('final')}>Confirm</button>
          </div>
        );

      case 'final':
        return (
          <div className="step-final slide-up">
            <div className="illustration-box">
              <img src="/login_screen_image.png" alt="Illustration" className="start-img" />
            </div>
            <h1 className="step-title">Find Your Way!</h1>
            
            <div className="final-bottom mt-auto">
              <button className="btn-primary" onClick={() => onLoginSuccess('mock-wizard-token')}>
                Get Started!
              </button>
              <p className="terms-text">
                By using WAY Transit, you agree to the<br/>
                <strong>Terms</strong> and <strong>Privacy Policy.</strong>
              </p>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="wizard-wrapper">
      <div className="wizard-container">
        {renderStep()}
      </div>
    </div>
  );
}
