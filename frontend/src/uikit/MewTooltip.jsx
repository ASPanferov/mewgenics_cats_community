import { useState } from "react";
import { C, FONT } from './theme';

const MewTooltip = ({ children, text }) => {
  const [s,setS] = useState(false);
  return (
    <div style={{position:"relative",display:"inline-block"}}
      onMouseEnter={()=>setS(true)} onMouseLeave={()=>setS(false)}>
      {children}
      {s && text && (
        <div style={{
          position:"absolute", bottom:"calc(100% + 8px)", left:"50%", transform:"translateX(-50%)",
          background:C.ink, color:C.white, fontFamily:FONT.stat, fontSize:13,
          padding:"5px 10px", borderRadius:"3px 4px 3px 5px",
          whiteSpace:"nowrap", zIndex:100, animation:"popIn 0.2s ease-out",
          boxShadow:`2px 2px 0 ${C.shadowStrong}`, filter:"url(#wobbly-sm)",
        }}>
          {text}
          <div style={{
            position:"absolute", bottom:-4, left:"50%", transform:"translateX(-50%) rotate(45deg)",
            width:8, height:8, background:C.ink,
          }}/>
        </div>
      )}
    </div>
  );
};

export default MewTooltip;
