import React, { useState, useEffect } from "react";

// Authentic Tabler IconSquareRoundedX SVG representation (zero external dependency)
export function IconSquareRoundedX({ className = "", size = 36, ...props }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.75"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      {...props}
    >
      <path stroke="none" d="M0 0h24v24H0z" fill="none" />
      <path d="M10 10l4 4m0 -4l-4 4" />
      <path d="M12 3c7.2 0 9 1.8 9 9s-1.8 9 -9 9s-9 -1.8 -9 -9s1.8 -9 9 -9z" />
    </svg>
  );
}

// Aceternity Check Outline Icon
const CheckOutline = ({ className = "" }) => {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
      strokeWidth={1.5}
      stroke="currentColor"
      width={24}
      height={24}
      className={className}
    >
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
    </svg>
  );
};

// Aceternity Filled Check Icon
const CheckFilled = ({ className = "" }) => {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="currentColor"
      width={24}
      height={24}
      className={className}
    >
      <path
        fillRule="evenodd"
        d="M2.25 12c0-5.385 4.365-9.75 9.75-9.75s9.75 4.365 9.75 9.75-4.365 9.75-9.75 9.75S2.25 17.385 2.25 12Zm13.36-1.814a.75.75 0 1 0-1.22-.872l-3.236 4.53L9.53 12.22a.75.75 0 0 0-1.06 1.06l2.25 2.25a.75.75 0 0 0 1.14-.094l3.75-5.25Z"
        clipRule="evenodd"
      />
    </svg>
  );
};

export const defaultLoadingStates = [
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

/**
 * Aceternity-style MultiStepLoader component.
 * Displays an animated multi-step progression modal during pipeline execution.
 */
export function MultiStepLoader({
  loadingStates = defaultLoadingStates,
  loading = false,
  duration = 2000,
  loop = true,
  onClose,
}) {
  const [currentState, setCurrentState] = useState(0);

  useEffect(() => {
    if (!loading) {
      setCurrentState(0);
      return;
    }

    const interval = setInterval(() => {
      setCurrentState((prev) => {
        if (prev >= loadingStates.length - 1) {
          return loop ? 0 : prev;
        }
        return prev + 1;
      });
    }, duration);

    return () => clearInterval(interval);
  }, [loading, loadingStates.length, duration, loop]);

  if (!loading) return null;

  const itemHeight = 52;
  const containerHeight = 320;
  // Center the active item within containerHeight
  const offset = containerHeight / 2 - currentState * itemHeight - itemHeight / 2;

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 1000,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        backgroundColor: "rgba(255, 250, 243, 0.94)",
        backdropFilter: "blur(20px)",
        WebkitBackdropFilter: "blur(20px)",
        padding: "1rem",
        animation: "fadeIn 0.3s ease-out",
      }}
    >
      {/* Ambient background glow */}
      <div
        style={{
          position: "absolute",
          width: "550px",
          height: "550px",
          background: "radial-gradient(circle, rgba(255, 229, 191, 0.7) 0%, rgba(246, 36, 64, 0.12) 40%, transparent 70%)",
          borderRadius: "50%",
          pointerEvents: "none",
          filter: "blur(40px)",
        }}
      />

      {/* Top right close button */}
      {onClose && (
        <button
          onClick={onClose}
          type="button"
          aria-label="Close loader"
          style={{
            position: "fixed",
            top: "1.5rem",
            right: "1.5rem",
            zIndex: 1010,
            background: "#FFF2DB",
            border: "1.5px solid #FFE5BF",
            borderRadius: "10px",
            color: "#141312",
            cursor: "pointer",
            padding: "0.45rem",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            boxShadow: "0 2px 8px rgba(92, 64, 30, 0.08)",
            transition: "all 0.2s ease",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = "#FFEED1";
            e.currentTarget.style.borderColor = "#F62440";
            e.currentTarget.style.color = "#F62440";
            e.currentTarget.style.transform = "scale(1.05)";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = "#FFF2DB";
            e.currentTarget.style.borderColor = "#FFE5BF";
            e.currentTarget.style.color = "#141312";
            e.currentTarget.style.transform = "scale(1)";
          }}
        >
          <IconSquareRoundedX size={32} />
        </button>
      )}

      {/* Pipeline Status Tag */}
      <div style={{ marginBottom: "2rem", textAlign: "center", zIndex: 10 }}>
        <div
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "0.5rem",
            padding: "0.4rem 1rem",
            borderRadius: "999px",
            background: "#FFF2DB",
            border: "1.5px solid #FFE5BF",
            color: "#F62440",
            fontSize: "0.78rem",
            fontWeight: 800,
            letterSpacing: "0.08em",
            textTransform: "uppercase",
            marginBottom: "0.75rem",
            boxShadow: "0 2px 6px rgba(92, 64, 30, 0.06)",
          }}
        >
          <span
            style={{
              width: "8px",
              height: "8px",
              borderRadius: "50%",
              background: "#F62440",
              boxShadow: "0 0 8px #F62440",
              animation: "pulse 1.5s infinite",
            }}
          />
          Multi-Agent Verification In Progress
        </div>
        <div style={{ fontSize: "0.88rem", fontWeight: 600, color: "var(--text-muted)" }}>
          Step {currentState + 1} of {loadingStates.length}
        </div>
      </div>

      {/* Main Steps Window with gradient masks */}
      <div
        style={{
          position: "relative",
          width: "100%",
          maxWidth: "640px",
          height: `${containerHeight}px`,
          overflow: "hidden",
          zIndex: 10,
          maskImage: "linear-gradient(to bottom, transparent 0%, black 22%, black 78%, transparent 100%)",
          WebkitMaskImage: "linear-gradient(to bottom, transparent 0%, black 22%, black 78%, transparent 100%)",
        }}
      >
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            transform: `translateY(${offset}px)`,
            transition: "transform 0.6s cubic-bezier(0.16, 1, 0.3, 1)",
          }}
        >
          {loadingStates.map((state, index) => {
            const isCompleted = index < currentState;
            const isCurrent = index === currentState;
            const isUpcoming = index > currentState;

            return (
              <div
                key={index}
                style={{
                  height: `${itemHeight}px`,
                  display: "flex",
                  alignItems: "center",
                  gap: "1.1rem",
                  padding: "0 1.25rem",
                  transition: "all 0.5s ease",
                  opacity: isCurrent ? 1 : isCompleted ? 0.65 : 0.22,
                  transform: isCurrent ? "scale(1.03)" : "scale(0.97)",
                  transformOrigin: "left center",
                }}
              >
                {/* Icon Column */}
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    width: "28px",
                    height: "28px",
                    flexShrink: 0,
                  }}
                >
                  {isCompleted && (
                    <div style={{ color: "#059669", filter: "drop-shadow(0 0 6px rgba(5, 150, 105, 0.4))" }}>
                      <CheckFilled />
                    </div>
                  )}

                  {isCurrent && (
                    <div
                      style={{
                        color: "#F62440",
                        filter: "drop-shadow(0 0 10px rgba(246, 36, 64, 0.6))",
                        animation: "pulse 1.4s infinite ease-in-out",
                      }}
                    >
                      <CheckFilled />
                    </div>
                  )}

                  {isUpcoming && (
                    <div style={{ color: "#D1C7BA" }}>
                      <CheckOutline />
                    </div>
                  )}
                </div>

                {/* Text Column */}
                <span
                  style={{
                    fontSize: isCurrent ? "1.2rem" : "0.98rem",
                    fontWeight: isCurrent ? 800 : isCompleted ? 600 : 400,
                    color: isCurrent ? "var(--text-main)" : isCompleted ? "var(--text-muted)" : "#9CA3AF",
                    letterSpacing: isCurrent ? "-0.01em" : "0",
                    textShadow: isCurrent ? "0 2px 8px rgba(246, 36, 64, 0.12)" : "none",
                    whiteSpace: "nowrap",
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                  }}
                >
                  {state.text}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

// Named and default export aliases
export { MultiStepLoader as Loader };

export function MultiStepLoaderDemo() {
  const [loading, setLoading] = useState(false);
  return (
    <div style={{ width: "100%", minHeight: "60vh", display: "flex", alignItems: "center", justifyContent: "center" }}>
      <MultiStepLoader loadingStates={defaultLoadingStates} loading={loading} duration={2000} onClose={() => setLoading(false)} />
      <button
        type="button"
        onClick={() => setLoading(true)}
        style={{
          background: "#39C3EF",
          color: "#000",
          fontSize: "1rem",
          fontWeight: 600,
          borderRadius: "8px",
          padding: "0.6rem 2rem",
          cursor: "pointer",
          border: "none",
          boxShadow: "0px -1px 0px 0px #ffffff40 inset, 0px 1px 0px 0px #ffffff40 inset",
        }}
      >
        Click to load
      </button>
    </div>
  );
}

export default MultiStepLoader;
