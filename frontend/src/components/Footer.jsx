import { useLang } from '../context/LangContext';

export default function Footer() {
  const { t } = useLang();

  return (
    <footer className="site-footer">
      <div className="footer-inner">
        <div className="footer-col">
          <h3>Dr. Beanies' Laboratory</h3>
          <p dangerouslySetInnerHTML={{ __html: t('footer_about') }} />
          <p>{t('footer_disclaimer')}</p>
        </div>
        <div className="footer-col">
          <h3>{t('footer_author')}</h3>
          <p>
            {t('footer_created_by')}{' '}
            <a href="https://t.me/arpanferov" target="_blank" rel="noopener noreferrer">
              @arpanferov
            </a>
          </p>
          <p style={{ marginTop: 8 }}>
            <button
              className="btn-feedback"
              onClick={() => {
                const ev = new CustomEvent('open-feedback');
                window.dispatchEvent(ev);
              }}
            >
              &#128172; {t('footer_feedback')}
            </button>
          </p>
        </div>
        <div className="footer-col">
          <h3>{t('footer_license')}</h3>
          <p>{t('footer_license_text')}</p>
          <p>{t('footer_license_text2')}</p>
        </div>
      </div>
      <div className="footer-bottom">
        {t('footer_brand')} &copy; 2025-2026 &mdash; Fan project. Not affiliated with Team Meat.
      </div>
    </footer>
  );
}
