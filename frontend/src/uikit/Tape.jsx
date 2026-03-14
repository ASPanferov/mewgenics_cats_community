import { C } from './theme';

const Tape = ({ rot = -4, top = -10, left = "50%" }) => (
  <div style={{
    position: "absolute", top, left, transform: `translateX(-50%) rotate(${rot}deg)`,
    width: 55, height: 16,
    background: "linear-gradient(180deg, rgba(210,206,198,0.7) 0%, rgba(190,186,178,0.6) 100%)",
    border: `1px solid ${C.inkFaint}40`,
    borderRadius: 2, zIndex: 5,
    animation: "tapeWiggle 6s ease-in-out infinite",
    boxShadow: `0 1px 3px ${C.shadow}`,
  }} />
);

export default Tape;
