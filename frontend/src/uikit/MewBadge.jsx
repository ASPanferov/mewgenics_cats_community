import { C, FONT } from './theme';

const MewBadge = ({ children, variant="default" }) => {
  const V = {
    default: { bg:C.slotBg, color:C.ink, b:C.inkLight },
    danger:  { bg:"#d8a8a8", color:C.redDark, b:C.roseBorder },
    success: { bg:"#c0d4b4", color:"#3a5828", b:C.green },
    magic:   { bg:"#ccc0d8", color:"#4a2a70", b:C.purple },
    rare:    { bg:"#ddd4b4", color:"#7a6420", b:C.gold },
  };
  const v = V[variant]||V.default;
  return (
    <span style={{
      display:"inline-block", fontFamily:FONT.stat, fontSize:13, fontWeight:600,
      color:v.color, background:v.bg, border:`1.5px solid ${v.b}80`,
      borderRadius:"2px 3px 2px 3px", padding:"2px 8px", filter:"url(#wobbly-sm)",
    }}>{children}</span>
  );
};

export default MewBadge;
