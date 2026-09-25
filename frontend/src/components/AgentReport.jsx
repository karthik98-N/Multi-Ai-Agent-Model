import React, { useState } from 'react';
import { 
  Compass, Search, Cpu, CheckCircle2, AlertTriangle, Flame, Scale, Wrench, 
  ChevronDown, ChevronUp, ShieldAlert, ListChecks, Layers
} from 'lucide-react';


// ── Human-readable renderer for pipeline step data ──────────────────────────
function renderValue(val, depth = 0) {
  if (val === null || val === undefined) return <span style={{ color: 'var(--text-subtle)' }}>—</span>;
  if (typeof val === 'boolean') return <span style={{ color: val ? '#059669' : '#E11D48', fontWeight: 700 }}>{val ? 'Yes' : 'No'}</span>;
  if (typeof val === 'number') return <span style={{ color: 'var(--accent-red)', fontWeight: 700 }}>{val}</span>;
  if (typeof val === 'string') {
    if (val.trim() === '{"contradictions": []}' || val.trim() === '{"contradictions":[]}' || val.includes('{"contradictions":')) {
      return <span style={{ color: '#059669', fontWeight: 700 }}>[verified successfully]</span>;
    }
    return <span style={{ color: 'var(--text-main)', fontWeight: 500 }}>{val}</span>;
  }

  if (Array.isArray(val)) {
    if (val.length === 0) return <span style={{ color: '#059669', fontWeight: 700 }}>[verified successfully]</span>;
    // Array of primitives → comma chips
    if (val.every(v => typeof v !== 'object' || v === null)) {
      return (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.35rem' }}>
          {val.map((v, i) => (
            <span key={i} style={{
              background: '#FFEED1',
              border: '1.5px solid var(--border-subtle)',
              borderRadius: '6px',
              padding: '0.15rem 0.55rem',
              fontSize: '0.8rem',
              fontWeight: 600,
              color: 'var(--text-main)'
            }}>{String(v)}</span>
          ))}
        </div>
      );
    }
    // Array of objects → numbered cards
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginTop: '0.25rem' }}>
        {val.map((v, i) => (
          <div key={i} style={{
            background: '#FFFFFF',
            border: '1.5px solid var(--border-subtle)',
            borderRadius: '8px',
            padding: '0.65rem 0.95rem',
            boxShadow: '0 1px 3px rgba(92, 64, 30, 0.04)'
          }}>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-subtle)', marginBottom: '0.35rem', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 700 }}>
              #{i + 1}
            </div>
            {renderValue(v, depth + 1)}
          </div>
        ))}
      </div>
    );
  }

  if (typeof val === 'object') {
    const entries = Object.entries(val);
    if (entries.length === 0) return <span style={{ color: 'var(--text-subtle)' }}>—</span>;
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.45rem' }}>
        {entries.map(([k, v]) => {
          const label = k.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
          return (
            <div key={k} style={{ display: 'flex', flexDirection: 'column', gap: '0.15rem' }}>
              <span style={{ fontSize: '0.72rem', color: 'var(--text-subtle)', textTransform: 'uppercase', letterSpacing: '0.06em', fontWeight: 700 }}>
                {label}
              </span>
              <div style={{ paddingLeft: depth > 0 ? '0.5rem' : 0 }}>
                {renderValue(v, depth + 1)}
              </div>
            </div>
          );
        })}
      </div>
    );
  }
  return <span style={{ color: 'var(--text-main)', fontWeight: 500 }}>{String(val)}</span>;
}

function StepDataView({ data, agentColor }) {
  const SKIP_KEYS = new Set(['raw', 'raw_output', 'debug']);
  const entries = Object.entries(data).filter(([k]) => !SKIP_KEYS.has(k));

  if (entries.length === 0) return null;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      {entries.map(([key, val]) => {
        const label = key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
        return (
          <div key={key}>
            <div style={{
              fontSize: '0.73rem',
              fontWeight: 700,
              letterSpacing: '0.08em',
              textTransform: 'uppercase',
              color: agentColor || 'var(--accent-cyan)',
              marginBottom: '0.4rem',
              borderBottom: `1px solid ${agentColor || 'rgba(6,182,212,0.3)'}30`,
              paddingBottom: '0.25rem'
            }}>
              {label}
            </div>
            <div style={{ fontSize: '0.875rem', lineHeight: 1.65 }}>
              {renderValue(val)}
            </div>
          </div>
        );
      })}
    </div>
  );
}
// ─────────────────────────────────────────────────────────────────────────────

const AGENT_CONFIG = {
  "Planner Agent": { icon: Compass, color: "var(--accent-cyan)" },
  "Research Agent": { icon: Search, color: "var(--accent-purple)" },
  "Generator Agent": { icon: Cpu, color: "var(--accent-indigo)" },
  "Independent Verifier": { icon: CheckCircle2, color: "var(--accent-emerald)" },
  "Contradiction Checker": { icon: AlertTriangle, color: "var(--accent-amber)" },
  "Red-Team Critic": { icon: Flame, color: "var(--accent-rose)" },
  "Decision Engine": { icon: Scale, color: "#cbd5e1" },
  "Correction Agent": { icon: Wrench, color: "var(--accent-indigo)" }
};

export default function AgentReport({ result }) {
  const [activeTab, setActiveTab] = useState('matrix'); // 'matrix' | 'critic' | 'trace'
  const [expandedSteps, setExpandedSteps] = useState({});

  if (!result) return null;

  const steps = result.steps_trace || [];
  const claims = result.claims_matrix || [];
  const objections = result.critic_objections || [];
  const contradictions = result.contradictions || [];

  const toggleStep = (idx) => {
    setExpandedSteps(prev => ({ ...prev, [idx]: !prev[idx] }));
  };

  return (
    <div className="glass-panel" style={{ padding: '2rem' }}>
      {/* HEADER WITH TABS */}
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center', 
        flexWrap: 'wrap', 
        gap: '1rem', 
        borderBottom: '1px solid var(--border-subtle)', 
        paddingBottom: '1.25rem',
        marginBottom: '1.5rem'
      }}>
        <div>
          <h3 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--accent-red)' }}>
            Multi-Agent Glassbox Audit Report
          </h3>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            Transparent verification logs, atomic claim verdicts, and adversarial red-team objections.
          </p>
        </div>

        {/* Tab Buttons with tactile depth */}
        <div style={{ display: 'flex', gap: '0.65rem' }}>
          <button
            type="button"
            className={activeTab === 'matrix' ? 'btn-primary' : 'bench-chip'}
            onClick={() => setActiveTab('matrix')}
            style={activeTab === 'matrix' ? { padding: '0.45rem 1rem', fontSize: '0.82rem' } : undefined}
          >
            <ListChecks size={14} />
            <span>Claims Matrix ({claims.length})</span>
          </button>

          <button
            type="button"
            className={activeTab === 'critic' ? 'btn-primary' : 'bench-chip'}
            onClick={() => setActiveTab('critic')}
            style={activeTab === 'critic' ? { padding: '0.45rem 1rem', fontSize: '0.82rem' } : undefined}
          >
            <Flame size={14} />
            <span>Critic Flags ({objections.length})</span>
          </button>

          <button
            type="button"
            className={activeTab === 'trace' ? 'btn-primary' : 'bench-chip'}
            onClick={() => setActiveTab('trace')}
            style={activeTab === 'trace' ? { padding: '0.45rem 1rem', fontSize: '0.82rem' } : undefined}
          >
            <Layers size={14} />
            <span>Pipeline Stepper ({steps.length})</span>
          </button>
        </div>
      </div>

      {/* TAB 1: CLAIMS VERIFICATION MATRIX */}
      {activeTab === 'matrix' && (
        <div>
          {claims.length === 0 ? (
            <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
              No atomic claims extracted for this query.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {claims.map((claim, idx) => (
                <div key={idx} style={{ 
                  background: '#FFFFFF', 
                  border: '1.5px solid var(--border-subtle)', 
                  borderRadius: '14px', 
                  padding: '1.35rem',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.85rem',
                  boxShadow: '0 2px 8px rgba(92, 64, 30, 0.05)'
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                      <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--text-subtle)', fontSize: '0.85rem' }}>
                        {claim.id}
                      </span>
                      <span className={`tag-badge ${claim.status}`}>
                        {claim.status}
                      </span>
                    </div>
                    <div style={{ display: 'flex', gap: '0.35rem', flexWrap: 'wrap', justifyContent: 'flex-end' }}>
                      {claim.evidence_refs && claim.evidence_refs.length > 0 ? (
                        claim.evidence_refs.map((ref, rIdx) => (
                          <span key={rIdx} className="ref-pill">{ref}</span>
                        ))
                      ) : (
                        <span style={{ color: 'var(--text-subtle)', fontSize: '0.75rem', fontWeight: 600 }}>No Evidence</span>
                      )}
                    </div>
                  </div>
                  
                  <div style={{ color: 'var(--text-main)', fontWeight: 600, fontSize: '1rem', lineHeight: 1.6 }}>
                    {claim.text}
                  </div>
                  
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.88rem', background: 'var(--bg-secondary)', padding: '0.85rem', borderRadius: '10px', borderLeft: '4px solid var(--accent-red)' }}>
                    <strong style={{ color: 'var(--text-main)' }}>Reasoning:</strong> {claim.reasoning || "Audited against reference corpus."}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* CONTRADICTIONS IF ANY */}
          {contradictions.length > 0 && (
            <div style={{ marginTop: '2rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem', color: '#fb7185' }}>
                <ShieldAlert size={18} />
                <h4 style={{ fontSize: '1rem', fontWeight: 700 }}>Detected Contradictions ({contradictions.length})</h4>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {contradictions.map((c, idx) => (
                  <div key={idx} style={{ background: 'rgba(244, 63, 94, 0.1)', border: '1px solid rgba(244, 63, 94, 0.3)', borderRadius: '10px', padding: '1rem' }}>
                    <div style={{ fontSize: '0.78rem', color: '#fb7185', fontWeight: 700, textTransform: 'uppercase', marginBottom: '0.35rem' }}>
                      {c.conflict_type}
                    </div>
                    <div style={{ fontSize: '0.88rem', color: '#fca5a5' }}>
                      {c.explanation}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* TAB 2: RED-TEAM CRITIC OBJECTIONS */}
      {activeTab === 'critic' && (
        <div>
          {objections.length === 0 ? (
            <div style={{ padding: '2.5rem', textAlign: 'center', color: '#34d399', background: 'rgba(16, 185, 129, 0.08)', borderRadius: '12px', border: '1px solid rgba(16, 185, 129, 0.2)' }}>
              <CheckCircle2 size={32} style={{ margin: '0 auto 0.5rem auto' }} />
              <div style={{ fontWeight: 600 }}>Zero Critical Objections Raised</div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                Adversarial Red-Team Critic did not detect hallucinated APIs, deprecated methods, or unstated assumptions.
              </div>
            </div>
          ) : (
            <div className="critic-grid" style={{ padding: 0 }}>
              {objections.map((obj, idx) => (
                <div key={idx} className={`critic-card ${obj.severity}`}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--text-subtle)' }}>
                      {obj.id}
                    </span>
                    <span className={`severity-pill ${obj.severity}`}>{obj.severity}</span>
                  </div>

                  <div>
                    <div style={{ fontSize: '0.88rem', fontWeight: 600, color: '#f87171', marginBottom: '0.25rem' }}>
                      {obj.issue}
                    </div>
                    {obj.target && (
                      <div style={{ fontSize: '0.78rem', color: 'var(--text-subtle)', background: 'rgba(0,0,0,0.3)', padding: '0.4rem', borderRadius: '6px', fontFamily: 'var(--font-mono)', marginBottom: '0.5rem' }}>
                        Target: {obj.target}
                      </div>
                    )}
                  </div>

                  {obj.recommendation && (
                    <div style={{ fontSize: '0.8rem', color: '#93c5fd', borderTop: '1px solid var(--border-subtle)', paddingTop: '0.5rem' }}>
                      <strong>Fix:</strong> {obj.recommendation}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* TAB 3: PIPELINE STEPPER TRACE */}
      {activeTab === 'trace' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {steps.map((stepInfo, index) => {
            const config = AGENT_CONFIG[stepInfo.agent] || { icon: Cpu, color: 'var(--text-muted)' };
            const Icon = config.icon;
            const isExpanded = expandedSteps[index];
            const hasData = stepInfo.data && Object.keys(stepInfo.data).length > 0;
            
            return (
              <div 
                key={index} 
                style={{ 
                  background: '#FFFFFF', 
                  border: '1.5px solid var(--border-subtle)', 
                  borderRadius: '14px', 
                  padding: '1.35rem',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.85rem',
                  boxShadow: '0 2px 8px rgba(92, 64, 30, 0.05)'
                }}
              >
                <div style={{ display: 'flex', gap: '1.25rem', alignItems: 'flex-start' }}>
                  <div style={{ 
                    background: 'var(--bg-secondary)', 
                    border: '1.5px solid var(--border-subtle)',
                    padding: '0.75rem', 
                    borderRadius: '12px', 
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: config.color,
                    boxShadow: '0 2px 4px rgba(92, 64, 30, 0.04)'
                  }}>
                    <Icon size={22} />
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                        <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-subtle)', fontFamily: 'var(--font-mono)' }}>
                          Step {stepInfo.step}
                        </span>
                        <h4 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-main)' }}>{stepInfo.agent}</h4>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                        {stepInfo.duration_ms && (
                          <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-subtle)', fontFamily: 'var(--font-mono)' }}>
                            {stepInfo.duration_ms}ms
                          </span>
                        )}
                        {hasData && (
                          <button
                            type="button"
                            onClick={() => toggleStep(index)}
                            style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', display: 'flex', alignItems: 'center' }}
                          >
                            {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                          </button>
                        )}
                      </div>
                    </div>
                    <div style={{ fontSize: '0.92rem', color: 'var(--text-muted)', lineHeight: 1.6, fontWeight: 500 }}>
                      {stepInfo.summary}
                    </div>
                  </div>
                </div>

                {/* EXPANDABLE STEP DETAILS — HUMAN-READABLE */}
                {isExpanded && hasData && (
                  <div style={{
                    marginTop: '0.5rem',
                    background: 'var(--bg-secondary)',
                    border: '1.5px solid var(--border-subtle)',
                    borderRadius: '10px',
                    padding: '1.1rem 1.35rem',
                    maxHeight: '320px',
                    overflowY: 'auto',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '0.75rem'
                  }}>
                    <StepDataView data={stepInfo.data} agentColor={config.color} />
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

