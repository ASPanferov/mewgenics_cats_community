import AbilityIcon from './AbilityIcon';

const TYPE_CLASSES = {
  ability: 'tag ability',
  passive: 'tag passive',
  item: 'tag item',
  mutation: 'tag mutation',
  defect: 'tag defect',
  'birth-defect': 'tag birth-defect',
};

export default function TagWithIcon({ name, desc, tagKey, type, iconName }) {
  const cls = TYPE_CLASSES[type] || 'tag';
  const showIcon = type === 'ability' || type === 'passive';
  const hasTooltip = desc && desc.trim();
  const showKey = tagKey && tagKey !== name;

  const tagContent = (
    <span className={cls} style={{ display: 'inline-flex', alignItems: 'center', gap: 3 }}>
      {showIcon && <AbilityIcon name={iconName || name} type={type} />}
      {name}
    </span>
  );

  if (!hasTooltip) return tagContent;

  return (
    <span className="tooltip-wrap">
      {tagContent}
      <span className="tip">
        <span className="tip-title">{name}</span>
        {showKey && <span className="tip-key">{tagKey}</span>}
        <span className="tip-desc">{desc}</span>
      </span>
    </span>
  );
}
