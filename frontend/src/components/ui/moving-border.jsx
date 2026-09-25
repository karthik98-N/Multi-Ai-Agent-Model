import React, { useRef, useEffect } from "react";

/**
 * Aceternity UI: MovingBorder
 * 
 * Creates an animated glowing beam that travels continuously along
 * the outer border path of any container or button using hardware-accelerated
 * SVG path tracking.
 */
export const MovingBorder = ({
  children,
  duration = 3000,
  rx = "16px",
  ry = "16px",
  ...otherProps
}) => {
  const pathRef = useRef(null);
  const dotRef = useRef(null);

  useEffect(() => {
    let animationFrameId;
    let startTime = null;

    const animate = (timestamp) => {
      if (!startTime) startTime = timestamp;
      const elapsed = timestamp - startTime;

      if (pathRef.current && dotRef.current) {
        try {
          const length = pathRef.current.getTotalLength ? pathRef.current.getTotalLength() : 0;
          if (length && !isNaN(length) && length > 0) {
            const pxPerMs = length / duration;
            const currentDistance = (elapsed * pxPerMs) % length;
            const pt = pathRef.current.getPointAtLength(currentDistance);
            if (pt) {
              dotRef.current.style.transform = `translate3d(${pt.x}px, ${pt.y}px, 0) translate(-50%, -50%)`;
            }
          }
        } catch {
          // Graceful fallback if SVG isn't yet laid out
        }
      }
      animationFrameId = requestAnimationFrame(animate);
    };

    animationFrameId = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(animationFrameId);
  }, [duration]);

  return (
    <>
      <svg
        xmlns="http://www.w3.org/2000/svg"
        preserveAspectRatio="none"
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          width: "100%",
          height: "100%",
          pointerEvents: "none",
        }}
        {...otherProps}
      >
        <rect
          fill="none"
          width="100%"
          height="100%"
          rx={rx}
          ry={ry}
          ref={pathRef}
        />
      </svg>
      <div
        ref={dotRef}
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          display: "inline-block",
          pointerEvents: "none",
          willChange: "transform",
        }}
      >
        {children}
      </div>
    </>
  );
};

/**
 * Aceternity UI: Button / MovingBorderContainer
 * 
 * Wraps content with an animated moving border track.
 * Supports polymorphic rendering via the `as` prop (e.g. as="div" or as="button").
 */
export function Button({
  borderRadius = "1.75rem",
  children,
  as: Component = "button",
  containerClassName = "",
  borderClassName = "",
  duration = 8000,
  className = "",
  style = {},
  glowColor,
  glowOpacity = 0.4,
  blur = "10px",
  ...otherProps
}) {
  return (
    <Component
      className={containerClassName}
      style={{
        position: "relative",
        borderRadius: borderRadius,
        padding: "2px",
        overflow: "hidden",
        background: "transparent",
        border: "none",
        cursor: Component === "button" ? "pointer" : "default",
        ...style,
      }}
      {...otherProps}
    >
      {/* Moving border glow layer */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          borderRadius: `calc(${borderRadius} * 0.98)`,
          pointerEvents: "none",
        }}
      >
        <MovingBorder duration={duration} rx={borderRadius} ry={borderRadius}>
          <div
            className={borderClassName}
            style={{
              height: "170px",
              width: "170px",
              opacity: glowOpacity,
              background:
                glowColor ||
                "radial-gradient(circle, #FF3D57 0%, #F62440 25%, #FB7185 50%, #F59E0B 72%, transparent 88%)",
              filter: `blur(${blur})`,
            }}
          />
        </MovingBorder>
      </div>

      {/* Inner surface container */}
      <div
        className={className}
        style={{
          position: "relative",
          width: "100%",
          height: "100%",
          borderRadius: `calc(${borderRadius} * 0.94)`,
          display: "flex",
        }}
      >
        {children}
      </div>
    </Component>
  );
}

/**
 * Demo component as specified in Aceternity UI documentation
 */
export function MovingBorderDemo() {
  return (
    <div>
      <Button
        borderRadius="1.75rem"
        className="bg-white dark:bg-slate-900 text-black dark:text-white border-neutral-200 dark:border-slate-800"
      >
        Borders are cool
      </Button>
    </div>
  );
}

export default Button;
