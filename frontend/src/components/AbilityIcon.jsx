import { useState } from 'react';
import iconMap from '../data/abilityIconMap.json';

const nameToIdCache = {};
function getIconId(name) {
  if (!name) return null;
  const key = name.toLowerCase();
  if (nameToIdCache[key] !== undefined) return nameToIdCache[key];
  const byName = iconMap.byName;
  if (byName) {
    const id = byName[key] || byName[name];
    if (id) { nameToIdCache[key] = id; return id; }
  }
  const byId = iconMap.byId;
  if (byId) {
    for (const [id, n] of Object.entries(byId)) {
      if (n.toLowerCase() === key) {
        nameToIdCache[key] = id;
        return id;
      }
    }
  }
  nameToIdCache[key] = null;
  return null;
}

export default function AbilityIcon({ name, type }) {
  const [errored, setErrored] = useState(false);
  const iconId = getIconId(name);

  if (!iconId || errored) {
    const color = type === 'ability' ? '#c83030' : '#2a7a50';
    return (
      <span
        className="ability-icon-fallback"
        style={{
          display: 'inline-block',
          width: 16,
          height: 16,
          borderRadius: '50%',
          background: color,
          opacity: 0.5,
          verticalAlign: 'middle',
          flexShrink: 0,
        }}
      />
    );
  }

  if (type === 'passive') {
    return (
      <img
        src={`/assets/icons/passives/${iconId}.png`}
        alt={name}
        width={16}
        height={16}
        style={{ verticalAlign: 'middle', flexShrink: 0 }}
        onError={() => setErrored(true)}
      />
    );
  }

  return (
    <img
      src={`/assets/icons/abilities/${iconId}.svg`}
      alt={name}
      width={16}
      height={16}
      style={{ verticalAlign: 'middle', flexShrink: 0 }}
      onError={() => setErrored(true)}
    />
  );
}
