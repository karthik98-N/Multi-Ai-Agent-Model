import React, { useState } from 'react';
import {
  CheckCircle, AlertTriangle, XCircle, ExternalLink,
  Columns, FileText, Award, ShieldAlert, Shield,
  Activity, AlertOctagon, ThumbsUp, ThumbsDown
} from 'lucide-react';

// ── Confidence colour map (Harmonised with ColorHunt Palette) ────────────────
const CONF_COLORS = {
  HIGH:         { text: '#059669', bg: '#DCFCE7', border: '#86EFAC' },
  MEDIUM:       { text: '#D97706', bg: '#FEF3C7', border: '#FCD34D' },
  LOW:          { text: '#EA580C', bg: '#FFEDD5', border: '#FDBA74' },
  INSUFFICIENT: { text: '#E11D48', bg: '#FFE4E6', border: '#FDA4AF' },
};

const GUARD_COLORS = {
  NONE:     null,
  LOW:      { text: '#B45309', bg: '#FFFBEB', border: '#FDE68A', icon: Shield },
  MEDIUM:   { text: '#C2410C', bg: '#FFF7ED', border: '#FFEDD5', icon: AlertTriangle },
  HIGH:     { text: '#B91C1C', bg: '#FEF2F2', border: '#FECDD3', icon: ShieldAlert },
  CRITICAL: { text: '#9F1239', bg: '#FFF1F2', border: '#FFE4E6', icon: AlertOctagon },
};

function CredibilityDot({ score }) {
  const color = score >= 0.7 ? '#34d399' : score >= 0.45 ? '#fbbf24' : '#f87171';
  const label = score >= 0.7 ? 'High trust' : score >= 0.45 ? 'Medium trust' : 'Low trust';
  return (
    <span title={`Source credibility: ${label} (${Math.round(score * 100)}%)`}
      style={{
        display: 'inline-block', width: 8, height: 8,
        borderRadius: '50%', background: color,
        boxShadow: `0 0 4px ${color}80`
      }}
    />
  );
}

function FeedbackWidget({ result }) {
  const [status, setStatus] = useState('idle'); // idle, giving_negative, submitting, submitted
  const [feedbackTags, setFeedbackTags] = useState([]);
  const [userCorrection, setUserCorrection] = useState('');

  const submitFeedback = async (type) => {
    setStatus('submitting');
    try {
      await fetch('http://localhost:8000/api/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: result.query || 'unknown',
          raw_answer: result.raw_unverified_answer || '',
          verified_answer: result.final_answer || result.verified_answer || '',
          feedback_type: type,
          feedback_tags: feedbackTags,
          user_correction: userCorrection
        })
      });
      setStatus('submitted');
    } catch (e) {
      console.error(e);
      setStatus('idle');
    }
  };

  if (status === 'submitted') {
    return <div style={{ color: '#059669', fontSize: '0.85rem', fontWeight: 600, marginTop: '1rem' }}>Thank you! Your feedback helps fine-tune our agents.</div>;
  }

  return (
    <div style={{ marginTop: '1.25rem', borderTop: '1.5px solid var(--border-subtle)', paddingTop: '1rem' }}>
      {status === 'idle' && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)', fontWeight: 600 }}>Rate this verification:</span>
          <button 
            onClick={() => submitFeedback(1)} 
            style={{ 
              background: '#DCFCE7', 
              border: '1.5px solid #86EFAC', 
              borderRadius: '8px', 
              padding: '0.45rem 0.85rem', 
              color: '#065F46', 
              fontWeight: 700,
              cursor: 'pointer', 
              display: 'flex', 
              alignItems: 'center', 
              gap: '0.4rem', 
              fontSize: '0.82rem',
              boxShadow: '0 2px 0 #BBF7D0'
            }}
          >
            <ThumbsUp size={14} style={{ color: '#059669' }} /> Good
          </button>
          <button 
            onClick={() => setStatus('giving_negative')} 
            style={{ 
              background: '#FFE4E6', 
              border: '1.5px solid #FDA4AF', 
              borderRadius: '8px', 
              padding: '0.45rem 0.85rem', 
              color: '#9F1239', 
              fontWeight: 700,
              cursor: 'pointer', 
              display: 'flex', 
              alignItems: 'center', 
              gap: '0.4rem', 
              fontSize: '0.82rem',
              boxShadow: '0 2px 0 #FECDD3'
            }}
          >
            <ThumbsDown size={14} style={{ color: '#E11D48' }} /> Inaccurate
          </button>
        </div>
      )}
      
      {status === 'giving_negative' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem', background: 'var(--bg-secondary)', border: '1.5px solid var(--border-subtle)', padding: '1.25rem', borderRadius: '12px', boxShadow: '0 2px 8px rgba(92, 64, 30, 0.05)' }}>
          <span style={{ fontSize: '0.88rem', color: 'var(--accent-red)', fontWeight: 700 }}>What went wrong?</span>
          <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
            {['Hallucination', 'Missed Contradiction', 'Formatting Issue', 'Bad Logic'].map(tag => (
              <button 
                key={tag} 
                onClick={() => setFeedbackTags(prev => prev.includes(tag) ? prev.filter(t => t !== tag) : [...prev, tag])} 
                style={{ 
                  background: feedbackTags.includes(tag) ? '#FFE4E6' : '#FFFFFF', 
                  border: `1.5px solid ${feedbackTags.includes(tag) ? 'var(--accent-red)' : 'var(--border-subtle)'}`, 
                  borderRadius: '16px', 
                  padding: '0.3rem 0.8rem', 
                  fontSize: '0.78rem', 
                  fontWeight: 600,
                  color: feedbackTags.includes(tag) ? 'var(--accent-red)' : 'var(--text-main)', 
                  cursor: 'pointer', 
                  transition: 'all 0.2s',
                  boxShadow: '0 1px 3px rgba(0, 0, 0, 0.04)'
                }}
              >
                {tag}
              </button>
            ))}
          </div>
          <textarea 
            placeholder="What should the agent have said? (Optional)" 
            value={userCorrection} 
            onChange={e => setUserCorrection(e.target.value)} 
            style={{ width: '100%', background: '#FFFFFF', border: '1.5px solid var(--border-subtle)', borderRadius: '8px', padding: '0.75rem', color: 'var(--text-main)', fontSize: '0.88rem', minHeight: '80px', marginTop: '0.5rem', resize: 'vertical' }} 
          />
          <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end', marginTop: '0.5rem' }}>
            <button onClick={() => setStatus('idle')} style={{ background: 'none', border: 'none', color: 'var(--text-subtle)', cursor: 'pointer', fontSize: '0.85rem', fontWeight: 600, padding: '0.4rem 0.8rem' }}>Cancel</button>
            <button onClick={() => submitFeedback(-1)} className="btn-primary" style={{ padding: '0.5rem 1.25rem', fontSize: '0.85rem' }}>Submit Feedback</button>
          </div>
        </div>
      )}
    </div>
  );
}

function ConfidenceBreakdown({ breakdown }) {
  if (!breakdown) return null;
  const bars = [
    { key: 'factual',     label: 'Factual Grounding' },
    { key: 'source',      label: 'Source Credibility' },
    { key: 'consistency', label: 'Consistency' },
    { key: 'critic',      label: 'Critic Clearance' },
  ];
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginTop: '0.75rem' }}>
      {bars.map(({ key, label }) => {
        const val = breakdown[key] ?? 0;
        const color = val >= 70 ? '#34d399' : val >= 45 ? '#fbbf24' : '#f87171';
        return (
          <div key={key}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: '#94a3b8', marginBottom: '0.2rem' }}>
              <span>{label}</span>
              <span style={{ color, fontWeight: 700 }}>{val.toFixed(0)}</span>
            </div>
            <div style={{ height: 4, background: 'rgba(255,255,255,0.07)', borderRadius: 4, overflow: 'hidden' }}>
              <div style={{ height: '100%', width: `${val}%`, background: color, borderRadius: 4, transition: 'width 0.6s ease' }} />
            </div>
          </div>
        );
      })}
    </div>
  );
}

// Format and sanitize text into clean, normal readable paragraphs
// Strips tables, pipes, asterisks (** or *), markdown headers, dividers (---), citations, and bibliography
function renderNormalText(text) {
  if (!text) return null;

  // Replace any {"contradictions": []} or similar json with [verified successfully]
  let cleaned = String(text)
    .replace(/\{"contradictions":\s*\[\]\}/gi, '[verified successfully]')
    .replace(/^([^\n]*Confidence:[^\n]*\n+)?(\*[^\n]*\*\n+)?(---+\s*\n+)?/gi, '')
    .trim();

  if (
    cleaned === '[verified successfully]' ||
    cleaned === '{"contradictions": []}' ||
    cleaned === '{"contradictions":[]}' ||
    cleaned.replace(/\s+/g, '') === '{"contradictions":[]}'
  ) {
    return (
      <div style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '0.5rem',
        padding: '0.45rem 0.95rem',
        background: 'rgba(16, 185, 129, 0.12)',
        border: '1px solid rgba(16, 185, 129, 0.35)',
        borderRadius: '8px',
        color: '#34d399',
        fontWeight: 600,
        fontSize: '0.96rem'
      }}>
        <CheckCircle size={17} style={{ color: '#34d399' }} />
        <span>[verified successfully]</span>
      </div>
    );
  }

  // 2. Remove trailing references / sources / bibliography block
  cleaned = cleaned.replace(/\n+\s*(?:references?|sources?|citations?|evidence cited|evidence pool)\s*:?[\s\S]*$/i, '');

  // 3. Remove conversational sign-offs at the end
  cleaned = cleaned.replace(/\n*(?:if you (?:need|have|require)|let me know|feel free to|please let me know)[\s\S]*$/i, '');

  // 4. Remove inline citation tags like [REF-1], [REF-1, REF-2], (REF-1), etc.
  cleaned = cleaned
    .replace(/\[\s*REF[-\s]?\w+(?:\s*,\s*REF[-\s]?\w+)*\s*\]/gi, '')
    .replace(/\(\s*REF[-\s]?\w+(?:\s*,\s*REF[-\s]?\w+)*\s*\)/gi, '')
    .replace(/\[\s*REF[^\s\]]*\s*\]/gi, '')
    .replace(/(?<=\s)\[\d+(?:\s*,\s*\d+)*\]/g, '');

  // 5. Convert markdown tables into plain flowing sentences
  const lines = cleaned.split('\n');
  const newLines = [];
  let tableRows = [];

  for (let line of lines) {
    const stripped = line.trim();
    if (stripped.startsWith('|') && stripped.endsWith('|')) {
      if (/^\|[\s\-:|]+\|$/.test(stripped)) continue;
      const cells = stripped.slice(1, -1).split('|').map(c => c.trim());
      const firstCell = (cells[0] || '').toLowerCase();
      if (['source', 'item', 'claim', 'parameter', 'name', 'field', 'id', 'key'].some(h => firstCell.includes(h))) continue;
      if (cells.length >= 2) {
        const col1 = cells[0].replace(/[*_#]/g, '').trim();
        const col2 = cells[1].replace(/[*_#]/g, '').trim();
        if (col1 && col2) tableRows.push(col1 + ': ' + col2);
        else if (col2) tableRows.push(col2);
      } else if (cells.length === 1) {
        tableRows.push(cells[0].replace(/[*_#]/g, '').trim());
      }
    } else {
      if (tableRows.length > 0) {
        newLines.push(tableRows.map(r => /[.!?]$/.test(r) ? r : r + '.').join(' '));
        newLines.push('');
        tableRows = [];
      }
      newLines.push(line);
    }
  }

  if (tableRows.length > 0) {
    newLines.push(tableRows.map(r => /[.!?]$/.test(r) ? r : r + '.').join(' '));
    newLines.push('');
  }

  cleaned = newLines.join('\n');

  // 6. Remove horizontal rules (---, ___, ***)
  cleaned = cleaned.replace(/^\s*[-*_]{3,}\s*$/gm, '');

  // 7. Remove markdown headers (#, ##, ###)
  cleaned = cleaned.replace(/^\s*#{1,6}\s*(.+)$/gm, '\n\n$1:\n\n');

  // 8. Remove asterisks (*, **, ***) and underscores (_, __, ___)
  cleaned = cleaned.replace(/\*{1,3}(.*?)\*{1,3}/g, '$1');
  cleaned = cleaned.replace(/_{1,3}(.*?)_{1,3}/g, '$1');

  // 9. Remove list markers (e.g. '1. ', '2. ', '- ', '* ', '• ')
  cleaned = cleaned.replace(/^\s*(?:\d+[\.\)]|[-*•])\s+/gm, '');

  // 10. Remove remaining pipes or backticks
  cleaned = cleaned.replace(/\|/g, '').replace(/`/g, '');

  // 11. Clean up spacing before punctuation and multiple spaces
  cleaned = cleaned
    .replace(/\s+([.,;:!?])/g, '$1')
    .replace(/:\s*([.,;])/g, '$1')
    .replace(/\.{2,}/g, '.')
    .replace(/[ \t]{2,}/g, ' ')
    .trim();

  // 12. Split by double newlines into clean normal paragraphs and merge short labels with next paragraph
  const rawParas = cleaned
    .split(/\n\s*\n/)
    .map(p => p.replace(/\s*\n\s*/g, ' ').trim())
    .filter(p => p.length > 0);

  const merged = [];
  for (let i = 0; i < rawParas.length; i++) {
    if (rawParas[i].endsWith(':') && rawParas[i].length < 60 && i + 1 < rawParas.length) {
      merged.push(`${rawParas[i]} ${rawParas[i + 1]}`);
      i++;
    } else {
      merged.push(rawParas[i]);
    }
  }

  if (merged.length === 0) {
    return <div>{cleaned}</div>;
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      {merged.map((para, i) => {
        if (
          para.trim() === '[verified successfully]' ||
          para.trim() === '{"contradictions": []}' ||
          para.trim() === '{"contradictions":[]}' ||
          para.trim().includes('{"contradictions":')
        ) {
          return (
            <div key={i} style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.5rem',
              padding: '0.45rem 0.95rem',
              background: '#DCFCE7',
              border: '1.5px solid #86EFAC',
              borderRadius: '8px',
              color: '#065F46',
              fontWeight: 700,
              fontSize: '0.94rem'
            }}>
              <CheckCircle size={17} style={{ color: '#059669' }} />
              <span>[verified successfully]</span>
            </div>
          );
        }
        return (
          <p key={i} style={{ margin: 0, lineHeight: '1.75', fontSize: '0.98rem', color: 'var(--text-main)' }}>
            {para}
          </p>
        );
      })}
    </div>
  );
}

export default function ResultDisplay({ result }) {
  const [showComparison, setShowComparison]       = useState(true);
  const [showBreakdown,  setShowBreakdown]        = useState(false);

  if (!result || !result.final_answer) return null;

  const decision          = result.decision || 'ACCEPT';
  const confidence        = result.confidence_score !== undefined ? result.confidence_score : 100;
  const confLabel         = result.confidence_label || (confidence >= 80 ? 'HIGH' : confidence >= 60 ? 'MEDIUM' : 'LOW');
  const confColors        = CONF_COLORS[confLabel] || CONF_COLORS.MEDIUM;
  const guardRisk         = result.guard_risk_level || 'NONE';
  const guardSignals      = result.guard_signals || [];
  const guardCfg          = GUARD_COLORS[guardRisk];
  const isAmbiguous       = result.is_ambiguous;
  const ambiguitySummary  = result.ambiguity_summary || '';
  const isAccepted        = decision === 'ACCEPT';
  const isRejected        = decision === 'REJECT';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>

      {/* ── GUARD WARNING (when input was suspicious) ────────────────── */}
      {guardCfg && guardSignals.length > 0 && (
        <div style={{
          background: guardCfg.bg,
          border: `1px solid ${guardCfg.border}`,
          borderRadius: '12px',
          padding: '1rem 1.25rem',
          display: 'flex',
          alignItems: 'flex-start',
          gap: '0.75rem'
        }}>
          <guardCfg.icon size={20} style={{ color: guardCfg.text, flexShrink: 0, marginTop: 2 }} />
          <div>
            <div style={{ fontSize: '0.82rem', fontWeight: 700, color: guardCfg.text, marginBottom: '0.25rem' }}>
              Input Risk: {guardRisk} — Query triggered adversarial-input signals
            </div>
            <ul style={{ margin: 0, paddingLeft: '1.2rem', fontSize: '0.78rem', color: '#94a3b8' }}>
              {guardSignals.map((s, i) => <li key={i}>{s}</li>)}
            </ul>
          </div>
        </div>
      )}

      {/* ── AMBIGUITY ALERT ──────────────────────────────────────────── */}
      {isAmbiguous && (
        <div style={{
          background: 'rgba(251,191,36,0.08)',
          border: '1px solid rgba(251,191,36,0.25)',
          borderRadius: '12px',
          padding: '0.9rem 1.25rem',
          display: 'flex',
          alignItems: 'flex-start',
          gap: '0.75rem'
        }}>
          <Activity size={18} style={{ color: '#fbbf24', flexShrink: 0, marginTop: 2 }} />
          <div>
            <div style={{ fontSize: '0.82rem', fontWeight: 700, color: '#fbbf24', marginBottom: '0.2rem' }}>
              Ambiguous or Conflicting Information Detected
            </div>
            <div style={{ fontSize: '0.78rem', color: '#94a3b8' }}>{ambiguitySummary}</div>
          </div>
        </div>
      )}

      {/* ── DECISION & CONFIDENCE BANNER ─────────────────────────────── */}
      <div className={`decision-banner ${decision}`}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          {isAccepted
            ? <CheckCircle size={36} style={{ color: 'var(--accent-emerald)' }} />
            : isRejected
            ? <XCircle size={36} style={{ color: 'var(--accent-rose)' }} />
            : <AlertTriangle size={36} style={{ color: 'var(--accent-amber)' }} />}
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.25rem' }}>
              <span className={`decision-badge ${decision}`}>{decision}</span>
              <span style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>
                {result.iteration_count ? `${result.iteration_count} verification cycle(s)` : '1 cycle'}
              </span>
            </div>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
              {isAccepted
                ? 'Atomic claims grounded in empirical evidence. Passed adversarial red-team audit.'
                : isRejected
                ? 'Rejected — critical evidence conflict or insufficient information to produce a reliable answer.'
                : 'Audited and refined through multi-agent correction loops.'}
            </p>
          </div>
        </div>

        {/* Confidence score panel */}
        <div style={{
          display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '0.35rem',
          background: 'var(--bg-secondary)', padding: '0.85rem 1.35rem',
          borderRadius: '12px', border: '1.5px solid var(--border-subtle)', minWidth: 160,
          boxShadow: '0 2px 6px rgba(92, 64, 30, 0.05)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'var(--text-main)', fontSize: '0.82rem', fontWeight: 700 }}>
            <Award size={15} style={{ color: 'var(--accent-red)' }} />
            <span>Trust Score</span>
          </div>
          <div style={{ fontSize: '1.55rem', fontWeight: 800, color: confColors.text, fontFamily: 'var(--font-mono)' }}>
            {confidence.toFixed(1)}%
          </div>
          <span style={{
            fontSize: '0.72rem', fontWeight: 800, letterSpacing: '0.08em',
            padding: '0.18rem 0.6rem', borderRadius: 6,
            background: confColors.bg, border: `1.5px solid ${confColors.border}`,
            color: confColors.text
          }}>{confLabel}</span>
          <button
            type="button"
            onClick={() => setShowBreakdown(b => !b)}
            style={{ fontSize: '0.74rem', fontWeight: 600, color: 'var(--text-muted)', background: 'none', border: 'none', cursor: 'pointer', marginTop: '0.3rem' }}
          >
            {showBreakdown ? 'Hide breakdown ▲' : 'See breakdown ▼'}
          </button>
        </div>
      </div>

      {/* ── CONFIDENCE BREAKDOWN BAR CHART ───────────────────────────── */}
      {showBreakdown && result.confidence_breakdown && (
        <div style={{
          background: 'var(--bg-secondary)', border: '1.5px solid var(--border-subtle)',
          borderRadius: '14px', padding: '1.35rem 1.6rem',
          boxShadow: 'var(--card-shadow)'
        }}>
          <div style={{ fontSize: '0.85rem', fontWeight: 800, color: 'var(--text-main)', marginBottom: '0.6rem' }}>
            Confidence Sub-scores
          </div>
          <ConfidenceBreakdown breakdown={result.confidence_breakdown} />
          {result.confidence_breakdown.explanation && (
            <div style={{ marginTop: '0.85rem', fontSize: '0.78rem', color: 'var(--text-muted)', fontStyle: 'italic', fontWeight: 500 }}>
              {result.confidence_breakdown.explanation}
            </div>
          )}
        </div>
      )}

      {/* ── VIEW TOGGLE ───────────────────────────────────────────────── */}
      {result.raw_unverified_answer && (
        <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
          <button
            type="button" className="bench-chip"
            onClick={() => setShowComparison(!showComparison)}
            style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: showComparison ? 'rgba(99,102,241,0.2)' : undefined }}
          >
            <Columns size={14} />
            <span>{showComparison ? 'Single Verified View' : 'Side-by-Side Comparison'}</span>
          </button>
        </div>
      )}

      {/* ── ANSWER PANELS ─────────────────────────────────────────────── */}
      {showComparison && result.raw_unverified_answer ? (
        <div className="comparison-grid">
          <div className="glass-panel column-card" style={{ borderLeft: '4px solid var(--accent-rose)' }}>
            <div className="column-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <AlertTriangle size={18} style={{ color: 'var(--accent-rose)' }} />
                <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#fca5a5' }}>Raw Baseline AI Output</h3>
              </div>
              <span className="severity-pill CRITICAL">UNVERIFIED</span>
            </div>
            <div className="hallucination-alert">
              Standard single-pass output — may contain hallucinated APIs, dates, or false assumptions.
            </div>
            <div className="answer-body">{renderNormalText(result.raw_unverified_answer)}</div>
          </div>

          <div className="glass-panel column-card" style={{ borderLeft: '4px solid var(--accent-emerald)' }}>
            <div className="column-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <CheckCircle size={18} style={{ color: 'var(--accent-emerald)' }} />
                <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#6ee7b7' }}>Verified Multi-Agent Answer</h3>
              </div>
              <span className="severity-pill LOW" style={{ background: 'rgba(16,185,129,0.2)', color: '#34d399' }}>
                GROUNDED & AUDITED
              </span>
            </div>
            <div className="answer-body">{renderNormalText(result.final_answer || result.verified_answer)}</div>
            <FeedbackWidget result={result} />
          </div>
        </div>
      ) : (
        <div className="glass-panel column-card" style={{ borderLeft: '4px solid var(--accent-emerald)', padding: '1.75rem' }}>
          <div className="column-header" style={{ marginBottom: '1.25rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <CheckCircle size={20} style={{ color: 'var(--accent-emerald)' }} />
              <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: '#6ee7b7' }}>Verified Multi-Agent Answer</h3>
            </div>
            <span className="severity-pill LOW" style={{ background: 'rgba(16,185,129,0.2)', color: '#34d399' }}>
              GROUNDED & AUDITED
            </span>
          </div>
          <div className="answer-body">{renderNormalText(result.final_answer || result.verified_answer)}</div>
          <FeedbackWidget result={result} />
        </div>
      )}

      {/* ── EVIDENCE REFERENCES ───────────────────────────────────────── */}
      {result.evidence_pool && result.evidence_pool.length > 0 && (
        <div className="glass-panel" style={{ padding: '1.75rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
            <FileText size={18} style={{ color: 'var(--accent-red)' }} />
            <h3 style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--text-main)' }}>
              Empirical Evidence References ({result.evidence_pool.length})
            </h3>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '0.95rem' }}>
            {result.evidence_pool.map((e, idx) => {
              const credScore = result.confidence_breakdown?.source
                ? result.confidence_breakdown.source / 100
                : 0.6;
              return (
                <div key={idx} style={{
                  background: '#FFFFFF', border: '1.5px solid var(--border-subtle)',
                  borderRadius: '12px', padding: '1.15rem',
                  display: 'flex', flexDirection: 'column', gap: '0.55rem',
                  boxShadow: '0 2px 6px rgba(92, 64, 30, 0.04)'
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <span className="ref-pill">{e.id}</span>
                      <CredibilityDot score={credScore} />
                    </div>
                    {e.url && (
                      <a href={e.url} target="_blank" rel="noopener noreferrer"
                        style={{ color: 'var(--accent-red)', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.25rem', fontSize: '0.78rem', textDecoration: 'none' }}>
                        <span>Source</span>
                        <ExternalLink size={12} />
                      </a>
                    )}
                  </div>
                  <div style={{ fontSize: '0.92rem', fontWeight: 700, color: 'var(--text-main)' }}>{e.title}</div>
                  <div style={{ fontSize: '0.84rem', color: 'var(--text-muted)', lineHeight: 1.6, maxHeight: '80px', overflowY: 'auto' }}>
                    {e.snippet}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
