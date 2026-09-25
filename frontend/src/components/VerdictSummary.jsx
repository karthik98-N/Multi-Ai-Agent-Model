import React from 'react';
import { CheckCircle2, XCircle, AlertTriangle, ChevronRight } from 'lucide-react';

const VERDICT_COLORS = {
  ACCEPT:  { border: '#86EFAC', bg: '#F0FDF4', icon: CheckCircle2,  iconColor: '#059669', label: 'ACCEPTED' },
  REJECT:  { border: '#FECDD3', bg: '#FFF1F2', icon: XCircle,       iconColor: '#E11D48', label: 'REJECTED' },
  REVISE:  { border: '#FDE68A', bg: '#FFFBEB', icon: AlertTriangle, iconColor: '#D97706', label: 'CORRECTED' },
};

// Detect the kind of line for colour-coding
function classifyLine(line) {
  const l = line.toLowerCase();
  if (l.startsWith('verdict:'))            return 'verdict';
  if (l.startsWith('overall confidence:')) return 'confidence';
  if (l.startsWith('input warning:') || l.includes('adversarial signal')) return 'warning';
  if (l.startsWith('input check:'))       return 'ok';
  if (l.startsWith('  confirmed:'))       return 'confirmed';
  if (l.startsWith('  contradicted:') || l.startsWith('  unverifiable:')) return 'failed';
  if (l.startsWith('  conflict:'))        return 'conflict';
  if (l.startsWith('  issue:'))           return 'issue';
  if (l.startsWith('red-team critic:') && l.includes('no objection')) return 'ok';
  if (l.startsWith('red-team critic:'))   return 'warning';
  if (l.startsWith('source conflicts:') && l.includes('no contradiction')) return 'ok';
  if (l.startsWith('source conflicts:'))  return 'warning';
  if (l.startsWith('ambiguity:') && l.includes('all claims')) return 'ok';
  if (l.startsWith('ambiguity:'))         return 'warning';
  if (l.startsWith('claims checked:'))    return 'info';
  return 'info';
}

const LINE_STYLES = {
  verdict:    { color: '#141312',  fontWeight: 800, fontSize: '1.05rem' },
  confidence: { color: '#4338CA',  fontWeight: 700 },
  warning:    { color: '#B45309',  fontWeight: 600 },
  ok:         { color: '#047857',  fontWeight: 600 },
  confirmed:  { color: '#065F46',  paddingLeft: '1rem', fontSize: '0.88rem', fontWeight: 600 },
  failed:     { color: '#BE123C',  paddingLeft: '1rem', fontSize: '0.88rem', fontWeight: 600 },
  conflict:   { color: '#C2410C',  paddingLeft: '1rem', fontSize: '0.88rem', fontWeight: 600 },
  issue:      { color: '#B91C1C',  paddingLeft: '1rem', fontSize: '0.88rem', fontWeight: 600 },
  info:       { color: '#3D3935',  fontWeight: 500 },
};

const LINE_ICONS = {
  verdict:    null,
  confidence: null,
  warning:    '⚠',
  ok:         '✓',
  confirmed:  '✓',
  failed:     '✗',
  conflict:   '⚔',
  issue:      '!',
  info:       '·',
};

export default function VerdictSummary({ result }) {
  if (!result || !result.verdict_lines || result.verdict_lines.length === 0) return null;

  const decision = result.decision || 'ACCEPT';
  const cfg = VERDICT_COLORS[decision] || VERDICT_COLORS.ACCEPT;
  const Icon = cfg.icon;

  return (
    <div style={{
      background: cfg.bg,
      border: `1.5px solid ${cfg.border}`,
      borderRadius: '16px',
      padding: '1.75rem 2rem',
      display: 'flex',
      flexDirection: 'column',
      gap: '1.25rem',
      boxShadow: 'var(--card-shadow)',
    }}>

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <div style={{
          background: 'var(--bg-secondary)',
          border: '1.5px solid var(--border-subtle)',
          borderRadius: '12px',
          padding: '0.65rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 2px 4px rgba(92, 64, 30, 0.05)',
        }}>
          <Icon size={28} style={{ color: cfg.iconColor }} />
        </div>
        <div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--text-main)', margin: 0 }}>
            Final Analysis Summary
          </h2>
          <p style={{ fontSize: '0.82rem', color: 'var(--text-subtle)', margin: 0, marginTop: '0.15rem', fontWeight: 500 }}>
            Synthesised from {result.steps_trace?.length || 0} agent steps across {result.iteration_count || 1} verification cycle(s)
          </p>
        </div>

        <span style={{
          marginLeft: 'auto',
          fontSize: '0.78rem',
          fontWeight: 800,
          letterSpacing: '0.08em',
          padding: '0.35rem 0.95rem',
          borderRadius: '8px',
          background: 'var(--bg-secondary)',
          border: `1.5px solid ${cfg.border}`,
          color: cfg.iconColor,
          textTransform: 'uppercase',
          boxShadow: '0 2px 4px rgba(92, 64, 30, 0.06)',
        }}>
          {cfg.label}
        </span>
      </div>

      {/* Divider */}
      <div style={{ height: 1.5, background: 'var(--border-subtle)' }} />

      {/* Verdict lines */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.55rem' }}>
        {result.verdict_lines.map((line, idx) => {
          const type  = classifyLine(line);
          const style = LINE_STYLES[type] || LINE_STYLES.info;
          const icon  = LINE_ICONS[type];
          const isIndented = line.startsWith('  ');

          return (
            <div
              key={idx}
              style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: '0.5rem',
                paddingLeft: isIndented ? '1.25rem' : 0,
                lineHeight: 1.6,
              }}
            >
              {/* Leading icon / bullet */}
              <span style={{
                flexShrink: 0,
                fontSize: '0.8rem',
                fontWeight: 700,
                marginTop: '0.15rem',
                width: '1rem',
                textAlign: 'center',
                color: style.color,
                opacity: 0.8,
              }}>
                {icon || <ChevronRight size={12} style={{ color: style.color }} />}
              </span>

              {/* Line text */}
              <span style={{
                fontSize: style.fontSize || '0.9rem',
                fontWeight: style.fontWeight || 400,
                color: style.color,
                letterSpacing: '0.01em',
              }}>
                {line.replace(/^\s+/, '')}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
