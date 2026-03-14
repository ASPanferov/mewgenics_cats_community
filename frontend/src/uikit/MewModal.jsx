import { C, FONT } from './theme';

const MewModal = ({ open, onClose, title, children }) => {
  if (!open) return null;
  return (
    <div style={{
      position:"fixed", inset:0, zIndex:999,
      display:"flex", alignItems:"center", justifyContent:"center",
      background:"rgba(40,38,34,0.55)", backdropFilter:"blur(2px)",
    }} onClick={onClose}>
      <div onClick={e=>e.stopPropagation()} style={{
        background:C.panelBg, maxWidth:460, width:"90%",
        borderRadius:"3px 5px 4px 6px", border:`3px solid ${C.ink}80`,
        boxShadow:`5px 5px 0 ${C.shadowStrong}`,
        overflow:"hidden", animation:"popIn 0.35s cubic-bezier(0.34,1.56,0.64,1)",
        filter:"url(#paper)",
      }}>
        <div style={{
          display:"flex", justifyContent:"space-between", alignItems:"center",
          padding:"14px 18px", borderBottom:`2.5px solid ${C.ink}20`, background:C.paperBg,
        }}>
          <span style={{ fontFamily:FONT.title, fontSize:19, color:C.ink }}>{title}</span>
          <button onClick={onClose} style={{
            background:"none", border:"none", cursor:"pointer",
            fontFamily:FONT.title, fontSize:20, color:C.inkLight,
            transform:"rotate(4deg)", transition:"transform 0.2s",
          }}
          onMouseEnter={e=>e.target.style.transform="rotate(12deg) scale(1.2)"}
          onMouseLeave={e=>e.target.style.transform="rotate(4deg)"}
          >&#x2715;</button>
        </div>
        <div style={{padding:"18px"}}>{children}</div>
      </div>
    </div>
  );
};

export default MewModal;
