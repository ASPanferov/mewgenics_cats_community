import { useState } from 'react';
import { useLang } from '../context/LangContext';
import TagWithIcon from './TagWithIcon';

const STAT_ICONS = ['STR', 'DEX', 'CON', 'INT', 'SPD', 'CHA', 'LCK'];

export default function CatCard({ cat, canGenerate, onGenerate, onPublish, onUnpublish, onImageClick }) {
  const { lang, t } = useLang();
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState('');
  const [bust, setBust] = useState(0);

  const imgUrl = `/img/${cat.db_id}${bust ? `?t=${bust}` : ''}`;

  async function handleGenerate() {
    setGenerating(true);
    setError('');
    try {
      const r = await fetch(`/api/cat/${cat.db_id}/generate`, { method: 'POST' });
      const d = await r.json();
      if (d.success) {
        cat.has_image = true;
        cat.image_url = d.image_url;
        setBust(Date.now());
        if (onGenerate) onGenerate(cat, d);
      } else {
        setError(d.error || t('error'));
      }
    } catch (e) {
      setError(t('net_error'));
    } finally {
      setGenerating(false);
    }
  }

  async function handlePublish() {
    try {
      const r = await fetch(`/api/cat/${cat.db_id}/publish`, { method: 'POST' });
      const d = await r.json();
      if (d.success) {
        cat.published = d.published;
        if (onPublish) onPublish(cat, d);
      }
    } catch (e) { /* ignore */ }
  }

  async function handleUnpublish() {
    try {
      const r = await fetch(`/api/cat/${cat.db_id}/unpublish`, { method: 'POST' });
      const d = await r.json();
      if (d.success) {
        cat.published = d.published;
        if (onUnpublish) onUnpublish(cat, d);
      }
    } catch (e) { /* ignore */ }
  }

  const genderIcon = cat.gender_code === 1
    ? '\u2642' : cat.gender_code === 2
    ? '\u2640' : cat.gender === '\u043a\u043e\u0442-\u043f\u0430\u0443\u043a'
    ? '\u{1F577}' : '';

  const genderText = cat.gender_code === 1
    ? t('male') : cat.gender_code === 2
    ? t('female') : cat.gender === '\u043a\u043e\u0442-\u043f\u0430\u0443\u043a'
    ? t('spider_cat') : '';

  const deadClass = cat.is_dead ? ' dead-card' : '';

  // Info strip chips
  const chips = [];
  if (genderText) chips.push({ label: null, val: genderText });
  if (cat.breed && cat.breed !== 'None' && cat.breed !== '')
    chips.push({ label: t('breed'), val: cat.breed });
  if (cat.age_days != null)
    chips.push({ label: t('age'), val: `${cat.age_days} ${t('days')}` });
  if (cat.birth_day != null)
    chips.push({ label: t('born'), val: `${t('born_day')} ${cat.birth_day}` });
  if (cat.inbreeding_level > 0)
    chips.push({ label: t('inbreeding'), val: cat.inbreeding_level });
  if (cat.parent_keys && cat.parent_keys.length > 0)
    chips.push({ label: t('parents'), val: cat.parent_keys.length });
  if (cat.voice && cat.voice !== '\u043d\u0435\u0438\u0437\u0432\u0435\u0441\u0442\u043d\u043e' && cat.voice !== 'unknown')
    chips.push({ label: t('voice'), val: cat.voice });

  // Stat rendering
  function renderStats() {
    if (!cat.stats) return null;
    return (
      <div className="card-stats">
        {STAT_ICONS.map((k) => {
          const s = cat.stats[k];
          if (!s) return null;
          const cls = s.extra < 0 ? 'hurt' : (s.bonus > 0 || s.extra > 0) ? 'buff' : '';
          const mods = [];
          if (s.bonus) mods.push((s.bonus > 0 ? '+' : '') + s.bonus);
          if (s.extra) mods.push((s.extra > 0 ? '+' : '') + s.extra);
          return (
            <div className="stat-cell" key={k}>
              <span className="stat-icon">{lang === 'ru' ? s.label_ru : s.label_en}</span>
              <span className={`stat-val ${cls}`}>{s.effective}</span>
              {mods.length > 0 && (
                <span className="stat-mod">{s.base}{mods.join('')}</span>
              )}
            </div>
          );
        })}
      </div>
    );
  }

  function renderTagSection(items, type, label) {
    if (!items || !items.length) return null;
    return (
      <div className="card-section">
        <span className="card-section-label">{label}</span>
        <div className="card-section-content">
          {items.map((it, i) => {
            if (typeof it === 'object' && it.name) {
              return (
                <TagWithIcon
                  key={`${it.name}-${i}`}
                  name={it.name}
                  desc={it.desc}
                  tagKey={it.key}
                  type={type}
                  iconName={it.key || it.name}
                />
              );
            }
            return (
              <TagWithIcon
                key={`${it}-${i}`}
                name={it}
                type={type}
              />
            );
          })}
        </div>
      </div>
    );
  }

  function renderMutations() {
    if (!cat.mutations || !cat.mutations.length) return null;
    return (
      <div className="card-section">
        <span className="card-section-label">{t('mutations_label')}</span>
        <div className="card-section-content">
          {cat.mutations.map((m, i) => {
            const cls = m.is_defect ? 'defect' : 'mutation';
            const partName = lang === 'ru'
              ? (m.part_ru || m.part || '')
              : (m.part_en || m.part || '');
            return (
              <TagWithIcon
                key={`mut-${i}`}
                name={partName + (m.is_defect && !m.desc ? t('defect_suffix') : '')}
                desc={m.desc}
                tagKey={m.is_defect ? t('birth_defect') : undefined}
                type={cls}
              />
            );
          })}
        </div>
      </div>
    );
  }

  function renderBirthDefects() {
    const defects = cat.birth_defect_passives || [];
    if (!defects.length) return null;
    return (
      <div className="card-section">
        <span className="card-section-label">{t('defects_label')}</span>
        <div className="card-section-content">
          {defects.map((d, i) => (
            <span className="tag birth-defect" key={i}>{d}</span>
          ))}
        </div>
      </div>
    );
  }

  const hasFocus = cat.stat_focus && cat.stat_focus !== t('none') && cat.stat_focus !== '\u043d\u0435\u0442' && cat.stat_focus !== 'none';

  return (
    <div className={`cat-card${deadClass}`}>
      {/* HEADER */}
      <div className="card-header">
        <div className="card-name-wrap">
          <span className="card-name">{cat.name}</span>
          {genderIcon && <span className="card-gender">{genderIcon}</span>}
        </div>
        <div className="card-badges">
          {cat.is_dead && <span className="badge badge-dead">{t('dead')}</span>}
          {cat.status === 'Injured' && !cat.is_dead && (
            <span className="badge badge-status">{t('injured')}</span>
          )}
          {cat.is_retired && <span className="badge badge-retired">{t('retired_badge')}</span>}
          {cat.is_donated && <span className="badge badge-donated">NPC</span>}
          {cat.published && <span className="badge badge-published">{t('in_feed')}</span>}
          <span className={`badge badge-class bc-${cat.class_en}`}>{cat['class']}</span>
        </div>
      </div>

      {/* IMAGE */}
      <div className="card-top">
        {(cat.has_image || bust) ? (
          <img
            className="cat-portrait"
            src={imgUrl}
            alt={cat.name}
            onClick={() => onImageClick && onImageClick(imgUrl)}
          />
        ) : (
          <div className="no-portrait">&#128049;</div>
        )}
        <div className="card-actions">
          <button
            className="btn btn-generate"
            disabled={!canGenerate || generating}
            onClick={handleGenerate}
          >
            {generating ? (
              <><span className="loading-spinner" /> ...</>
            ) : (
              cat.has_image ? t('regenerate') : t('generate')
            )}
          </button>
          {cat.has_image && (
            cat.published ? (
              <button className="btn btn-unpublish" onClick={handleUnpublish}>
                {t('unpublish')}
              </button>
            ) : (
              <button className="btn btn-publish" onClick={handlePublish}>
                {t('publish')}
              </button>
            )
          )}
        </div>
      </div>

      {/* INFO STRIP */}
      {chips.length > 0 && (
        <div className="card-info-strip">
          {chips.map((c, i) => (
            <span className="info-chip" key={i}>
              {c.label && <span className="ic-label">{c.label}</span>}
              <span className="ic-val">{c.val}</span>
            </span>
          ))}
        </div>
      )}

      {/* STATS */}
      {renderStats()}

      {/* BODY */}
      <div className="card-body">
        {hasFocus && (
          <div className="card-section">
            <span className="card-section-label">{t('focus')}</span>
            <span className="focus-value">{cat.stat_focus}</span>
          </div>
        )}
        {renderTagSection(cat.abilities_rich || cat.abilities, 'ability', t('attacks'))}
        {renderTagSection(cat.passives_rich || cat.passives, 'passive', t('passives_label'))}
        {renderTagSection(cat.items_rich || cat.items, 'item', t('items_label'))}
        {renderMutations()}
        {renderBirthDefects()}
      </div>

      {error && <div className="error-msg">{error}</div>}
    </div>
  );
}
