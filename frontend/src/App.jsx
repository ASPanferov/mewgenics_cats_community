import { lazy, Suspense, useState, useEffect } from 'react';
import { Routes, Route } from 'react-router-dom';
import { useLang } from './context/LangContext';
import { useAuth } from './hooks/useAuth';
import Header from './components/Header';
import Nav from './components/Nav';
import Footer from './components/Footer';
import FeedbackModal from './components/FeedbackModal';
import { SketchFilters, Styles as UiKitStyles } from './uikit/SvgFilters';
import './App.css';
import './redesign/game.css';

const LandingPage = lazy(() => import('./pages/LandingPage'));
const FeedPage = lazy(() => import('./pages/FeedPage'));
const CabinetPage = lazy(() => import('./pages/CabinetPage'));

function Loading() {
  const { t } = useLang();
  return (
    <div className="page-center">
      <span className="loading-spinner" /> {t('loading')}
    </div>
  );
}

export default function App() {
  const [feedbackOpen, setFeedbackOpen] = useState(false);
  const { user } = useAuth();

  useEffect(() => {
    const handler = () => setFeedbackOpen(true);
    window.addEventListener('open-feedback', handler);
    return () => window.removeEventListener('open-feedback', handler);
  }, []);

  return (
    <>
      <SketchFilters />
      <UiKitStyles />
      <Header />
      <Nav />
      <Suspense fallback={<Loading />}>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/feed" element={<FeedPage />} />
          <Route path="/cabinet" element={<CabinetPage />} />
        </Routes>
      </Suspense>
      <Footer />
      <FeedbackModal
        isOpen={feedbackOpen}
        onClose={() => setFeedbackOpen(false)}
        userName={user?.name || ''}
      />
    </>
  );
}
