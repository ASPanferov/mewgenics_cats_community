import { C } from './theme';
import Paw from './Paw';

const MewDivider = () => (
  <div style={{ position:"relative", height:18, margin:"10px 0" }}>
    <svg width="100%" height="18">
      <line x1="0" y1="9" x2="100%" y2="9" stroke={C.inkFaint} strokeWidth="1.5"
        strokeDasharray="6 4" opacity="0.4" />
    </svg>
    <Paw size={14} color={`${C.inkFaint}80`}
      style={{position:"absolute",top:2,left:"50%",transform:"translateX(-50%)"}} />
  </div>
);

export default MewDivider;
