import React from 'react';
import { HashRouter, Routes, Route, useLocation, Navigate } from 'react-router-dom';
import { Layout } from './components/Layout';
import { Home } from './pages/Home';
import { DocsIntroduction } from './pages/DocsIntroduction';
import { Architecture } from './pages/Architecture';
import { ApiReference } from './pages/ApiReference';

const ScrollToTop = () => {
  const { pathname } = useLocation();

  React.useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname]);

  return null;
};

const App: React.FC = () => {
  return (
    <HashRouter>
      <ScrollToTop />
      <Routes>
        <Route path="/" element={<Layout type="docs"><Home /></Layout>} />
        <Route path="/docs" element={<Navigate to="/docs/introduction" replace />} />
        <Route path="/docs/introduction" element={<Layout type="docs"><DocsIntroduction /></Layout>} />
        <Route path="/docs/architecture" element={<Layout type="docs"><Architecture /></Layout>} />
        <Route path="/api" element={<Layout type="api"><ApiReference /></Layout>} />
        {/* Fallback routes */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </HashRouter>
  );
};

export default App;