import React, { useState, useEffect } from 'react';
import { Sparkles, RefreshCw, AlertCircle, PlayCircle, ShieldCheck } from 'lucide-react';
import Header from './components/Header';
import AgentReport from './components/AgentReport';
import ResultDisplay from './components/ResultDisplay';
import VerdictSummary from './components/VerdictSummary';
import { MultiStepLoader } from './components/ui/multi-step-loader';
import { Button } from './components/ui/moving-border';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const VERIFICATION_LOADING_STATES = [
  { text: "Scanning query for adversarial traps & guardrails" },
  { text: "Planner Agent decomposing task into verification criteria" },
  { text: "Live Research Agent querying web & citation databases" },
  { text: "Extracting atomic factual claims & evidence snippets" },
  { text: "Generator Agent drafting candidate baseline response" },
  { text: "Independent Verifier auditing factual claims against evidence" },
  { text: "Contradiction Engine scanning for cross-source discrepancies" },
  { text: "Adversarial Red-Team Critic attacking candidate answer" },
  { text: "Corrector & Synthesizer assembling final verified audit" },
];

const DEFAULT_BENCHMARKS = [
  {
    id: "bench-1",
    title: "1. Deprecated API",
    query: "Write Python code using LangChain's initialize_agent() with AgentType.ZERO_SHOT_REACT_DESCRIPTION to query a SQL database.",
    desc: "Tests deprecation detection and self-correction."
  },
  {
    id: "bench-2",
    title: "2. Conflicting Sources",
    query: "Exactly how many astronomical units (AU) is Voyager 1 from the Sun right now, and has it completely exited the heliosphere's magnetic influence?",
    desc: "Tests cross-source discrepancy detection."
  },
  {
    id: "bench-3",
    title: "3. Ambiguous Query",
    query: "How do I migrate my primary key column to UUID without table locking downtime?",
    desc: "Tests missing database engine qualification."
  },
  {
    id: "bench-4",
    title: "4. Trick Question",
    query: "In what year was the historic suspension bridge connecting London to New York opened to passenger vehicles?",
    desc: "Tests false premise rejection & red-teaming."
  }
];

export default function App() {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [health, setHealth] = useState(null);
  const [error, setError] = useState(null);
  const [benchmarks, setBenchmarks] = useState(DEFAULT_BENCHMARKS);
  const [activeStepText, setActiveStepText] = useState('');

  useEffect(() => {
    fetch(`${API_BASE}/api/health`)
      .then(res => res.json())
      .then(data => setHealth(data))
      .catch(err => console.warn("Backend not reachable:", err));

    fetch(`${API_BASE}/api/benchmarks`)
      .then(res => res.json())
      .then(data => {
        if (Array.isArray(data) && data.length > 0) {
          setBenchmarks(data.map(b => ({
            id: b.id,
            title: b.category || b.title,
            query: b.query,
            desc: b.description
          })));
        }
      })
      .catch(() => {});
  }, []);

  const handleSelectBenchmark = (benchQuery) => {
    setQuery(benchQuery);
  };

  const handleVerify = async (e, customQuery) => {
    if (e) e.preventDefault();
    const targetQuery = (customQuery || query).trim();
    if (!targetQuery || loading) return;

    setLoading(true);
    setError(null);
    setResult(null);
    setActiveStepText("Step 1/7: Planner Agent decomposing query...");

    // Simulated progress stepper updates while awaiting response
    const timer1 = setTimeout(() => setActiveStepText("Step 2/7: Research Agent retrieving live web evidence..."), 1200);
    const timer2 = setTimeout(() => setActiveStepText("Step 3/7: Generator Agent drafting candidate answer with citations..."), 2800);
    const timer3 = setTimeout(() => setActiveStepText("Step 4/7: Independent Verifier auditing claims against evidence..."), 4500);
    const timer4 = setTimeout(() => setActiveStepText("Step 5/7: Adversarial Red-Team Critic attacking candidate answer..."), 6500);

    try {
      const res = await fetch(`${API_BASE}/api/verify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: targetQuery,
          force_search: true,
          enable_red_team: true
        })
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Verification pipeline encountered an error.');
      }

      const data = await res.json();
      setResult(data);
    } catch (err) {
      console.error(err);
      setError(err.message || 'Failed to complete verification pipeline.');
    } finally {
      clearTimeout(timer1);
      clearTimeout(timer2);
      clearTimeout(timer3);
      clearTimeout(timer4);
      setLoading(false);
      setActiveStepText('');
    }
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Aceternity-style Multi-Step Verification Loader */}
      <MultiStepLoader
        loading={loading}
        loadingStates={VERIFICATION_LOADING_STATES}
        duration={1800}
        loop={true}
        onClose={() => setLoading(false)}
      />

      <Header health={health} />

      <main className="main-content">
        {/* QUERY INPUT PANEL */}
        <div className="glass-panel query-box-container">
          <div>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--accent-red)' }}>
              Multi-Agent Verification Pipeline
            </h2>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
              Submit any complex prompt. The system executes a strict multi-agent loop: <strong>Plan $\rightarrow$ Research $\rightarrow$ Generate $\rightarrow$ Audit $\rightarrow$ Red-Team $\rightarrow$ Correct</strong>.
            </p>
          </div>

          {/* 1-CLICK BENCHMARK TEST SUITE */}
          <div className="benchmark-chips">
            <span className="chip-label">Test Scenarios:</span>
            {benchmarks.map((b) => (
              <button
                key={b.id}
                type="button"
                className="bench-chip"
                title={b.desc}
                onClick={() => {
                  handleSelectBenchmark(b.query);
                }}
              >
                <PlayCircle size={12} style={{ display: 'inline', marginRight: '4px', verticalAlign: '-1px' }} />
                <span>{b.title}</span>
              </button>
            ))}
          </div>

          <form onSubmit={handleVerify} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <Button
              as="div"
              containerClassName="query-input-moving-border"
              className="query-input-inner-wrapper"
              borderRadius="16px"
              duration={8500}
              glowOpacity={0.4}
              blur="10px"
            >
              <textarea
                className="query-input"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="e.g. Write Python code using LangChain's initialize_agent() to query a SQL database..."
                rows={4}
              />
            </Button>

            <div className="query-controls">
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-subtle)', fontSize: '0.8rem' }}>
                <ShieldCheck size={16} style={{ color: 'var(--accent-emerald)' }} />
                <span>Empirical Grounding Active • Adversarial Critic Enabled</span>
              </div>

              <button 
                type="submit" 
                className="btn-primary" 
                disabled={loading || !query.trim()}
              >
                {loading ? (
                  <>
                    <RefreshCw size={16} style={{ animation: 'spin 1s linear infinite' }} />
                    <span>Executing Pipeline...</span>
                  </>
                ) : (
                  <>
                    <Sparkles size={16} />
                    <span>Generate & Verify</span>
                  </>
                )}
              </button>
            </div>
          </form>

          {/* LOADING STEPPER NOTIFICATION */}
          {loading && (
            <div style={{ 
              background: '#FFEED1', 
              border: '1.5px solid var(--border-subtle)', 
              padding: '0.85rem 1.25rem', 
              borderRadius: '12px', 
              color: 'var(--text-main)', 
              display: 'flex', 
              alignItems: 'center', 
              gap: '0.75rem',
              fontSize: '0.9rem',
              boxShadow: '0 2px 6px rgba(92, 64, 30, 0.05)'
            }}>
              <div className="pulse-dot" style={{ background: 'var(--accent-red)' }} />
              <span style={{ fontWeight: 700 }}>{activeStepText || "Executing Multi-Agent Verification..."}</span>
            </div>
          )}

          {error && (
            <div style={{ 
              background: '#FFF1F2', 
              border: '1.5px solid #FECDD3', 
              padding: '0.85rem 1.25rem', 
              borderRadius: '10px', 
              color: '#9F1239', 
              display: 'flex', 
              alignItems: 'center', 
              gap: '0.6rem', 
              fontSize: '0.9rem',
              fontWeight: 600,
              boxShadow: '0 2px 6px rgba(159, 18, 57, 0.06)'
            }}>
              <AlertCircle size={18} style={{ color: '#E11D48' }} />
              <span>{error}</span>
            </div>
          )}
        </div>

        {/* RESULTS SECTION */}
        {result && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
            <ResultDisplay result={result} />
            <VerdictSummary result={result} />
            <AgentReport result={result} />
          </div>
        )}
      </main>

      <footer style={{ marginTop: 'auto', padding: '1.5rem', textAlign: 'center', borderTop: '1.5px solid var(--border-subtle)', background: 'rgba(255, 250, 243, 0.8)', color: 'var(--text-subtle)', fontSize: '0.82rem', fontWeight: 600 }}>
        HackFusion 2026: Multi-Agent AI Verification Platform • 100% Free-Tier Architecture
      </footer>
    </div>
  );
}

