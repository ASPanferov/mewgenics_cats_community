export const CLASS_COLORS = {
  Fighter: '#c03030',
  Tank: '#d07020',
  Hunter: '#308850',
  Mage: '#8858b0',
  Medic: '#a09880',
  Necromancer: '#2a2a2a',
  Druid: '#4a6a2a',
  Thief: '#b8a840',
  Tinkerer: '#58a030',
  Colorless: '#908070',
  Monk: '#b89828',
  Psychic: '#9038b0',
  Jester: 'linear-gradient(90deg, #c03030, #3858a8, #308850)',
  Butcher: '#701818',
};

/**
 * Get the CSS color (or gradient) for a cat class name.
 * Falls back to Colorless if the class is unknown.
 */
export function getClassColor(className) {
  if (!className) return CLASS_COLORS.Colorless;
  const key = className.charAt(0).toUpperCase() + className.slice(1).toLowerCase();
  return CLASS_COLORS[key] ?? CLASS_COLORS.Colorless;
}

/**
 * Returns an inline style object suitable for the class badge.
 * Handles gradient backgrounds (Jester) vs solid colors.
 */
export function getClassStyle(className) {
  const color = getClassColor(className);
  if (color.startsWith('linear-gradient')) {
    return { background: color, color: '#fff' };
  }
  return { backgroundColor: color, color: '#fff' };
}

export const STAT_ICONS = ['STR', 'DEX', 'CON', 'INT', 'SPD', 'CHA', 'LCK'];
