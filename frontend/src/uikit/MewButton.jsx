import { useState } from "react";
import { C, FONT } from './theme';

const MewButton = ({ children, variant="primary", size="md", disabled, onClick, icon, style:xs }) => {
  const [p, setP] = useState(false);
  const [h, setH] = useState(false);
  const V = {
    primary:  { bg:C.slotBg, hbg:C.white, border:C.ink, text:C.ink },
    danger:   { bg:"#d8a8a8", hbg:"#ccaaaa", border:C.roseBorder, text:C.redDark },
    mutant:   { bg:"#c0d4b4", hbg:"#b4c8a4", border:C.green, text:"#3a5828" },
    potion:   { bg:"#ccc0d8", hbg:"#c0b4cc", border:C.purple, text:"#4a2a70" },
    ghost:    { bg:"transparent", hbg:`${C.ink}08`, border:C.inkLight, text:C.inkMid },
    rose:     { bg:C.roseLight, hbg:C.roseBg, border:C.roseBorder, text:C.redDark },
  };
  const v = V[variant]||V.primary;
  const S = { sm:{px:10,py:5,fs:14}, md:{px:18,py:9,fs:17}, lg:{px:26,py:13,fs:21} };
  const s = S[size]||S.md;
  return (
    <button onClick={onClick} disabled={disabled}
      onMouseDown={()=>setP(true)} onMouseUp={()=>setP(false)}
      onMouseEnter={()=>setH(true)} onMouseLeave={()=>{setP(false);setH(false)}}
      style={{
        position:"relative", display:"inline-flex", alignItems:"center", gap:7,
        fontFamily:FONT.body, fontSize:s.fs, fontWeight:700, letterSpacing:0.3,
        color: disabled?"#aaa":v.text,
        background: disabled?"#ccc":h?v.hbg:v.bg,
        border:`2.5px solid ${disabled?"#bbb":v.border}`,
        borderRadius:"2px 4px 3px 5px", padding:`${s.py}px ${s.px}px`,
        cursor: disabled?"not-allowed":"pointer",
        transform: p?"scale(0.96) rotate(-0.5deg)":h?"rotate(0.4deg) translateY(-1px)":"none",
        transition:"all 0.15s ease", filter:"url(#wobbly-sm)",
        boxShadow: h&&!disabled ? `2px 2px 0 ${C.shadowStrong}` : `1px 1px 0 ${C.shadow}`,
        animation:"wobbleSlow 6s ease-in-out infinite",
        ...xs,
      }}
    >
      {icon && <span style={{display:"flex",alignItems:"center"}}>{icon}</span>}
      {children}
    </button>
  );
};

export default MewButton;
