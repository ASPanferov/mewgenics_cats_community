import { C } from './theme';

export const SketchFilters = () => (
  <svg style={{ position: "absolute", width: 0, height: 0 }}>
    <defs>
      <filter id="wobbly">
        <feTurbulence type="turbulence" baseFrequency="0.015" numOctaves="3" seed="2" result="n" />
        <feDisplacementMap in="SourceGraphic" in2="n" scale="1.8" />
      </filter>
      <filter id="wobbly-sm">
        <feTurbulence type="turbulence" baseFrequency="0.02" numOctaves="2" seed="4" result="n" />
        <feDisplacementMap in="SourceGraphic" in2="n" scale="1" />
      </filter>
      <filter id="paper">
        <feTurbulence type="fractalNoise" baseFrequency="0.65" numOctaves="4" seed="8" />
        <feColorMatrix type="saturate" values="0" />
        <feBlend in="SourceGraphic" mode="multiply" result="paper" />
      </filter>
      <filter id="pencil">
        <feMorphology operator="dilate" radius="0.2" />
        <feGaussianBlur stdDeviation="0.2" />
        <feComposite in="SourceGraphic" />
      </filter>
    </defs>
  </svg>
);

export const Styles = () => (
  <style>{`
    @import url('https://fonts.googleapis.com/css2?family=Caveat:wght@400;500;600;700&family=Patrick+Hand&family=Permanent+Marker&family=Shadows+Into+Light&display=swap');

    @keyframes wobble {
      0%, 100% { transform: rotate(-0.2deg) translate(0,0); }
      25% { transform: rotate(0.15deg) translate(0.2px,-0.2px); }
      50% { transform: rotate(-0.1deg) translate(-0.2px,0.15px); }
      75% { transform: rotate(0.2deg) translate(0.15px,0.2px); }
    }
    @keyframes wobbleSlow {
      0%, 100% { transform: rotate(-0.4deg); }
      50% { transform: rotate(0.4deg); }
    }
    @keyframes popIn {
      0% { transform: scale(0) rotate(-8deg); opacity:0; }
      60% { transform: scale(1.1) rotate(1.5deg); }
      80% { transform: scale(0.97) rotate(-0.5deg); }
      100% { transform: scale(1) rotate(0deg); opacity:1; }
    }
    @keyframes slideUp {
      0% { transform: translateY(12px); opacity:0; }
      100% { transform: translateY(0); opacity:1; }
    }
    @keyframes sketchDraw {
      0% { clip-path: inset(0 100% 0 0); opacity:0; }
      20% { opacity:1; }
      100% { clip-path: inset(0 0 0 0); opacity:1; }
    }
    @keyframes pulse { 0%,100%{transform:scale(1)} 50%{transform:scale(1.02)} }
    @keyframes heartbeat { 0%,100%{transform:scale(1)} 15%{transform:scale(1.12)} 30%{transform:scale(1)} 45%{transform:scale(1.06)} }
    @keyframes tapeWiggle { 0%,100%{transform:rotate(-4deg)} 50%{transform:rotate(-2deg)} }
    @keyframes float { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-3px)} }
    @keyframes jitter {
      0%,100% { transform: translate(0,0) rotate(0); }
      10% { transform: translate(-0.5px,0.3px) rotate(-0.2deg); }
      30% { transform: translate(0.3px,-0.5px) rotate(0.15deg); }
      50% { transform: translate(-0.3px,0.2px) rotate(-0.1deg); }
      70% { transform: translate(0.5px,0.3px) rotate(0.2deg); }
      90% { transform: translate(-0.2px,-0.3px) rotate(-0.15deg); }
    }
    * { box-sizing: border-box; }
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: ${C.pageBg}; }
    ::-webkit-scrollbar-thumb { background: ${C.inkFaint}; border-radius: 3px; }
  `}</style>
);
