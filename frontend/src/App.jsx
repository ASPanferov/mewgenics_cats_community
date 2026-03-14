import { lazy, Suspense } from 'react';
import { Routes, Route } from 'react-router-dom';
import { useLang } from './context/LangContext';
import Header from './components/Header';
import Nav from './components/Nav';
import Footer from './components/Footer';
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
    </>
  );
}
