import { useState } from "react";
import { C, FONT } from './theme';

const MewInput = ({ label, placeholder, value, onChange }) => {
  const [f,setF] = useState(false);
  return (
    <div style={{ marginBottom: 12 }}>
      {label && <label style={{
        fontFamily:FONT.body, fontSize:16, fontWeight:600, color:C.ink,
        display:"block", marginBottom:3,
      }}>{label}</label>}
      <input placeholder={placeholder} value={value} onChange={onChange}
        onFocus={()=>setF(true)} onBlur={()=>setF(false)}
        style={{
          width:"100%", padding:"9px 12px",
          fontFamily:FONT.stat, fontSize:16, color:C.ink,
          background:C.slotBg,
          border:`2.5px solid ${f?C.ink:C.inkFaint}`,
          borderRadius:"2px 3px 2px 4px",
          outline:"none", transition:"border-color 0.2s",
          boxShadow: f ? `0 0 0 2px ${C.ink}10` : "none",
          filter:"url(#wobbly-sm)",
        }}
      />
    </div>
  );
};

export default MewInput;
