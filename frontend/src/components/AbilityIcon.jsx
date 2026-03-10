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
    // Fallback: strip trailing digits (e.g. "Catbot2" -> "catbot")
    const stripped = key.replace(/\d+$/, '');
    if (stripped !== key && byName[stripped]) {
      nameToIdCache[key] = byName[stripped];
      return byName[stripped];
    }
  }
  nameToIdCache[key] = null;
  return null;
}

export default function AbilityIcon({ name, type, size = 16 }) {
  const [errored, setErrored] = useState(false);
  const iconId = getIconId(name);

  if (!iconId || errored) {
    const color = type === 'ability' ? '#c83030' : type === 'passive' ? '#2a7a50' : type === 'item' ? '#b89828' : type === 'mutation' ? '#7838a0' : '#8a7050';
    return (
      <span
        className="ability-icon-fallback"
        style={{
          display: 'inline-block',
          width: size,
          height: size,
          borderRadius: '50%',
          background: color,
          opacity: 0.5,
          verticalAlign: 'middle',
          flexShrink: 0,
        }}
      />
    );
  }

  return (
    <img
      src={`/assets/icons/abilities/${iconId}.svg`}
      alt={name}
      width={size}
      height={size}
      style={{ verticalAlign: 'middle', flexShrink: 0 }}
      onError={() => setErrored(true)}
    />
  );
}
