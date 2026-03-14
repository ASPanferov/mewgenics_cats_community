import { useState, useEffect } from "react";
import { C, FONT } from './theme';
import Tape from './Tape';
import Ribbon from './Ribbon';

const MewCard = ({ children, title, tape, pinned, torn, style:xs, ribbon }) => {
  const [vis,setVis] = useState(false);
  useEffect(()=>{setTimeout(()=>setVis(true),80)},[]);
  return (
    <div style={{
      position:"relative", background:C.panelBg,
      padding: ribbon ? "36px 20px 20px" : "22px 18px",
      borderRadius:"2px 3px 2px 4px",
      border:`2.5px solid ${C.ink}70`,
      boxShadow:`3px 3px 0 ${C.shadow}, inset 0 0 40px rgba(30,28,24,0.03)`,
      filter:"url(#paper)",
      opacity:vis?1:0, transform:vis?"translateY(0)":"translateY(10px)",
      transition:"all 0.4s ease",
      ...(torn && {
        clipPath:"polygon(0 0,100% 0,100% 2%,98% 3.5%,100% 5.5%,99% 8%,100% 100%,0 100%,1.5% 96%,0 93%,2% 89%)"
      }),
      ...xs,
    }}>
      {tape && <Tape />}
      {pinned && (
        <div style={{
          position:"absolute",top:-5,right:14,width:12,height:12,borderRadius:"50%",
          background:C.red, border:`2px solid ${C.redDark}`,
          boxShadow:`0 2px 4px ${C.shadowStrong}`, zIndex:5,
        }}/>
      )}
      {ribbon && (
        <div style={{position:"absolute",top:-16,left:"50%",transform:"translateX(-50%)",zIndex:6}}>
          <Ribbon>{title}</Ribbon>
        </div>
      )}
      {title && !ribbon && (
        <div style={{
          fontFamily:FONT.title, fontSize:20, color:C.ink,
          marginBottom:12, paddingBottom:7,
          borderBottom:`2px dashed ${C.inkFaint}50`,
          animation:"sketchDraw 0.7s ease-out",
        }}>
          {title}
        </div>
      )}
      {children}
    </div>
  );
};

export default MewCard;
