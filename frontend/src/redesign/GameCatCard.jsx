import { useState } from 'react';
import SkillCard from '../components/SkillCard';

const STAT_CONFIG = [
  { key: 'STR', icon: '⚔', css: 'str' },
  { key: 'DEX', icon: '🎯', css: 'dex' },
  { key: 'CON', icon: '🛡', css: 'con' },
  { key: 'INT', icon: '📖', css: 'int' },
  { key: 'SPD', icon: '💨', css: 'spd' },
  { key: 'CHA', icon: '✨', css: 'cha' },
  { key: 'LCK', icon: '🍀', css: 'lck' },
];

export default function GameCatCard({ cat, lang = 'ru', canGenerate, onGenerate, onPublish, onUnpublish, onImageClick }) {
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState('');
  const [bust, setBust] = useState(0);

  const imgUrl = cat.image_url || (cat.has_image ? `/img/${cat.db_id}${bust ? `?t=${bust}` : ''}` : null);
  const genderIcon = cat.gender_code === 1 ? '♂' : cat.gender_code === 2 ? '♀' : '';

  async function handleGenerate() {
    setGenerating(true); setError('');
    try {
      const r = await fetch(`/api/cat/${cat.db_id}/generate`, { method: 'POST' });
      const d = await r.json();
      if (d.success) { cat.has_image = true; cat.image_url = d.image_url; setBust(Date.now()); onGenerate?.(cat, d); }
      else setError(d.error || 'Ошибка');
    } catch { setError('Ошибка сети'); }
    finally { setGenerating(false); }
  }

  async function handlePublish() {
    try { const r = await fetch(`/api/cat/${cat.db_id}/publish`, { method: 'POST' }); const d = await r.json(); if (d.success) { cat.published = d.published; onPublish?.(cat, d); } } catch {}
  }

  async function handleUnpublish() {
    try { const r = await fetch(`/api/cat/${cat.db_id}/unpublish`, { method: 'POST' }); const d = await r.json(); if (d.success) { cat.published = d.published; onUnpublish?.(cat, d); } } catch {}
  }

  const abilities = cat.abilities_rich || (cat.abilities || []).map(a => ({ name: a, key: a }));
  const passives = cat.passives_rich || (cat.passives || []).map(p => ({ name: p, key: p }));
  const items = cat.items_rich || (cat.items || []).map(i => ({ name: i, key: i }));
  const mutations = cat.mutations || [];

  return (
    <div className="game-panel game-card-compact">
      {/* PORTRAIT */}
      <div className="portrait-area">
        {imgUrl ? (
          <img className="cat-portrait-img" src={imgUrl} alt={cat.name}
            onClick={() => onImageClick?.(imgUrl)} />
        ) : (
          <div className="no-portrait-game">🐱</div>
        )}
      </div>

      {/* NAME */}
      <div className="cat-name-banner">
        <span>{cat.name}</span>
        {genderIcon && <span className="gender-icon">{genderIcon}</span>}
      </div>

      {/* BADGES */}
      <div className="badges-row">
        <span className={`game-badge class-badge c-${cat.class_en}`}>
          {lang === 'ru' ? cat.class_ru || cat['class'] : cat.class_en}
        </span>
        {cat.is_dead && <span className="game-badge dead">{lang === 'ru' ? 'Мёртв' : 'Dead'}</span>}
        {cat.status === 'Injured' && !cat.is_dead && <span className="game-badge injured">{lang === 'ru' ? 'Ранен' : 'Injured'}</span>}
        {cat.is_retired && <span className="game-badge retired">{lang === 'ru' ? 'Отставка' : 'Retired'}</span>}
        {cat.is_donated && <span className="game-badge donated">NPC</span>}
        {cat.published && <span className="game-badge published">{lang === 'ru' ? 'В ленте' : 'Published'}</span>}
      </div>

      {/* INFO */}
      <div className="info-row">
        {cat.breed && cat.breed !== 'None' && cat.breed !== '' && (
          <div className="info-item">
            <span className="info-label">{lang === 'ru' ? 'Порода:' : 'Breed:'}</span>
            <span className="info-val">{cat.breed}</span>
          </div>
        )}
        {cat.age_days != null && (
          <div className="info-item">
            <span className="info-label">{lang === 'ru' ? 'Возраст:' : 'Age:'}</span>
            <span className="info-val">{cat.age_days} {lang === 'ru' ? 'дн.' : 'days'}</span>
          </div>
        )}
        {cat.inbreeding_level > 0 && (
          <div className="info-item">
            <span className="info-label">{lang === 'ru' ? 'Инбридинг:' : 'Inbreeding:'}</span>
            <span className="info-val">{cat.inbreeding_level}</span>
          </div>
        )}
        {cat.stat_focus && cat.stat_focus !== 'нет' && cat.stat_focus !== 'none' && (
          <div className="info-item">
            <span className="info-label">{lang === 'ru' ? 'Фокус:' : 'Focus:'}</span>
            <span className="info-val">{cat.stat_focus}</span>
          </div>
        )}
      </div>

      {/* STATS */}
      {cat.stats && (
        <div className="stats-panel">
          <div className="stat-rows">
            {STAT_CONFIG.map(({ key, icon, css }) => {
              const s = cat.stats[key];
              if (!s) return null;
              const cls = s.extra < 0 ? 'hurt' : (s.bonus > 0 || s.extra > 0) ? 'buff' : '';
              const mods = [];
              if (s.bonus) mods.push((s.bonus > 0 ? '+' : '') + s.bonus);
              if (s.extra) mods.push((s.extra > 0 ? '+' : '') + s.extra);
              return (
                <div className="stat-row" key={key}>
                  <div className={`stat-row-icon ${css}`}>{icon}</div>
                  <span className={`stat-row-val ${cls}`}>{s.effective}</span>
                  {mods.length > 0 && <span className="stat-row-mod">({s.base}{mods.join('')})</span>}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* ABILITIES — TV frame cards */}
      {abilities.length > 0 && (
        <>
          <div className="section-divider">{lang === 'ru' ? 'Атаки' : 'Attacks'}</div>
          <div className="skill-grid">
            {abilities.map((a, i) => (
              <SkillCard key={`ab-${i}`} name={a.name} desc={a.desc} iconKey={a.key} type="ability" lang={lang} />
            ))}
          </div>
        </>
      )}

      {/* PASSIVES */}
      {passives.length > 0 && (
        <>
          <div className="section-divider">{lang === 'ru' ? 'Пассивки' : 'Passives'}</div>
          <div className="skill-grid">
            {passives.map((p, i) => (
              <SkillCard key={`ps-${i}`} name={p.name} desc={p.desc} iconKey={p.key} type="passive" lang={lang} />
            ))}
          </div>
        </>
      )}

      {/* ITEMS */}
      {items.length > 0 && (
        <>
          <div className="section-divider">{lang === 'ru' ? 'Предметы' : 'Items'}</div>
          <div className="skill-grid">
            {items.map((it, i) => (
              <SkillCard key={`it-${i}`} name={it.name} desc={it.desc} iconKey={it.key} type="item" lang={lang} />
            ))}
          </div>
        </>
      )}

      {/* MUTATIONS */}
      {mutations.length > 0 && (
        <>
          <div className="section-divider">{lang === 'ru' ? 'Мутации' : 'Mutations'}</div>
          <div className="skill-grid">
            {mutations.map((m, i) => {
              const name = lang === 'ru' ? (m.part_ru || m.part || '') : (m.part_en || m.part || '');
              return (
                <SkillCard key={`mut-${i}`} name={name} desc={m.desc} iconKey={m.part} type={m.is_defect ? 'defect' : 'mutation'} lang={lang} />
              );
            })}
          </div>
        </>
      )}

      {/* ACTIONS */}
      <div className="game-actions">
        <button className="game-btn primary" disabled={!canGenerate || generating} onClick={handleGenerate}>
          {generating ? '...' : (cat.has_image ? (lang === 'ru' ? 'Перегенерировать' : 'Regenerate') : (lang === 'ru' ? 'Генерировать' : 'Generate'))}
        </button>
        {cat.has_image && (
          cat.published
            ? <button className="game-btn muted" onClick={handleUnpublish}>{lang === 'ru' ? 'Убрать' : 'Unpublish'}</button>
            : <button className="game-btn success" onClick={handlePublish}>{lang === 'ru' ? 'В ленту' : 'Publish'}</button>
        )}
      </div>

      {error && <div style={{ color: '#c03030', padding: '8px 10px', fontSize: '12px', fontWeight: 700 }}>{error}</div>}
    </div>
  );
}
