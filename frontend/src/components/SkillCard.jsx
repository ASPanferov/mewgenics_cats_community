import AbilityIcon from './AbilityIcon';

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

export default function SkillCard({ name, desc, iconKey, type, lang = 'ru', compact = false }) {
  const labels = lang === 'ru' ? TYPE_LABELS_RU : TYPE_LABELS_EN;

  return (
    <div className={`skill-card ${type}${compact ? ' compact' : ''}`}>
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
