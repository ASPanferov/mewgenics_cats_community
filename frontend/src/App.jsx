import { lazy, Suspense } from 'react';
import { Routes, Route } from 'react-router-dom';
import { useLang } from './context/LangContext';
import Header from './components/Header';
import Nav from './components/Nav';
import Footer from './components/Footer';
import './App.css';
import './redesign/game.css';

const FeedPage = lazy(() => import('./pages/FeedPage'));
const CabinetPage = lazy(() => import('./pages/CabinetPage'));
const DemoPage = lazy(() => import('./redesign/DemoPage'));

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
      <Header />
      <Nav />
      <Suspense fallback={<Loading />}>
        <Routes>
          <Route path="/" element={<FeedPage />} />
          <Route path="/cabinet" element={<CabinetPage />} />
          <Route path="/demo" element={<DemoPage />} />
        </Routes>
      </Suspense>
      <Footer />
    </>
  );
}
