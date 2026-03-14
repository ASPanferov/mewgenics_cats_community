import { useState, useEffect } from "react";
import { C, FONT } from './theme';

const MewStatBar = ({ label, value, max, color=C.red, icon }) => {
  const pct = Math.min((value/max)*100,100);
  const [a,setA] = useState(0);
  useEffect(()=>{setTimeout(()=>setA(pct),200)},[pct]);
  return (
    <div style={{marginBottom:7}}>
      <div style={{
        display:"flex", justifyContent:"space-between", alignItems:"center",
        fontFamily:FONT.stat, fontSize:15, fontWeight:700, color:C.ink, marginBottom:2,
      }}>
        <span style={{display:"flex",alignItems:"center",gap:3}}>
          {icon} {label}
        </span>
        <span style={{fontSize:13,color:C.inkMid}}>{value}/{max}</span>
      </div>
      <div style={{
        position:"relative", height:16, background:C.slotBg,
        borderRadius:"2px 3px 2px 3px", border:`2px solid ${C.ink}50`,
        overflow:"hidden", filter:"url(#wobbly-sm)",
      }}>
        <div style={{
          height:"100%", width:`${a}%`,
          background:`linear-gradient(90deg, ${color}, ${color}cc)`,
          borderRadius:"1px 2px 1px 2px",
          transition:"width 0.8s cubic-bezier(0.34,1.56,0.64,1)",
          boxShadow:"inset 0 -2px 3px rgba(0,0,0,0.1)",
        }}/>
        {[25,50,75].map(p=>(
          <div key={p} style={{
            position:"absolute",top:0,left:`${p}%`,width:1,height:"100%",
            background:`${C.ink}10`,
          }}/>
        ))}
      </div>
    </div>
  );
};

export default MewStatBar;
