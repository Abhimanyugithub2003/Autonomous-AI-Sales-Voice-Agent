import React, { useState, useEffect, useRef } from 'react';
import {
  Mic, MicOff, PhoneCall, PhoneOff, Volume2, VolumeX,
  Calendar, CheckCircle, Clock, Database, Sparkles,
  User, Mail, Phone, DollarSign, Cpu, FileText,
  TrendingUp, BarChart3, ChevronRight, Download, Send,
  RefreshCw, ShieldCheck, HelpCircle
} from './icons.jsx';

export default function App() {
  // Call & Voice State
  const [isCallActive, setIsCallActive] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isAgentThinking, setIsAgentThinking] = useState(false);
  const [audioMuted, setAudioMuted] = useState(false);
  const [voiceMode, setVoiceMode] = useState('edge'); // 'edge' (server TTS) or 'web' (browser native)

  // Data & History
  const [callId, setCallId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState('');
  const [activeTab, setActiveTab] = useState('lead'); // 'lead', 'booking', 'rag', 'analytics'

  // Lead State
  const [lead, setLead] = useState({
    customer_name: null,
    email: null,
    phone: null,
    budget: null,
    requirements: [],
    timeline: null,
    interest_level: 'Medium',
    sentiment: 'Neutral',
    score: 0,
    status: 'Not Qualified'
  });

  // Appointment & Calendar
  const [appointment, setAppointment] = useState(null);
  const [availableSlots, setAvailableSlots] = useState([]);

  // Products (RAG)
  const [products, setProducts] = useState([]);
  const [retrievedProducts, setRetrievedProducts] = useState([]);

  // Analytics & Summary
  const [callSummary, setCallSummary] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [systemHealth, setSystemHealth] = useState(null);

  // References
  const transcriptEndRef = useRef(null);
  const recognitionRef = useRef(null);
  const audioPlayerRef = useRef(new Audio());

  // Auto-scroll transcript
  useEffect(() => {
    transcriptEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isAgentThinking]);

  // Initial Data Fetch
  useEffect(() => {
    fetchHealth();
    fetchProducts();
    fetchSlots();
    fetchAnalytics();
  }, []);

  const fetchHealth = async () => {
    try {
      const res = await fetch('/api/health');
      const data = await res.json();
      setSystemHealth(data);
    } catch (e) {
      console.warn('Backend not yet reachable', e);
    }
  };

  const fetchProducts = async () => {
    try {
      const res = await fetch('/api/products');
      const data = await res.json();
      setProducts(data.products || []);
    } catch (e) {}
  };

  const fetchSlots = async () => {
    try {
      const res = await fetch('/api/appointments/slots');
      const data = await res.json();
      setAvailableSlots(data.slots || []);
    } catch (e) {}
  };

  const fetchAnalytics = async () => {
    try {
      const res = await fetch('/api/analytics');
      const data = await res.json();
      setAnalytics(data);
    } catch (e) {}
  };

  // Setup Web Speech API for Browser-level Speech-to-Text
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = false;
      recognition.lang = 'en-US';

      recognition.onstart = () => {
        setIsListening(true);
      };

      recognition.onresult = (event) => {
        const last = event.results.length - 1;
        const transcript = event.results[last][0].transcript.trim();
        if (transcript) {
          handleUserUtterance(transcript);
        }
      };

      recognition.onerror = (event) => {
        console.warn('Speech recognition status:', event.error);
        if (event.error === 'not-allowed') {
          setIsListening(false);
        }
      };

      recognition.onend = () => {
        // Automatically keep listening if call is still active
        if (isCallActive && !isSpeaking) {
          try {
            recognition.start();
          } catch (e) {}
        } else {
          setIsListening(false);
        }
      };

      recognitionRef.current = recognition;
    }
  }, [isCallActive, isSpeaking]);

  // Start Call
  const handleStartCall = () => {
    const newCallId = `CALL-${Math.random().toString(36).substr(2, 7).toUpperCase()}`;
    setCallId(newCallId);
    setIsCallActive(true);
    setMessages([
      {
        sender: 'agent',
        text: "Hello! Welcome to Fortive AI Solutions. My name is Alex Carter. We specialize in high-performance enterprise laptops, engineering workstations, and rugged systems. What kind of workloads or specifications are you looking for today?",
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }
    ]);
    setCallSummary(null);

    // Speak initial greeting
    speakResponse("Hello! Welcome to Fortive AI Solutions. My name is Alex Carter. We specialize in high-performance enterprise laptops, engineering workstations, and rugged systems. What kind of workloads or specifications are you looking for today?");

    // Start microphone if supported
    if (recognitionRef.current) {
      try {
        recognitionRef.current.start();
      } catch (e) {}
    }
  };

  // End Call & Generate Summary
  const handleEndCall = async () => {
    setIsCallActive(false);
    setIsListening(false);
    setIsSpeaking(false);
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch (e) {}
    }
    if (audioPlayerRef.current) {
      audioPlayerRef.current.pause();
    }
    window.speechSynthesis?.cancel();

    // Generate call summary
    if (messages.length > 0) {
      try {
        const res = await fetch('/api/call-summary', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            call_id: callId,
            history: messages,
            lead: lead,
            appointment: appointment
          })
        });
        const summaryData = await res.json();
        setCallSummary(summaryData);
        setActiveTab('analytics');
        fetchAnalytics();
      } catch (e) {
        console.error('Failed to generate summary', e);
      }
    }
  };

  // Process User Utterance
  const handleUserUtterance = async (text) => {
    if (!text.trim()) return;

    // Pause mic recognition while agent processes and speaks
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch (e) {}
    }

    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const userMsg = { sender: 'user', text, timestamp: time };
    setMessages((prev) => [...prev, userMsg]);
    setIsAgentThinking(true);

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          call_id: callId,
          message: text,
          history: [...messages, userMsg],
          current_lead: lead
        })
      });

      const data = await res.json();
      setIsAgentThinking(false);

      if (data.reply) {
        const agentMsg = {
          sender: 'agent',
          text: data.reply,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          latency: data.latency_ms
        };
        setMessages((prev) => [...prev, agentMsg]);

        // Update lead state
        if (data.lead) {
          setLead(data.lead);
        }

        // Update retrieved products
        if (data.retrieved_products) {
          setRetrievedProducts(data.retrieved_products);
        }

        // Update booking if made
        if (data.booking) {
          setAppointment(data.booking);
          setActiveTab('booking');
        }

        // Speak aloud
        speakResponse(data.reply);
      }
    } catch (e) {
      setIsAgentThinking(false);
      console.error('Chat turn error', e);
    }
  };

  // Text-to-Speech logic
  const speakResponse = async (text) => {
    if (audioMuted) return;

    setIsSpeaking(true);

    if (voiceMode === 'edge') {
      try {
        const res = await fetch('/api/tts', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text })
        });
        if (res.ok) {
          const blob = await res.blob();
          const audioUrl = URL.createObjectURL(blob);
          audioPlayerRef.current.src = audioUrl;
          audioPlayerRef.current.onended = () => {
            setIsSpeaking(false);
            if (isCallActive && recognitionRef.current) {
              try {
                recognitionRef.current.start();
              } catch (e) {}
            }
          };
          await audioPlayerRef.current.play();
          return;
        }
      } catch (err) {
        console.warn('Server TTS failed, falling back to Web Speech Synthesis', err);
      }
    }

    // Fallback or Web Speech Synthesis
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 1.0;
      utterance.pitch = 1.0;
      utterance.onend = () => {
        setIsSpeaking(false);
        if (isCallActive && recognitionRef.current) {
          try {
            recognitionRef.current.start();
          } catch (e) {}
        }
      };
      window.speechSynthesis.speak(utterance);
    } else {
      setIsSpeaking(false);
    }
  };

  // Form submit for typing input
  const handleTextSubmit = (e) => {
    e.preventDefault();
    if (!inputText.trim()) return;
    if (!isCallActive) {
      handleStartCall();
    }
    const txt = inputText;
    setInputText('');
    handleUserUtterance(txt);
  };

  // Quick scenario triggers
  const triggerScenario = (scenarioText) => {
    if (!isCallActive) {
      handleStartCall();
      setTimeout(() => {
        handleUserUtterance(scenarioText);
      }, 600);
    } else {
      handleUserUtterance(scenarioText);
    }
  };

  return (
    <div style={{ maxWidth: '1440px', margin: '0 auto', padding: '24px 20px', minHeight: '100vh', display: 'flex', flexDirection: 'column', gap: '20px' }}>
      
      {/* Header */}
      <header className="glass-panel" style={{ padding: '16px 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{ width: '44px', height: '44px', borderRadius: '12px', background: 'linear-gradient(135deg, #6366f1 0%, #06b6d4 100%)', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 4px 12px rgba(99,102,241,0.4)' }}>
            <Mic size={24} color="#fff" />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <h1 style={{ fontSize: '20px', fontWeight: '800', letterSpacing: '-0.5px' }}>FORTIVE AI</h1>
              <span className="badge badge-info">Autonomous Sales Agent</span>
            </div>
            <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>Real-time Voice Conversation • RAG Knowledge • Lead Qualification • Meeting Scheduling</p>
          </div>
        </div>

        {/* System Badges & Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
          {systemHealth && (
            <div style={{ display: 'flex', gap: '8px' }}>
              <span className={`badge ${systemHealth.database?.connected ? 'badge-success' : 'badge-warning'}`}>
                <Database size={12} />
                {systemHealth.database?.connected ? 'MongoDB Live' : 'JSON Fallback'}
              </span>
              <span className="badge badge-purple">
                <Sparkles size={12} />
                {systemHealth.llm_engine}
              </span>
            </div>
          )}

          {/* Audio Output Mode Toggle */}
          <div style={{ display: 'flex', background: 'rgba(255,255,255,0.05)', borderRadius: '8px', padding: '2px', border: '1px solid var(--border-color)' }}>
            <button
              onClick={() => setVoiceMode('edge')}
              style={{
                background: voiceMode === 'edge' ? 'var(--primary)' : 'transparent',
                color: '#fff',
                border: 'none',
                padding: '4px 10px',
                borderRadius: '6px',
                fontSize: '11px',
                cursor: 'pointer',
                fontWeight: '600'
              }}
            >
              Edge Neural TTS
            </button>
            <button
              onClick={() => setVoiceMode('web')}
              style={{
                background: voiceMode === 'web' ? 'var(--primary)' : 'transparent',
                color: '#fff',
                border: 'none',
                padding: '4px 10px',
                borderRadius: '6px',
                fontSize: '11px',
                cursor: 'pointer',
                fontWeight: '600'
              }}
            >
              Browser Speech
            </button>
          </div>

          {/* Mute Audio */}
          <button
            onClick={() => setAudioMuted(!audioMuted)}
            className="btn-secondary"
            title={audioMuted ? 'Unmute Agent' : 'Mute Agent'}
          >
            {audioMuted ? <VolumeX size={16} color="var(--danger)" /> : <Volume2 size={16} />}
          </button>
        </div>
      </header>

      {/* Quick Demo Scenario Bar */}
      <div className="glass-panel" style={{ padding: '12px 20px', display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
        <span style={{ fontSize: '12px', fontWeight: '700', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
          Test Scenarios:
        </span>
        <button
          onClick={() => triggerScenario("Hi, I want to know about your available products.")}
          className="btn-secondary"
          style={{ fontSize: '12px', padding: '6px 12px' }}
        >
          1. General Product Inquiry
        </button>
        <button
          onClick={() => triggerScenario("I am David Miller. I need a heavy duty laptop for 3D CAD modeling and deep learning. My budget is around $3500 and email is david@techfirm.com.")}
          className="btn-secondary"
          style={{ fontSize: '12px', padding: '6px 12px' }}
        >
          2. High-Intent CAD/AI Lead ($3500)
        </button>
        <button
          onClick={() => triggerScenario("Yes, please schedule a product demo with your engineering specialist.")}
          className="btn-secondary"
          style={{ fontSize: '12px', padding: '6px 12px' }}
        >
          3. Book Appointment Demo
        </button>
      </div>

      {/* Main Grid: Left Stage (Voice & Transcript) & Right Stage (Lead & Knowledge Cockpit) */}
      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(380px, 1.25fr) minmax(360px, 1fr)', gap: '20px', flex: 1 }}>
        
        {/* Left Column: Voice Call Cockpit & Transcript */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          
          {/* Active Voice Stage */}
          <div className="glass-panel" style={{ padding: '24px', textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center', position: 'relative', overflow: 'hidden' }}>
            
            {/* Background Glow Ring */}
            <div style={{
              position: 'absolute',
              width: '260px',
              height: '260px',
              borderRadius: '50%',
              background: isSpeaking ? 'radial-gradient(circle, rgba(6,182,212,0.2) 0%, transparent 70%)' : isListening ? 'radial-gradient(circle, rgba(99,102,241,0.25) 0%, transparent 70%)' : 'transparent',
              filter: 'blur(20px)',
              pointerEvents: 'none'
            }} />

            {/* Glowing Microphone Orb */}
            <div
              className={isListening || isSpeaking ? 'pulsing-mic' : ''}
              style={{
                width: '100px',
                height: '100px',
                borderRadius: '50%',
                background: isSpeaking
                  ? 'linear-gradient(135deg, #06b6d4 0%, #3b82f6 100%)'
                  : isListening
                  ? 'linear-gradient(135deg, #6366f1 0%, #a855f7 100%)'
                  : 'rgba(255,255,255,0.08)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: isSpeaking
                  ? '0 0 35px rgba(6, 182, 212, 0.6)'
                  : isListening
                  ? '0 0 35px rgba(99, 102, 241, 0.6)'
                  : 'none',
                marginBottom: '16px',
                transition: 'all 0.3s ease'
              }}
            >
              {isListening ? (
                <Mic size={42} color="#fff" />
              ) : isSpeaking ? (
                <Volume2 size={42} color="#fff" />
              ) : (
                <PhoneCall size={38} color="#94a3b8" />
              )}
            </div>

            {/* Call Status Badge */}
            <div style={{ marginBottom: '12px' }}>
              {isSpeaking ? (
                <span className="badge badge-info" style={{ fontSize: '13px', padding: '6px 14px' }}>
                  <Volume2 size={14} /> Agent Alex is Speaking...
                </span>
              ) : isAgentThinking ? (
                <span className="badge badge-purple" style={{ fontSize: '13px', padding: '6px 14px' }}>
                  <RefreshCw size={14} className="spin" /> Consulting RAG & Reasoning...
                </span>
              ) : isListening ? (
                <span className="badge badge-success" style={{ fontSize: '13px', padding: '6px 14px' }}>
                  <Mic size={14} /> Listening to your voice... Speak now!
                </span>
              ) : isCallActive ? (
                <span className="badge badge-warning" style={{ fontSize: '13px', padding: '6px 14px' }}>
                  Call Connected • Waiting for speech
                </span>
              ) : (
                <span className="badge" style={{ background: 'rgba(255,255,255,0.06)', color: 'var(--text-muted)', fontSize: '13px', padding: '6px 14px' }}>
                  Voice Agent Standby
                </span>
              )}
            </div>

            {/* Waveform Animation */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px', height: '40px', marginBottom: '20px' }}>
              {[0.4, 0.8, 1.2, 0.6, 1.4, 0.9, 0.5, 1.1, 0.7].map((dur, idx) => (
                <div
                  key={idx}
                  style={{
                    width: '5px',
                    height: isSpeaking ? `${Math.sin(idx + 1) * 20 + 25}px` : isListening ? `${Math.cos(idx + 1) * 15 + 20}px` : '6px',
                    background: isSpeaking ? 'var(--accent)' : isListening ? 'var(--primary)' : 'rgba(255,255,255,0.2)',
                    borderRadius: '4px',
                    transition: 'all 0.15s ease',
                    animation: (isSpeaking || isListening) ? `waveBar ${dur}s infinite ease-in-out` : 'none'
                  }}
                />
              ))}
            </div>

            {/* Primary Action Buttons */}
            <div style={{ display: 'flex', gap: '14px', alignItems: 'center' }}>
              {!isCallActive ? (
                <button onClick={handleStartCall} className="btn-primary" style={{ padding: '12px 28px', fontSize: '15px' }}>
                  <PhoneCall size={18} />
                  Start Live Voice Call
                </button>
              ) : (
                <button onClick={handleEndCall} className="btn-danger" style={{ padding: '12px 28px', fontSize: '15px' }}>
                  <PhoneOff size={18} />
                  End Call & Generate Summary
                </button>
              )}
            </div>
          </div>

          {/* Live Transcript Pane */}
          <div className="glass-panel" style={{ flex: 1, display: 'flex', flexDirection: 'column', height: '440px', overflow: 'hidden' }}>
            <div style={{ padding: '14px 18px', borderBottom: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <FileText size={16} color="var(--primary)" />
                <span style={{ fontSize: '14px', fontWeight: '700' }}>Live Call Transcript</span>
                {callId && <span style={{ fontSize: '11px', color: 'var(--text-dim)', background: 'rgba(255,255,255,0.05)', padding: '2px 6px', borderRadius: '4px' }}>{callId}</span>}
              </div>
              <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{messages.length} utterances</span>
            </div>

            {/* Messages Feed */}
            <div style={{ flex: 1, padding: '16px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '14px' }}>
              {messages.length === 0 ? (
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--text-dim)', textAlign: 'center', gap: '8px' }}>
                  <Mic size={32} style={{ opacity: 0.3 }} />
                  <p style={{ fontSize: '14px' }}>Click "Start Live Voice Call" or choose a scenario above to begin conversation.</p>
                </div>
              ) : (
                messages.map((msg, index) => (
                  <div
                    key={index}
                    style={{
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: msg.sender === 'user' ? 'flex-end' : 'flex-start'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px', fontSize: '11px', color: 'var(--text-dim)' }}>
                      <span>{msg.sender === 'user' ? 'Customer' : 'Alex (Fortive AI)'}</span>
                      <span>•</span>
                      <span>{msg.timestamp}</span>
                      {msg.latency && <span style={{ color: 'var(--accent)', fontWeight: '600' }}>⚡ {msg.latency}ms</span>}
                    </div>
                    <div
                      style={{
                        maxWidth: '82%',
                        padding: '12px 16px',
                        borderRadius: msg.sender === 'user' ? '14px 14px 2px 14px' : '14px 14px 14px 2px',
                        background: msg.sender === 'user'
                          ? 'linear-gradient(135deg, #4f46e5 0%, #4338ca 100%)'
                          : 'rgba(255, 255, 255, 0.06)',
                        border: msg.sender === 'user' ? 'none' : '1px solid var(--border-color)',
                        color: '#fff',
                        fontSize: '14px',
                        lineHeight: '1.5',
                        boxShadow: msg.sender === 'user' ? '0 4px 12px rgba(79, 70, 229, 0.25)' : 'none'
                      }}
                    >
                      {msg.text}
                    </div>
                  </div>
                ))
              )}
              {isAgentThinking && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--accent)', fontSize: '13px', fontStyle: 'italic', padding: '6px 0' }}>
                  <RefreshCw size={14} className="spin" />
                  Alex is analyzing requirements & matching product catalog...
                </div>
              )}
              <div ref={transcriptEndRef} />
            </div>

            {/* Input Bar (Text + Voice fallback) */}
            <form onSubmit={handleTextSubmit} style={{ padding: '12px 16px', borderTop: '1px solid var(--border-color)', display: 'flex', gap: '10px' }}>
              <input
                type="text"
                placeholder={isCallActive ? "Type customer speech or speak into microphone..." : "Type a message to start call..."}
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                style={{
                  flex: 1,
                  background: 'rgba(255, 255, 255, 0.04)',
                  border: '1px solid var(--border-color)',
                  borderRadius: '10px',
                  padding: '10px 14px',
                  color: '#fff',
                  fontSize: '14px',
                  outline: 'none'
                }}
              />
              <button type="submit" className="btn-primary" style={{ padding: '0 16px' }}>
                <Send size={16} />
              </button>
            </form>
          </div>
        </div>

        {/* Right Column: Dynamic Intelligence Stage (Lead, Appointments, RAG, Analytics) */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          
          {/* Navigation Tabs */}
          <div className="glass-panel" style={{ padding: '6px', display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '6px' }}>
            <button
              onClick={() => setActiveTab('lead')}
              style={{
                background: activeTab === 'lead' ? 'var(--primary)' : 'transparent',
                color: activeTab === 'lead' ? '#fff' : 'var(--text-muted)',
                border: 'none',
                padding: '8px 4px',
                borderRadius: '8px',
                fontSize: '12px',
                fontWeight: '600',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '6px'
              }}
            >
              <User size={14} /> Lead BANT
            </button>
            <button
              onClick={() => setActiveTab('booking')}
              style={{
                background: activeTab === 'booking' ? 'var(--primary)' : 'transparent',
                color: activeTab === 'booking' ? '#fff' : 'var(--text-muted)',
                border: 'none',
                padding: '8px 4px',
                borderRadius: '8px',
                fontSize: '12px',
                fontWeight: '600',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '6px'
              }}
            >
              <Calendar size={14} /> Schedule
            </button>
            <button
              onClick={() => setActiveTab('rag')}
              style={{
                background: activeTab === 'rag' ? 'var(--primary)' : 'transparent',
                color: activeTab === 'rag' ? '#fff' : 'var(--text-muted)',
                border: 'none',
                padding: '8px 4px',
                borderRadius: '8px',
                fontSize: '12px',
                fontWeight: '600',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '6px'
              }}
            >
              <Cpu size={14} /> RAG Catalog
            </button>
            <button
              onClick={() => { setActiveTab('analytics'); fetchAnalytics(); }}
              style={{
                background: activeTab === 'analytics' ? 'var(--primary)' : 'transparent',
                color: activeTab === 'analytics' ? '#fff' : 'var(--text-muted)',
                border: 'none',
                padding: '8px 4px',
                borderRadius: '8px',
                fontSize: '12px',
                fontWeight: '600',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '6px'
              }}
            >
              <BarChart3 size={14} /> Analytics
            </button>
          </div>

          {/* TAB 1: Real-time Lead Qualification Card */}
          {activeTab === 'lead' && (
            <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h3 style={{ fontSize: '16px', fontWeight: '700', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <ShieldCheck size={18} color="var(--primary)" />
                  Lead Qualification (BANT)
                </h3>
                <span className={`badge ${lead.score >= 70 ? 'badge-success' : lead.score >= 40 ? 'badge-warning' : 'badge-danger'}`}>
                  {lead.status}
                </span>
              </div>

              {/* BANT Score Meter */}
              <div style={{ background: 'rgba(255,255,255,0.04)', padding: '14px', borderRadius: '12px', border: '1px solid var(--border-color)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', fontSize: '13px' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Qualification Score</span>
                  <span style={{ fontWeight: '800', color: lead.score >= 70 ? '#34d399' : '#fbbf24' }}>{lead.score} / 100</span>
                </div>
                <div style={{ width: '100%', height: '8px', background: 'rgba(255,255,255,0.08)', borderRadius: '4px', overflow: 'hidden' }}>
                  <div
                    style={{
                      width: `${lead.score}%`,
                      height: '100%',
                      background: lead.score >= 70 ? 'linear-gradient(90deg, #10b981, #06b6d4)' : 'linear-gradient(90deg, #f59e0b, #ef4444)',
                      transition: 'width 0.4s ease'
                    }}
                  />
                </div>
              </div>

              {/* Extracted Attributes Grid */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div style={{ background: 'rgba(255,255,255,0.03)', padding: '12px', borderRadius: '10px', border: '1px solid var(--border-color)' }}>
                  <div style={{ fontSize: '11px', color: 'var(--text-dim)', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <User size={12} /> Customer Name
                  </div>
                  <div style={{ fontSize: '14px', fontWeight: '600' }}>
                    {lead.customer_name || <span style={{ color: 'var(--text-dim)' }}>Detecting...</span>}
                  </div>
                </div>

                <div style={{ background: 'rgba(255,255,255,0.03)', padding: '12px', borderRadius: '10px', border: '1px solid var(--border-color)' }}>
                  <div style={{ fontSize: '11px', color: 'var(--text-dim)', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <DollarSign size={12} /> Stated Budget
                  </div>
                  <div style={{ fontSize: '14px', fontWeight: '600', color: lead.budget ? 'var(--accent)' : 'inherit' }}>
                    {lead.budget || <span style={{ color: 'var(--text-dim)' }}>Not mentioned</span>}
                  </div>
                </div>

                <div style={{ background: 'rgba(255,255,255,0.03)', padding: '12px', borderRadius: '10px', border: '1px solid var(--border-color)' }}>
                  <div style={{ fontSize: '11px', color: 'var(--text-dim)', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <Mail size={12} /> Email Address
                  </div>
                  <div style={{ fontSize: '13px', fontWeight: '500', wordBreak: 'break-all' }}>
                    {lead.email || <span style={{ color: 'var(--text-dim)' }}>Pending capture</span>}
                  </div>
                </div>

                <div style={{ background: 'rgba(255,255,255,0.03)', padding: '12px', borderRadius: '10px', border: '1px solid var(--border-color)' }}>
                  <div style={{ fontSize: '11px', color: 'var(--text-dim)', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <Clock size={12} /> Purchase Timeline
                  </div>
                  <div style={{ fontSize: '14px', fontWeight: '600' }}>
                    {lead.timeline || <span style={{ color: 'var(--text-dim)' }}>Not specified</span>}
                  </div>
                </div>
              </div>

              {/* Requirements Chips */}
              <div>
                <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '8px' }}>Identified Technical Requirements:</div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                  {lead.requirements && lead.requirements.length > 0 ? (
                    lead.requirements.map((req, idx) => (
                      <span key={idx} className="badge badge-purple" style={{ fontSize: '11px' }}>
                        {req}
                      </span>
                    ))
                  ) : (
                    <span style={{ fontSize: '12px', color: 'var(--text-dim)' }}>No specific workloads identified yet</span>
                  )}
                </div>
              </div>

              {/* Sentiment & Intent Indicator */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '8px', borderTop: '1px solid var(--border-color)' }}>
                <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Customer Sentiment:</span>
                <span className={`badge ${lead.sentiment === 'Positive' ? 'badge-success' : 'badge-info'}`}>
                  {lead.sentiment}
                </span>
              </div>
            </div>
          )}

          {/* TAB 2: Appointment Booking */}
          {activeTab === 'booking' && (
            <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <h3 style={{ fontSize: '16px', fontWeight: '700', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Calendar size={18} color="var(--primary)" />
                Appointment Booking & Calendar
              </h3>

              {appointment ? (
                <div style={{ background: 'rgba(16, 185, 129, 0.08)', border: '1px solid rgba(16, 185, 129, 0.3)', borderRadius: '12px', padding: '16px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#34d399', fontWeight: '700', fontSize: '15px' }}>
                    <CheckCircle size={20} />
                    Appointment Confirmed!
                  </div>
                  <div style={{ fontSize: '13px', lineHeight: '1.6', color: 'var(--text-main)' }}>
                    <div><strong>Meeting ID:</strong> {appointment.booking_id}</div>
                    <div><strong>Client:</strong> {appointment.customer_name}</div>
                    <div><strong>Date & Time:</strong> {appointment.date} at {appointment.time_slot}</div>
                    <div><strong>Meeting Link:</strong> <a href={appointment.meeting_link} target="_blank" rel="noreferrer" style={{ color: 'var(--accent)' }}>{appointment.meeting_link}</a></div>
                  </div>
                  <a
                    href={`/api/appointments/${appointment.booking_id}/ics`}
                    className="btn-primary"
                    style={{ fontSize: '12px', padding: '8px 14px', alignSelf: 'flex-start', textDecoration: 'none' }}
                  >
                    <Download size={14} /> Download .ICS Calendar Invite
                  </a>
                </div>
              ) : (
                <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
                  When the customer expresses buying interest, the AI agent automatically proposes and books a live 20-minute demonstration.
                </p>
              )}

              {/* Available Slots Preview */}
              <div>
                <div style={{ fontSize: '13px', fontWeight: '600', marginBottom: '8px', color: 'var(--text-muted)' }}>
                  Upcoming Open Slots (Google Calendar Synchronized):
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '200px', overflowY: 'auto' }}>
                  {availableSlots.slice(0, 4).map((slot, idx) => (
                    <div
                      key={idx}
                      style={{
                        padding: '10px 14px',
                        background: 'rgba(255,255,255,0.03)',
                        borderRadius: '8px',
                        border: '1px solid var(--border-color)',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        fontSize: '13px'
                      }}
                    >
                      <span>{slot.label}</span>
                      <span className="badge badge-success" style={{ fontSize: '10px' }}>Available</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* TAB 3: RAG Knowledge Base Inspector */}
          {activeTab === 'rag' && (
            <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h3 style={{ fontSize: '16px', fontWeight: '700', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Cpu size={18} color="var(--primary)" />
                  RAG Enterprise Knowledge Base
                </h3>
                <span className="badge badge-info">{products.length} Products Indexed</span>
              </div>
              <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                Vector retrieval ranks enterprise hardware specs, pricing, warranties, and target use cases in sub-milliseconds.
              </p>

              {/* Product Cards List */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', maxHeight: '340px', overflowY: 'auto' }}>
                {products.map((p) => (
                  <div
                    key={p.id}
                    style={{
                      background: 'rgba(255,255,255,0.03)',
                      borderRadius: '10px',
                      border: '1px solid var(--border-color)',
                      padding: '12px'
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '6px' }}>
                      <span style={{ fontWeight: '700', fontSize: '14px', color: '#fff' }}>{p.name}</span>
                      <span style={{ color: '#34d399', fontWeight: '800', fontSize: '14px' }}>${p.price}</span>
                    </div>
                    <div style={{ fontSize: '11px', color: 'var(--text-dim)', marginBottom: '6px' }}>{p.category}</div>
                    <div style={{ fontSize: '12px', color: 'var(--text-muted)', lineHeight: '1.4' }}>{p.key_benefits}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* TAB 4: Executive Call Summary & CRM Analytics */}
          {activeTab === 'analytics' && (
            <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <h3 style={{ fontSize: '16px', fontWeight: '700', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <TrendingUp size={18} color="var(--primary)" />
                Call Summary & CRM Metrics (MongoDB)
              </h3>

              {/* Summary Block */}
              {callSummary ? (
                <div style={{ background: 'rgba(99, 102, 241, 0.08)', border: '1px solid rgba(99, 102, 241, 0.25)', borderRadius: '12px', padding: '14px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  <div style={{ fontWeight: '700', fontSize: '14px', color: '#818cf8' }}>Executive Call Summary</div>
                  <p style={{ fontSize: '13px', lineHeight: '1.5', color: '#e2e8f0' }}>{callSummary.executive_summary}</p>
                  <div style={{ fontSize: '12px' }}>
                    <strong>Recommended Next Action:</strong> {callSummary.recommended_next_action}
                  </div>
                </div>
              ) : (
                <div style={{ padding: '12px', background: 'rgba(255,255,255,0.02)', borderRadius: '10px', fontSize: '12px', color: 'var(--text-dim)' }}>
                  End the current call or click below to generate an automated executive summary and save lead details to MongoDB.
                </div>
              )}

              {/* Aggregated MongoDB Metrics */}
              {analytics && (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '10px' }}>
                  <div style={{ background: 'rgba(255,255,255,0.03)', padding: '12px', borderRadius: '10px', border: '1px solid var(--border-color)' }}>
                    <div style={{ fontSize: '11px', color: 'var(--text-dim)' }}>Total Calls Processed</div>
                    <div style={{ fontSize: '20px', fontWeight: '800', marginTop: '4px' }}>{analytics.total_calls}</div>
                  </div>
                  <div style={{ background: 'rgba(255,255,255,0.03)', padding: '12px', borderRadius: '10px', border: '1px solid var(--border-color)' }}>
                    <div style={{ fontSize: '11px', color: 'var(--text-dim)' }}>Qualified Leads Saved</div>
                    <div style={{ fontSize: '20px', fontWeight: '800', marginTop: '4px', color: 'var(--accent)' }}>{analytics.total_leads}</div>
                  </div>
                  <div style={{ background: 'rgba(255,255,255,0.03)', padding: '12px', borderRadius: '10px', border: '1px solid var(--border-color)' }}>
                    <div style={{ fontSize: '11px', color: 'var(--text-dim)' }}>Appointments Booked</div>
                    <div style={{ fontSize: '20px', fontWeight: '800', marginTop: '4px', color: '#34d399' }}>{analytics.appointments_booked}</div>
                  </div>
                  <div style={{ background: 'rgba(255,255,255,0.03)', padding: '12px', borderRadius: '10px', border: '1px solid var(--border-color)' }}>
                    <div style={{ fontSize: '11px', color: 'var(--text-dim)' }}>Pipeline Conversion Rate</div>
                    <div style={{ fontSize: '20px', fontWeight: '800', marginTop: '4px', color: '#fbbf24' }}>{analytics.conversion_rate_percent}%</div>
                  </div>
                </div>
              )}
            </div>
          )}

        </div>
      </div>

    </div>
  );
}
