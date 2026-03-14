import { C, FONT } from './theme';

const MewNotification = ({ message, variant="info", visible }) => {
  const V = {
    info:    { bg:C.panelBg, b:C.ink, icon:"📋" },
    success: { bg:"#c0d4b4", b:C.green, icon:"✨" },
    warning: { bg:"#ddd4b4", b:C.gold, icon:"⚠️" },
    error:   { bg:"#d8a8a8", b:C.roseBorder, icon:"💀" },
  };
  const v = V[variant];
  if (!visible) return null;
  return (
    <div style={{
      display:"flex", alignItems:"center", gap:9,
      background:v.bg, border:`2.5px solid ${v.b}70`,
      borderRadius:"2px 4px 3px 5px", padding:"9px 14px",
      fontFamily:FONT.stat, fontSize:14, color:C.ink,
      boxShadow:`2px 2px 0 ${C.shadow}`,
      animation:"popIn 0.35s cubic-bezier(0.34,1.56,0.64,1)",
      filter:"url(#wobbly-sm)",
    }}>
      <span style={{fontSize:18}}>{v.icon}</span>
      {message}
    </div>
  );
};

export default MewNotification;
