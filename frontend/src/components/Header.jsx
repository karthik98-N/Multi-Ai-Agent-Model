import React from 'react';
import { ShieldCheck, Zap, Activity } from 'lucide-react';

export default function Header({ health }) {
  const isOnline = health?.status === 'healthy';
  const modelName = health?.primary_model ? health.primary_model.replace('openai/', '') : 'Groq 120B';

  return (
    <header className="app-header">
      <div className="brand-section">
        <div className="brand-logo-glow">
          <ShieldCheck size={24} />
        </div>
        <div className="brand-titles">
          <h1>HackFusion 2026: AI Verification Engine</h1>
          <div className="brand-tag">Multi-Agent Auditing & Red-Teaming Platform</div>
        </div>
      </div>

      <div className="header-badges">
        <div className="status-pill" title={isOnline ? "Backend is connected and healthy" : "Connecting to backend..."}>
          <div 
            className="pulse-dot" 
            style={{ 
              background: isOnline ? 'var(--accent-emerald)' : 'var(--accent-amber)',
              boxShadow: isOnline ? '0 0 8px var(--accent-emerald)' : '0 0 8px var(--accent-amber)'
            }} 
          />
          <span>{modelName}</span>
        </div>
        <div className="status-pill">
          <Zap size={13} style={{ color: 'var(--accent-cyan)' }} />
          <span>Live DDG Search</span>
        </div>
        <div className="status-pill">
          <Activity size={13} style={{ color: 'var(--accent-purple)' }} />
          <span>100% Free Stack</span>
        </div>
      </div>
    </header>
  );
}

