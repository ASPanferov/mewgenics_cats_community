import { C, FONT } from './theme';

const MewStatChip = ({ stat, value, positive }) => (
  <div style={{
    display:"inline-flex", alignItems:"center", gap:4,
    background: positive ? "#c0d4b4" : "#d8a8a8",
    border:`2px solid ${positive?C.green:C.roseBorder}60`,
    borderRadius:"2px 4px 3px 5px", padding:"4px 10px",
    fontFamily:FONT.body, fontWeight:700, fontSize:16,
    color: positive ? "#3a5828" : C.redDark,
    animation:"popIn 0.35s cubic-bezier(0.34,1.56,0.64,1)",
    filter:"url(#wobbly-sm)",
  }}>
    <span>{positive?"+":""}{value}</span>
    <span style={{fontSize:13,opacity:0.8}}>{stat}</span>
  </div>
);

export default MewStatChip;
