import { C } from './theme';

const Paw = ({ size = 18, color = C.inkFaint, style: s = {} }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" style={s}>
    <ellipse cx="12" cy="16" rx="5" ry="4" fill={color} />
    <circle cx="7.5" cy="9.5" r="2.2" fill={color} />
    <circle cx="16.5" cy="9.5" r="2.2" fill={color} />
    <circle cx="5" cy="13.5" r="1.8" fill={color} />
    <circle cx="19" cy="13.5" r="1.8" fill={color} />
  </svg>
);

export default Paw;
