import { useState, useEffect, useRef, useCallback } from 'react';
import { useLang } from '../context/LangContext';
import { useAuth } from '../hooks/useAuth';
import SkillCard from '../components/SkillCard';

const FEED_PAGE_SIZE = 20;

export default function FeedPage() {
  const { lang, t } = useLang();
  const { user } = useAuth();
  const [cats, setCats] = useState([]);
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);
  const [total, setTotal] = useState(0);
  const [fullscreenImg, setFullscreenImg] = useState(null);
  const [toastMsg, setToastMsg] = useState('');
  const offsetRef = useRef(0);
  const loadingRef = useRef(false);
  const sentinelRef = useRef(null);

  function showToast(msg) {
    setToastMsg(msg);
    setTimeout(() => setToastMsg(''), 3000);
  }

  const loadMore = useCallback(async () => {
    if (loadingRef.current || done) return;
    loadingRef.current = true;
    setLoading(true);
    try {
      const r = await fetch(`/api/feed?offset=${offsetRef.current}&limit=${FEED_PAGE_SIZE}`);
      const d = await r.json();
      const newCats = d.cats || [];
      setTotal(d.total || 0);
      setCats(prev => [...prev, ...newCats]);
      offsetRef.current += newCats.length;
      if (newCats.length < FEED_PAGE_SIZE || offsetRef.current >= (d.total || 0)) {
        setDone(true);
      }
    } catch (e) {
      /* ignore */
    } finally {
      setLoading(false);
      loadingRef.current = false;
    }
  }, [done]);

  // IntersectionObserver for infinite scroll
  useEffect(() => {
    const sentinel = sentinelRef.current;
    if (!sentinel) return;
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          loadMore();
        }
      },
      { rootMargin: '300px' }
    );
    observer.observe(sentinel);
    return () => observer.disconnect();
  }, [loadMore]);

  // Initial load
  useEffect(() => {
    loadMore();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  async function toggleLike(catId, idx) {
    if (!user) { showToast(t('login_to_like')); return; }
    try {
      const r = await fetch(`/api/cat/${catId}/like`, { method: 'POST' });
      const d = await r.json();
      if (d.success) {
        setCats(prev => prev.map((c, i) =>
          i === idx ? { ...c, liked: d.liked, like_count: d.like_count } : c
        ));
      } else {
        showToast(d.error || t('error'));
      }
    } catch (e) {
      showToast(t('net_error'));
    }
  }

  function shareCat(catId, catName) {
    const url = window.location.origin + '/cat/' + catId;
    if (navigator.share) {
      navigator.share({ title: catName + ' \u2014 Mewgenics', url }).catch(() => {});
    } else if (navigator.clipboard) {
      navigator.clipboard.writeText(url).then(() => showToast(t('link_copied')));
    } else {
      prompt(t('copy_link'), url);
    }
  }

  function renderDetails(cat) {
    const parts = [];
    const genderText = cat.gender_code === 1 ? t('male') : cat.gender_code === 2 ? t('female') : '';
    if (genderText) parts.push(genderText);
    if (cat.age_days) parts.push(`${cat.age_days} ${t('days')}`);
    if (cat.is_dead) parts.push(t('dead'));
    else if (cat.status === 'Injured') parts.push(t('injured'));
    if (cat.is_retired) parts.push(t('filter_retired'));
    if (!parts.length) return null;
    return (
      <div style={{ fontSize: 12, color: '#7a756c', marginBottom: 4 }}>
        {parts.join(' \u00b7 ')}
      </div>
    );
  }

  if (!loading && cats.length === 0 && done) {
    return (
      <div className="feed-grid">
        <div className="empty-feed">
          <p style={{ fontSize: 48 }}>&#128049;</p>
          <p>{t('empty_feed')}</p>
          <p style={{ fontSize: 13, color: '#a8a49c' }}>{t('empty_feed_hint')}</p>
        </div>
      </div>
    );
  }

  return (
    <>
      <div className="feed-grid">
        {cats.map((c, i) => (
          <div className="feed-card" key={c.db_id}>
            <img
              className="feed-img"
              src={`/img/${c.db_id}`}
              alt={c.name}
              onClick={() => setFullscreenImg(`/img/${c.db_id}`)}
            />
            <div className="feed-card-info">
              <div className="feed-card-top">
                <span className="feed-cat-name">{c.name}</span>
                <span className={`badge badge-class bc-${c.class_en}`}>{c['class']}</span>
              </div>
              <div className="feed-owner">
                {c.owner_avatar && <img src={c.owner_avatar} alt="" />}
                {c.owner_name}
              </div>
              {renderDetails(c)}
              <div className="feed-skills">
                {(c.abilities_rich || c.abilities || []).map((a, j) => {
                  const nm = typeof a === 'object' ? a.name : a;
                  const ds = typeof a === 'object' ? a.desc : '';
                  const key = typeof a === 'object' ? (a.key || a.name) : a;
                  return (
                    <SkillCard key={`ab-${j}`} name={nm} desc={ds} iconKey={key} type="ability" lang={lang} compact />
                  );
                })}
                {(c.passives_rich || c.passives || []).map((p, j) => {
                  const nm = typeof p === 'object' ? p.name : p;
                  const ds = typeof p === 'object' ? p.desc : '';
                  const key = typeof p === 'object' ? (p.key || p.name) : p;
                  return (
                    <SkillCard key={`ps-${j}`} name={nm} desc={ds} iconKey={key} type="passive" lang={lang} compact />
                  );
                })}
              </div>
            </div>
            <div className="feed-card-bottom">
              <button
                className={`like-btn${c.liked ? ' liked' : ''}`}
                onClick={() => toggleLike(c.db_id, i)}
              >
                {c.liked ? '\u2764' : '\u2661'}{' '}
                <span className="like-count">{c.like_count || 0}</span>
              </button>
              <button
                className="share-btn"
                onClick={() => shareCat(c.db_id, c.name)}
              >
                &#128279; {t('share')}
              </button>
            </div>
          </div>
        ))}

        {loading && (
          <div className="feed-loader">
            <span className="loading-spinner" /> {t('loading')}
          </div>
        )}
      </div>

      {/* Sentinel for IntersectionObserver */}
      <div ref={sentinelRef} style={{ height: 1 }} />

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
