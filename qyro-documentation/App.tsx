import React from 'react';
import { HashRouter, Routes, Route, useLocation, Navigate } from 'react-router-dom';
import { Layout } from './components/Layout';
import { Home } from './pages/Home';
import { DocsIntroduction } from './pages/DocsIntroduction';
import { Installation } from './pages/Installation';
import { HelloWorld } from './pages/HelloWorld';
import { Bindings } from './pages/Bindings';
import { Sandboxing } from './pages/Sandboxing';
import { GuidePython } from './pages/GuidePython';
import { GuideNode } from './pages/GuideNode';
import { GuideRust } from './pages/GuideRust';
import { GuideGo } from './pages/GuideGo';
import { CliReference } from './pages/CliReference';
import { ConfigReference } from './pages/ConfigReference';
import { AdvancedPatterns } from './pages/AdvancedPatterns';
import { Deployment } from './pages/Deployment';
import { Contributing } from './pages/Contributing';
import { Blog } from './pages/Blog';
import { Troubleshooting } from './pages/Troubleshooting';
import { Changelog } from './pages/Changelog';
import { Roadmap } from './pages/Roadmap';
import { NotFound } from './pages/NotFound';
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
        <Route path="/" element={<Layout><Home /></Layout>} />
        <Route path="/docs" element={<Navigate to="/docs/introduction" replace />} />
        <Route path="/docs/introduction" element={<Layout><DocsIntroduction /></Layout>} />
        <Route path="/docs/installation" element={<Layout><Installation /></Layout>} />
        <Route path="/docs/hello-world" element={<Layout><HelloWorld /></Layout>} />
        <Route path="/docs/architecture" element={<Layout><Architecture /></Layout>} />
        <Route path="/docs/bindings" element={<Layout><Bindings /></Layout>} />
        <Route path="/docs/sandboxing" element={<Layout><Sandboxing /></Layout>} />
        <Route path="/docs/guides/python" element={<Layout><GuidePython /></Layout>} />
        <Route path="/docs/guides/node" element={<Layout><GuideNode /></Layout>} />
        <Route path="/docs/guides/rust" element={<Layout><GuideRust /></Layout>} />
        <Route path="/docs/guides/go" element={<Layout><GuideGo /></Layout>} />

        <Route path="/docs/reference/cli" element={<Layout><CliReference /></Layout>} />
        <Route path="/docs/reference/config" element={<Layout><ConfigReference /></Layout>} />

        <Route path="/docs/resources/advanced" element={<Layout><AdvancedPatterns /></Layout>} />
        <Route path="/docs/resources/deployment" element={<Layout><Deployment /></Layout>} />
        <Route path="/docs/resources/contributing" element={<Layout><Contributing /></Layout>} />

        <Route path="/blog" element={<Layout><Blog /></Layout>} />

        <Route path="/docs/resources/troubleshooting" element={<Layout><Troubleshooting /></Layout>} />
        <Route path="/docs/resources/changelog" element={<Layout><Changelog /></Layout>} />
        <Route path="/docs/resources/roadmap" element={<Layout><Roadmap /></Layout>} />

        <Route path="/api" element={<Layout><ApiReference /></Layout>} />
        {/* Fallback routes */}
        <Route path="*" element={<Layout><NotFound /></Layout>} />
      </Routes>
    </HashRouter>
  );
};

export default App;