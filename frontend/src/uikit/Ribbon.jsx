import { C, FONT } from './theme';

const Ribbon = ({ children, style: s }) => (
  <div style={{
    position: "relative", display: "inline-block", padding: "6px 28px 8px",
    background: C.white, border: `2.5px solid ${C.ink}`,
    fontFamily: FONT.title, fontSize: 22, color: C.ink,
    textAlign: "center", filter: "url(#wobbly-sm)",
    animation: "wobbleSlow 5s ease-in-out infinite",
    ...s,
  }}>
    {/* Ribbon fold left */}
    <div style={{
      position: "absolute", left: -10, top: "50%", transform: "translateY(-50%)",
      width: 0, height: 0,
      borderTop: "14px solid transparent", borderBottom: "14px solid transparent",
      borderRight: `10px solid ${C.ink}`,
    }} />
    <div style={{
      position: "absolute", left: -7, top: "50%", transform: "translateY(-50%)",
      width: 0, height: 0,
      borderTop: "12px solid transparent", borderBottom: "12px solid transparent",
      borderRight: `8px solid ${C.white}`,
    }} />
    {/* Ribbon fold right */}
    <div style={{
      position: "absolute", right: -10, top: "50%", transform: "translateY(-50%)",
      width: 0, height: 0,
      borderTop: "14px solid transparent", borderBottom: "14px solid transparent",
      borderLeft: `10px solid ${C.ink}`,
    }} />
    <div style={{
      position: "absolute", right: -7, top: "50%", transform: "translateY(-50%)",
      width: 0, height: 0,
      borderTop: "12px solid transparent", borderBottom: "12px solid transparent",
      borderLeft: `8px solid ${C.white}`,
    }} />
    {children}
  </div>
);

export default Ribbon;
