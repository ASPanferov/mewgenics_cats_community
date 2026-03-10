import AbilityIcon from './AbilityIcon';
import classMap from '../data/classMap.json';

const TYPE_LABELS_RU = {
  ability: 'Атака',
  passive: 'Пассивка',
  item: 'Предмет',
  mutation: 'Мутация',
  defect: 'Дефект',
};

const TYPE_LABELS_EN = {
  ability: 'Attack',
  passive: 'Passive',
  item: 'Item',
  mutation: 'Mutation',
  defect: 'Defect',
};

function getSkillClass(iconKey, name) {
  const key = (iconKey || name || '').toLowerCase();
  return classMap[key] || null;
}

export default function SkillCard({ name, desc, iconKey, type, lang = 'ru', compact = false }) {
  const labels = lang === 'ru' ? TYPE_LABELS_RU : TYPE_LABELS_EN;
  const skillClass = (type === 'ability' || type === 'passive') ? getSkillClass(iconKey, name) : null;
  const classCss = skillClass ? ` sc-${skillClass}` : '';

  return (
    <div className={`skill-card ${type}${compact ? ' compact' : ''}${classCss}`}>
      <div className="skill-card-frame">
        <div className="skill-card-screen">
          <AbilityIcon name={iconKey || name} type={type === 'defect' ? 'ability' : type} size={compact ? 32 : 44} />
        </div>
      </div>
      <div className="skill-card-name">{name}</div>
      {desc && (
        <div className="skill-tooltip">
          <div className="skill-tooltip-title">{name}</div>
          <div className="skill-tooltip-desc">{desc}</div>
          <div className="skill-tooltip-type">{labels[type] || type}</div>
        </div>
      )}
    </div>
  );
}
