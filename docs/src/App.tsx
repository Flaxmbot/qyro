
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from './layouts/Layout';
import { Home } from './pages/Home';
import { QuickStart } from './pages/QuickStart';
import { Architecture } from './pages/Architecture';
import { Configuration } from './pages/Configuration';
import { Reference } from './pages/Reference';
import { Polyglot } from './pages/Polyglot';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Home />} />
          <Route path="quick-start" element={<QuickStart />} />
          <Route path="architecture" element={<Architecture />} />
          <Route path="configuration" element={<Configuration />} />
          <Route path="api" element={<Reference />} />
          <Route path="polyglot" element={<Polyglot />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
