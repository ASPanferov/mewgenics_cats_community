import { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import { useLang } from '../context/LangContext';
import { useAuth } from '../hooks/useAuth';
import CatCard from '../components/CatCard';
import UploadBox from '../components/UploadBox';

const CATS_PER_PAGE = 25;
const CAT_CLASSES = [
  'Fighter', 'Tank', 'Hunter', 'Mage', 'Medic', 'Necromancer',
  'Druid', 'Thief', 'Tinkerer', 'Monk', 'Jester', 'Psychic',
  'Butcher', 'Colorless',
];

export default function CabinetPage() {
  const { t } = useLang();
  const { user, loading: authLoading, refetch } = useAuth();

  const [saveInfo, setSaveInfo] = useState(null);
  const [saveLoading, setSaveLoading] = useState(true);
  const [allCats, setAllCats] = useState([]);
  const [currentPage, setCurrentPage] = useState(0);
  const [fullscreenImg, setFullscreenImg] = useState(null);
  const [toastMsg, setToastMsg] = useState('');

  // Filters
  const [search, setSearch] = useState('');
  const [classFilter, setClassFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [genderFilter, setGenderFilter] = useState('');
  const [imageFilter, setImageFilter] = useState('');
  const [sortBy, setSortBy] = useState('image_first');

  const fileRef = useRef(null);

  function showToast(msg) {
    setToastMsg(msg);
    setTimeout(() => setToastMsg(''), 3000);
  }

  // Load save info
  useEffect(() => {
    if (!user || user.waitlist) return;
    setSaveLoading(true);
    fetch('/api/save-info')
      .then(r => r.json())
      .then(info => {
        setSaveInfo(info.save_id ? info : null);
      })
      .catch(() => setSaveInfo(null))
      .finally(() => setSaveLoading(false));
  }, [user]);

  // Load cats
  useEffect(() => {
    if (!saveInfo) return;
    fetch('/api/cats')
      .then(r => r.json())
      .then(cats => setAllCats(cats))
      .catch(() => {});
  }, [saveInfo]);

  // Filter + sort
  const filteredCats = useMemo(() => {
    const s = search.toLowerCase();
    let fl = allCats.filter(c => {
      if (s && !c.name.toLowerCase().includes(s)) return false;
      if (classFilter && c.class_en !== classFilter) return false;
      if (genderFilter && String(c.gender_code) !== genderFilter) return false;
      if (imageFilter === 'yes' && !c.has_image) return false;
      if (imageFilter === 'no' && c.has_image) return false;
      if (statusFilter) {
        if (statusFilter === 'alive' && c.is_dead) return false;
        if (statusFilter === 'retired' && !c.is_retired) return false;
        if (statusFilter === 'donated' && !c.is_donated) return false;
        if (statusFilter === 'OK' && (c.status !== 'OK' || c.is_dead)) return false;
        if (statusFilter === 'Injured' && c.status !== 'Injured') return false;
        if (statusFilter === 'Dead' && !c.is_dead) return false;
      }
      return true;
    });

    fl.sort((a, b) => {
      switch (sortBy) {
        case 'birth_desc': return (b.birth_day ?? -1) - (a.birth_day ?? -1);
        case 'birth_asc': return (a.birth_day ?? 9999) - (b.birth_day ?? 9999);
        case 'name_asc': return a.name.localeCompare(b.name, 'ru');
        case 'name_desc': return b.name.localeCompare(a.name, 'ru');
        case 'class': return (a.class_en || '').localeCompare(b.class_en || '');
        case 'image_first':
          if (a.has_image && !b.has_image) return -1;
          if (!a.has_image && b.has_image) return 1;
          return (b.birth_day ?? -1) - (a.birth_day ?? -1);
        default: return 0;
      }
    });

    return fl;
  }, [allCats, search, classFilter, statusFilter, genderFilter, imageFilter, sortBy]);

  const totalPages = Math.ceil(filteredCats.length / CATS_PER_PAGE);
  const safePage = currentPage >= totalPages ? Math.max(0, totalPages - 1) : currentPage;
  const pageCats = filteredCats.slice(safePage * CATS_PER_PAGE, (safePage + 1) * CATS_PER_PAGE);
  const canGen = user && user.generations_count < user.max_generations;

  // Reset page on filter change
  useEffect(() => { setCurrentPage(0); }, [search, classFilter, statusFilter, genderFilter, imageFilter]);

  function goToPage(p) {
    setCurrentPage(p);
    document.querySelector('.cat-grid')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  const handleUploadSuccess = useCallback((d) => {
    showToast(`${d.cat_count} ${t('cats_loaded')}`);
    // Reload save info and cats
    fetch('/api/save-info')
      .then(r => r.json())
      .then(info => setSaveInfo(info.save_id ? info : null))
      .catch(() => {});
    fetch('/api/cats')
      .then(r => r.json())
      .then(cats => setAllCats(cats))
      .catch(() => {});
  }, [t]);

  async function handleNewSave(file) {
    if (!file) return;
    showToast(t('loading'));
    const fd = new FormData();
    fd.append('save_file', file);
    try {
      const r = await fetch('/api/upload', { method: 'POST', body: fd });
      const d = await r.json();
      if (d.success) {
        handleUploadSuccess(d);
      } else {
        showToast(d.error || t('error'));
      }
    } catch (e) {
      showToast(t('net_error'));
    }
  }

  function handleCatGenerate(cat, d) {
    setAllCats(prev => prev.map(c => c.db_id === cat.db_id ? { ...c, has_image: true, image_url: d.image_url } : c));
    refetch(); // refresh user gen count
  }

  function handleCatPublish(cat) {
    setAllCats(prev => prev.map(c => c.db_id === cat.db_id ? { ...c, published: cat.published } : c));
    showToast(t('published_toast'));
  }

  function handleCatUnpublish(cat) {
    setAllCats(prev => prev.map(c => c.db_id === cat.db_id ? { ...c, published: cat.published } : c));
    showToast(t('unpublished_toast'));
  }

  // --- RENDER ---

  if (authLoading) {
    return (
      <div className="page-center">
        <span className="loading-spinner" /> {t('loading')}
      </div>
    );
  }

  // Not logged in
  if (!user) {
    return (
      <div className="page-center">
        <h2>{t('login_prompt')}</h2>
        <p>{t('login_subtitle')}</p>
        <a href="/auth/google" className="btn-google">
          <svg viewBox="0 0 24 24" width="22" height="22">
            <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"/>
            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
          </svg>
          {t('login_google')}
        </a>
      </div>
    );
  }

  // Waitlist
  if (user.waitlist) {
    return (
      <div className="page-center">
        <h2>&#9203; {t('waitlist_title')}</h2>
        <p>{t('waitlist_desc')}</p>
        <p style={{ fontSize: 48, fontWeight: 800, color: '#6b4830', margin: '16px 0' }}>
          #{user.waitlist_position}{' '}
          <span style={{ fontSize: 20, color: '#8a7050' }}>
            {t('waitlist_of')} {user.waitlist_total}
          </span>
        </p>
        <p style={{ color: '#8a7050', fontSize: 14, maxWidth: 400, margin: '0 auto' }}>
          {t('waitlist_hint')}
        </p>
        <a href="/" className="btn-google" style={{ marginTop: 20 }}>
          &#128049; {t('feed')}
        </a>
      </div>
    );
  }

  // Loading save info
  if (saveLoading) {
    return (
      <div className="page-center">
        <span className="loading-spinner" /> {t('loading')}
      </div>
    );
  }

  // No save uploaded yet
  if (!saveInfo) {
    return <UploadBox onSuccess={handleUploadSuccess} />;
  }

  // Main cabinet UI
  return (
    <>
      {/* Controls bar */}
      <div className="controls">
        <div className="controls-row">
          <input
            type="text"
            placeholder={t('search')}
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
          <div className="ctrl-group">
            <label>{t('filter_class')}</label>
            <select value={classFilter} onChange={e => setClassFilter(e.target.value)}>
              <option value="">{t('filter_all')}</option>
              {CAT_CLASSES.map(c => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>
          <div className="ctrl-group">
            <label>{t('filter_status')}</label>
            <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)}>
              <option value="">{t('filter_all')}</option>
              <option value="alive">{t('filter_alive')}</option>
              <option value="OK">OK</option>
              <option value="Injured">{t('filter_injured')}</option>
              <option value="Dead">{t('filter_dead')}</option>
              <option value="retired">{t('filter_retired')}</option>
              <option value="donated">{t('filter_donated')}</option>
            </select>
          </div>
          <div className="ctrl-group">
            <label>{t('filter_gender')}</label>
            <select value={genderFilter} onChange={e => setGenderFilter(e.target.value)}>
              <option value="">{t('filter_all')}</option>
              <option value="1">{t('filter_male')}</option>
              <option value="2">{t('filter_female')}</option>
            </select>
          </div>
          <div className="ctrl-group">
            <label>{t('filter_image')}</label>
            <select value={imageFilter} onChange={e => setImageFilter(e.target.value)}>
              <option value="">{t('filter_all')}</option>
              <option value="yes">{t('filter_with_art')}</option>
              <option value="no">{t('filter_no_art')}</option>
            </select>
          </div>
          <div className="ctrl-group">
            <label>{t('sort')}</label>
            <select value={sortBy} onChange={e => setSortBy(e.target.value)}>
              <option value="image_first">{t('sort_img')}</option>
              <option value="birth_desc">{t('sort_new')}</option>
              <option value="birth_asc">{t('sort_old')}</option>
              <option value="name_asc">{t('sort_name_az')}</option>
              <option value="name_desc">{t('sort_name_za')}</option>
              <option value="class">{t('sort_class')}</option>
            </select>
          </div>
          <label className="ctrl-btn" style={{ cursor: 'pointer' }}>
            {t('new_save')}
            <input
              ref={fileRef}
              type="file"
              accept=".sav"
              style={{ display: 'none' }}
              onChange={e => { if (e.target.files[0]) handleNewSave(e.target.files[0]); }}
            />
          </label>
          <div className="save-info">
            <span>{t('day')} <b>{saveInfo.current_day || '?'}</b></span>
            <span>{t('gold')} <b>{saveInfo.house_gold || '?'}</b></span>
            {saveInfo.house_food && (
              <span>{t('food')} <b>{saveInfo.house_food}</b></span>
            )}
            {saveInfo.adventure_coins && (
              <span>{t('coins')} <b>{saveInfo.adventure_coins}</b></span>
            )}
            {saveInfo.blank_collars && (
              <span>{t('collars')} <b>{saveInfo.blank_collars}</b></span>
            )}
            <span className="cat-count-badge">
              {filteredCats.length} / {allCats.length}
            </span>
          </div>
        </div>
      </div>

      {/* Cat grid */}
      <div className="cat-grid">
        {pageCats.map(cat => (
          <CatCard
            key={cat.db_id}
            cat={cat}
            canGenerate={canGen}
            onGenerate={handleCatGenerate}
            onPublish={handleCatPublish}
            onUnpublish={handleCatUnpublish}
            onImageClick={(url) => setFullscreenImg(url)}
          />
        ))}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="pagination">
          <button disabled={safePage === 0} onClick={() => goToPage(0)}>&laquo;</button>
          <button disabled={safePage === 0} onClick={() => goToPage(safePage - 1)}>&lsaquo;</button>
          {(() => {
            let start = Math.max(0, safePage - 3);
            let end = Math.min(totalPages, start + 7);
            if (end - start < 7) start = Math.max(0, end - 7);
            const btns = [];
            for (let i = start; i < end; i++) {
              btns.push(
                <button
                  key={i}
                  className={i === safePage ? 'active' : ''}
                  onClick={() => goToPage(i)}
                >
                  {i + 1}
                </button>
              );
            }
            return btns;
          })()}
          <button disabled={safePage >= totalPages - 1} onClick={() => goToPage(safePage + 1)}>&rsaquo;</button>
          <button disabled={safePage >= totalPages - 1} onClick={() => goToPage(totalPages - 1)}>&raquo;</button>
          <span className="page-info">
            {safePage * CATS_PER_PAGE + 1}-{Math.min((safePage + 1) * CATS_PER_PAGE, filteredCats.length)} {t('of')} {filteredCats.length}
          </span>
        </div>
      )}

      {/* Fullscreen viewer */}
      {fullscreenImg && (
        <div
          className="image-fullscreen active"
          onClick={() => setFullscreenImg(null)}
        >
          <img src={fullscreenImg} alt="" />
        </div>
      )}

      {/* Toast */}
      {toastMsg && <div className="toast show">{toastMsg}</div>}
    </>
  );
}
