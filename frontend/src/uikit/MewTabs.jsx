import { C, FONT } from './theme';

const MewTabs = ({ tabs, active, onChange }) => (
  <div style={{
    display: "flex", gap: 0, borderBottom: `2.5px solid ${C.ink}30`, marginBottom: 14,
  }}>
    {tabs.map(t => (
      <button key={t} onClick={()=>onChange(t)} style={{
        fontFamily: FONT.body, fontSize: 18, fontWeight: active===t?700:500,
        color: active===t ? C.ink : C.inkLight,
        background: active===t ? C.panelBg : "transparent",
        border: active===t ? `2.5px solid ${C.ink}30` : "2px solid transparent",
        borderBottom: active===t ? `2.5px solid ${C.panelBg}` : "none",
        borderRadius: "3px 5px 0 0", padding: "7px 16px",
        cursor: "pointer", position: "relative", bottom: -2.5,
        transition: "all 0.2s",
        filter: active===t ? "url(#wobbly-sm)" : "none",
      }}>{t}</button>
    ))}
  </div>
);

export default MewTabs;
