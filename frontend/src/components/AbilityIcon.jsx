import { useState } from 'react';
import iconMap from '../data/abilityIconMap.json';

const nameToIdCache = {};

function normalize(s) {
  // Remove all spaces, underscores, hyphens, then lowercase
  return s.replace(/[\s_\-]/g, '').toLowerCase();
}

function getIconId(name) {
  if (!name) return null;
  const cacheKey = name;
  if (nameToIdCache[cacheKey] !== undefined) return nameToIdCache[cacheKey];

  const byName = iconMap.byName;
  if (!byName) { nameToIdCache[cacheKey] = null; return null; }

  // 1. Direct lookup (exact match)
  if (byName[name]) { nameToIdCache[cacheKey] = byName[name]; return byName[name]; }

  // 2. Lowercase
  const lower = name.toLowerCase();
  if (byName[lower]) { nameToIdCache[cacheKey] = byName[lower]; return byName[lower]; }

  // 3. Normalized (strip spaces/underscores/hyphens, lowercase)
  const norm = normalize(name);
  if (byName[norm]) { nameToIdCache[cacheKey] = byName[norm]; return byName[norm]; }

  // 4. PascalCase split to space-separated lowercase: "LineShot" -> "line shot"
  const spaced = name
    .replace(/([a-z])([A-Z])/g, '$1 $2')
    .replace(/([A-Z]+)([A-Z][a-z])/g, '$1 $2')
    .toLowerCase();
  if (byName[spaced]) { nameToIdCache[cacheKey] = byName[spaced]; return byName[spaced]; }

  // 5. Underscore variant: "line_shot"
  const underscored = spaced.replace(/\s+/g, '_');
  if (byName[underscored]) { nameToIdCache[cacheKey] = byName[underscored]; return byName[underscored]; }

  // 6. Strip trailing digits: "Catbot2" -> "catbot"
  const stripped = norm.replace(/\d+$/, '');
  if (stripped !== norm && byName[stripped]) {
    nameToIdCache[cacheKey] = byName[stripped];
    return byName[stripped];
  }

  // 7. Strip common suffixes
  for (const suffix of ['_alt', 'alt', '_ex', 'ex', '_2', '_ii']) {
    if (norm.endsWith(suffix)) {
      const base = norm.slice(0, -suffix.length);
      if (base && byName[base]) {
        nameToIdCache[cacheKey] = byName[base];
        return byName[base];
      }
    }
  }

  nameToIdCache[cacheKey] = null;
  return null;
}

export default function AbilityIcon({ name, type, size = 16 }) {
  const [errored, setErrored] = useState(false);
  const iconId = getIconId(name);

  if (!iconId || iconId > 901 || errored) {
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
      src={`/assets/icons/abilities/${iconId}.png`}
      alt={name}
      width={size}
      height={size}
      style={{ verticalAlign: 'middle', flexShrink: 0 }}
      onError={() => setErrored(true)}
    />
  );
}
