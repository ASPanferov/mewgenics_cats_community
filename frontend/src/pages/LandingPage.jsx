import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useLang } from '../context/LangContext';

export default function LandingPage() {
  const { t } = useLang();
  const [cats, setCats] = useState([]);
  const [fullscreenImg, setFullscreenImg] = useState(null);

  useEffect(() => {
    fetch('/api/feed?offset=0&limit=6')
      .then(r => r.json())
      .then(d => setCats(d.cats || []))
      .catch(() => {});
  }, []);

  return (
    <>
      {/* Hero */}
      <section className="landing-hero">
        <h2 className="landing-hero-title">{t('landing_title')}</h2>
        <p className="landing-hero-subtitle">{t('landing_subtitle')}</p>
        <p className="landing-hero-desc">{t('landing_desc')}</p>
        <Link to="/cabinet" className="btn btn-cta">{t('landing_cta')}</Link>
      </section>

      {/* How It Works */}
      <section className="landing-section">
        <h3 className="landing-section-title">{t('landing_how_title')}</h3>
        <div className="landing-steps">
          <div className="landing-step">
            <span className="landing-step-icon">&#128194;</span>
            <h4>{t('landing_step1_title')}</h4>
            <p>{t('landing_step1_desc')}</p>
          </div>
          <div className="landing-step">
            <span className="landing-step-icon">&#128300;</span>
            <h4>{t('landing_step2_title')}</h4>
            <p>{t('landing_step2_desc')}</p>
          </div>
          <div className="landing-step">
            <span className="landing-step-icon">&#127912;</span>
            <h4>{t('landing_step3_title')}</h4>
            <p>{t('landing_step3_desc')}</p>
          </div>
        </div>
      </section>

      {/* Gallery */}
      {cats.length > 0 && (
        <section className="landing-section">
          <h3 className="landing-section-title">{t('landing_gallery_title')}</h3>
          <div className="landing-gallery">
            {cats.map(c => (
              <div
                className="landing-gallery-card"
                key={c.db_id}
                onClick={() => setFullscreenImg(`/img/${c.db_id}`)}
              >
                <img src={`/img/${c.db_id}`} alt={c.name} />
                <div className="landing-gallery-name">{c.name}</div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* CTA */}
      <section className="landing-cta-section">
        <h3 className="landing-section-title">{t('landing_join_title')}</h3>
        <p className="landing-cta-desc">{t('landing_join_desc')}</p>
        <div className="landing-cta-buttons">
          <a href="/auth/google" className="btn-google">
            <svg viewBox="0 0 24 24" width="22" height="22">
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"/>
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
            </svg>
            {t('login_google')}
          </a>
          <a
            href="https://t.me/mewgenicsru"
            target="_blank"
            rel="noopener noreferrer"
            className="btn btn-telegram"
          >
            {t('landing_community')}
          </a>
        </div>
      </section>

      {/* Fullscreen viewer */}
      {fullscreenImg && (
        <div
          className="image-fullscreen active"
          onClick={() => setFullscreenImg(null)}
        >
          <img src={fullscreenImg} alt="" />
        </div>
      )}
    </>
  );
}
