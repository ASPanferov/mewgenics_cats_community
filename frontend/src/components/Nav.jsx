import { useEffect, useState } from 'react';
import { NavLink } from 'react-router-dom';
import { useLang } from '../context/LangContext';
import { useAuth } from '../hooks/useAuth';

export default function Nav() {
  const { t } = useLang();
  const { user } = useAuth();
  const [isAdmin, setIsAdmin] = useState(false);

  useEffect(() => {
    if (!user) { setIsAdmin(false); return; }
    fetch('/api/admin/check')
      .then(r => r.json())
      .then(d => { if (d.is_admin) setIsAdmin(true); })
      .catch(() => {});
  }, [user]);

  return (
    <div className="nav">
      <NavLink to="/" end className={({ isActive }) => isActive ? 'active' : ''}>
        {t('feed')}
      </NavLink>
      <NavLink to="/cabinet" className={({ isActive }) => isActive ? 'active' : ''}>
        {t('my_cats')}
      </NavLink>
      {isAdmin && (
        <a
          href="/admin"
          className="admin-link"
          style={{
            marginLeft: 'auto',
            color: '#f0d878',
            background: 'rgba(0,0,0,0.2)',
            borderRadius: 4,
          }}
        >
          {t('admin')}
        </a>
      )}
    </div>
  );
}
