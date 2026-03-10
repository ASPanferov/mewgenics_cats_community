import { useState, useEffect } from 'react';
import GameCatCard from './GameCatCard';
import './game.css';

// Demo with local cat images + real API data
const LOCAL_IMAGES = [1103, 1160, 1165, 1173, 1194, 1199, 1201, 1203, 1207];

export default function DemoPage() {
  const [cats, setCats] = useState([]);
  const [loading, setLoading] = useState(true);
  const [lang, setLang] = useState('ru');
  const [fullImg, setFullImg] = useState(null);

  useEffect(() => {
    fetchCats();
  }, []);

  async function fetchCats() {
    try {
      const r = await fetch('/api/feed?page=1');
      const d = await r.json();
      // Use API cats but override images with local ones for demo
      const merged = (d.cats || []).map((cat, i) => ({
        ...cat,
        image_url: i < LOCAL_IMAGES.length
          ? `/cats/${LOCAL_IMAGES[i]}.png`
          : cat.image_url,
        has_image: true,
      }));
      setCats(merged);
    } catch {
      // Fallback: generate mock cats
      setCats(generateMockCats());
    }
    setLoading(false);
  }

  return (
    <div className="game-page">
      {/* Simple header for demo */}
      <div style={{
        background: 'linear-gradient(180deg, #6b4830 0%, #3a1e0e 100%)',
        padding: '12px 24px',
        borderBottom: '4px solid #2a1a0e',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        boxShadow: '0 4px 12px rgba(0,0,0,0.4)',
      }}>
        <h1 style={{
          fontFamily: "'EdmundMcMillen', 'Nunito', sans-serif",
          fontSize: '28px',
          fontWeight: 800,
          color: '#f0d878',
          textShadow: '2px 2px 0 #2a1a0e',
          letterSpacing: '3px',
          textTransform: 'uppercase',
        }}>
          Mewgenics
        </h1>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <button
            onClick={() => setLang('ru')}
            style={{
              background: lang === 'ru' ? '#f0d878' : 'transparent',
              color: lang === 'ru' ? '#2a1a0e' : '#a08a60',
              border: '2px solid #a08a60',
              borderRadius: '4px',
              padding: '4px 10px',
              cursor: 'pointer',
              fontWeight: 800,
              fontFamily: 'Nunito, sans-serif',
            }}
          >RU</button>
          <button
            onClick={() => setLang('en')}
            style={{
              background: lang === 'en' ? '#f0d878' : 'transparent',
              color: lang === 'en' ? '#2a1a0e' : '#a08a60',
              border: '2px solid #a08a60',
              borderRadius: '4px',
              padding: '4px 10px',
              cursor: 'pointer',
              fontWeight: 800,
              fontFamily: 'Nunito, sans-serif',
            }}
          >EN</button>
        </div>
      </div>

      {/* Main content */}
      <div style={{ padding: '20px' }}>
        <div className="panel-banner" style={{ margin: '0 auto 20px' }}>
          {lang === 'ru' ? 'Мои коты' : 'My Cats'}
        </div>

        {loading ? (
          <div style={{ textAlign: 'center', padding: '60px', color: '#8a7050', fontSize: '18px' }}>
            {lang === 'ru' ? 'Загрузка...' : 'Loading...'}
          </div>
        ) : (
          <div className="game-cat-grid">
            {cats.map((cat, i) => (
              <GameCatCard
                key={cat.db_id || i}
                cat={cat}
                lang={lang}
                canGenerate={true}
                onImageClick={setFullImg}
              />
            ))}
          </div>
        )}
      </div>

      {/* Fullscreen image */}
      {fullImg && (
        <div
          style={{
            position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
            background: 'rgba(0,0,0,0.9)', zIndex: 2000, cursor: 'pointer',
            display: 'flex', justifyContent: 'center', alignItems: 'center',
          }}
          onClick={() => setFullImg(null)}
        >
          <img
            src={fullImg}
            alt=""
            style={{
              maxWidth: '95%', maxHeight: '95%', objectFit: 'contain',
              borderRadius: '4px', border: '4px solid #6b4830',
            }}
          />
        </div>
      )}
    </div>
  );
}

function generateMockCats() {
  return LOCAL_IMAGES.map((id, i) => ({
    db_id: id,
    name: ['Whiskers', 'Dr. Socks', 'Melody', 'Shadow', 'Mr. Fluffy', 'Patches', 'Luna', 'Gizmo', 'Noodle'][i],
    class: ['Механик', 'Боец', 'Маг', 'Охотник', 'Танк', 'Некромант', 'Друид', 'Вор', 'Шут'][i],
    class_en: ['Tinkerer', 'Fighter', 'Mage', 'Hunter', 'Tank', 'Necromancer', 'Druid', 'Thief', 'Jester'][i],
    class_ru: ['Механик', 'Боец', 'Маг', 'Охотник', 'Танк', 'Некромант', 'Друид', 'Вор', 'Шут'][i],
    gender_code: i % 3 === 0 ? 1 : 2,
    gender: i % 3 === 0 ? 'кот' : 'кошка',
    image_url: `/cats/${id}.png`,
    has_image: true,
    is_dead: i === 3,
    is_retired: i === 5,
    is_donated: false,
    published: i < 3,
    breed: i === 0 ? 'Siamese' : '',
    age_days: 10 + i * 3,
    inbreeding_level: i === 2 ? 1 : 0,
    stat_focus: i === 0 ? 'Обожжённый' : null,
    stats: {
      STR: { base: 5, bonus: i, extra: 0, effective: 5 + i, label_en: 'STR', label_ru: 'СИЛ' },
      DEX: { base: 7, bonus: 0, extra: i === 3 ? -2 : 0, effective: i === 3 ? 5 : 7, label_en: 'DEX', label_ru: 'ЛОВ' },
      CON: { base: 4, bonus: 2, extra: 0, effective: 6, label_en: 'CON', label_ru: 'ВЫН' },
      INT: { base: 8, bonus: 0, extra: 0, effective: 8, label_en: 'INT', label_ru: 'ИНТ' },
      SPD: { base: 6, bonus: 1, extra: 0, effective: 7, label_en: 'SPD', label_ru: 'СКР' },
      CHA: { base: 3, bonus: 0, extra: 0, effective: 3, label_en: 'CHA', label_ru: 'ХАР' },
      LCK: { base: 5, bonus: 0, extra: 0, effective: 5, label_en: 'LCK', label_ru: 'УДЧ' },
    },
    abilities_rich: [
      { name: 'Отражение', key: 'Reflect', desc: 'Отразите следующий снаряд обратно в атакующего.' },
      { name: 'Длинный выстрел', key: 'LongShot', desc: 'Стреляйте снарядом через всё поле.' },
      { name: 'Стрелодел', key: 'ArrowSmith', desc: '+1 Бонусную Атаку в начале след. хода.' },
    ].slice(0, 1 + (i % 3)),
    passives_rich: [
      { name: 'Проводник', key: 'Conductor', desc: 'Электро-урон +2 за каждый кусок металлической брони.' },
      { name: 'Быстроногий', key: 'FastFooted', desc: '+2 к скорости передвижения.' },
    ].slice(0, 1 + (i % 2)),
    items_rich: [
      { name: 'Скрытая Атака', key: 'SneakAttack', desc: 'Призывающие заклинания стоят -3 маны.' },
    ].slice(0, i % 2),
    mutations: i === 4 ? [
      { part: 'HornCharge', part_ru: 'Рога', part_en: 'Horn Charge', is_defect: false, desc: 'Дополнительная атака рогами.' },
      { part: 'PuncturedEye', part_ru: 'Проколотый глаз', part_en: 'Punctured Eye', is_defect: true, desc: 'Дефект зрения.' },
    ] : [],
    birth_defect_passives: [],
    parent_keys: [],
    like_count: i * 2,
    liked: i === 0,
  }));
}
