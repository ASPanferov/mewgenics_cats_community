import { useLang } from '../context/LangContext';
import { useAuth } from '../hooks/useAuth';

const GOOGLE_SVG = `<svg viewBox="0 0 24 24" width="18" height="18"><path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"/><path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/><path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/><path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/></svg>`;

export default function Header() {
  const { lang, setLang, t } = useLang();
  const { user } = useAuth();

  return (
    <div className="header">
      <div className="header-brand">
        <span className="header-logo">&#128049;</span>
        <h1>MEWGENICS</h1>
      </div>
      <div className="header-right">
        <div className="lang-switch">
          <button
            className={lang === 'ru' ? 'active' : ''}
            onClick={() => setLang('ru')}
          >
            RU
          </button>
          <button
            className={lang === 'en' ? 'active' : ''}
            onClick={() => setLang('en')}
          >
            EN
          </button>
        </div>
        <div className="auth-area">
          {user ? (
            <div className="user-info">
              {user.avatar_url && (
                <img src={user.avatar_url} alt="" />
              )}
              <span>{user.name}</span>
              {user.is_premium && (
                <span className="premium-badge">PRO</span>
              )}
              {user.waitlist ? (
                <span className="gen-counter" style={{ color: '#f0a040', borderColor: '#f0a040' }}>
                  #{user.waitlist_position} {t('waitlist_badge')}
                </span>
              ) : (
                <span className="gen-counter">
                  {user.generations_count}/{user.max_generations} {t('generations')}
                </span>
              )}
              <a href="/auth/logout" className="btn-logout">{t('logout')}</a>
            </div>
          ) : (
            <a href="/auth/google" className="btn-auth">{t('login')}</a>
          )}
        </div>
      </div>
    </div>
  );
}
