import React from 'react';
import { HoloPanel } from '../components/HoloPanel';
import { Link } from 'react-router-dom';

export const DocsIntroduction: React.FC = () => {
  return (
    <div className="flex flex-col xl:flex-row gap-12 px-6 py-12 lg:px-12 lg:py-16">
      {/* Main Content */}
      <div className="flex-1 max-w-4xl min-h-[100vh]">
        {/* Breadcrumb */}
        <div className="flex items-center gap-2 text-[10px] uppercase tracking-widest text-gray-500 mb-8 font-mono">
          <Link to="/" className="hover:text-white transition-colors">Docs</Link>
          <span className="text-white/20">/</span>
          <span>Start</span>
          <span className="text-white/20">/</span>
          <span className="text-white">Introduction</span>
        </div>

        {/* Title */}
        <h1 className="text-4xl md:text-5xl font-light tracking-tight text-white mb-6 relative">
          Introduction to Qyro
          <span className="absolute -left-8 top-2 w-1 h-8 bg-white shadow-[0_0_10px_white] hidden lg:block"></span>
        </h1>

        <p className="text-lg text-gray-400 leading-relaxed font-light mb-10 max-w-3xl">
          Qyro is a new way to build distributed systems. Instead of managing dozens of repositories, Dockerfiles, and Kubernetes manifests, you define your entire application stack—backend, frontend, workers, and databases—in a single <code className="text-holo-blue">.qyro</code> file.
        </p>

        {/* Info Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-12">
          {[
            { title: 'Single File Source', icon: 'description', desc: 'Define Python APIs, React Frontends, and Go Workers in one readable file.' },
            { title: 'Polyglot by Default', icon: 'translate', desc: 'Mix and match languages. Qyro handles the glue code, networking, and Docker builds.' }
          ].map((card, i) => (
            <div key={i} className="border border-white/10 bg-white/5 p-6 rounded-sm relative overflow-hidden group hover:border-white/30 transition-colors">
              <div className="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
              <div className="flex items-center gap-3 mb-3">
                <span className="material-symbols-outlined text-white/70">{card.icon}</span>
                <h3 className="text-sm font-bold text-white uppercase tracking-wider">{card.title}</h3>
              </div>
              <p className="text-xs text-gray-500 leading-relaxed">{card.desc}</p>
            </div>
          ))}
        </div>

        <div className="h-[1px] w-full bg-gradient-to-r from-white/20 via-white/5 to-transparent mb-12"></div>

        {/* Quick Start Section */}
        <h2 className="text-2xl font-light text-white mb-6 flex items-center gap-3">
          <span className="material-symbols-outlined text-white/50">terminal</span>
          Quick Start
        </h2>
        <p className="text-sm text-gray-500 mb-6 leading-relaxed max-w-2xl">
          Install Qyro via pip, create a new project, and run it. You'll need Docker installed.
        </p>

        {/* Code Block */}
        <div className="relative mb-16 group">
          <div className="absolute -inset-0.5 bg-gradient-to-r from-white/20 to-white/5 rounded-sm blur opacity-20 group-hover:opacity-40 transition duration-1000"></div>
          <HoloPanel noPadding className="rounded-sm">
            <div className="flex items-center justify-between px-4 py-3 border-b border-white/10 bg-white/5">
              <div className="flex items-center gap-4">
                <div className="flex gap-1.5">
                  <div className="size-2.5 rounded-full bg-gray-500/20 border border-gray-500/50"></div>
                  <div className="size-2.5 rounded-full bg-gray-500/20 border border-gray-500/50"></div>
                  <div className="size-2.5 rounded-full bg-gray-500/20 border border-gray-500/50"></div>
                </div>
                <span className="text-[10px] text-gray-400 font-mono uppercase tracking-wider">TERMINAL</span>
              </div>
              <div className="flex items-center gap-3">
                <button className="text-gray-500 hover:text-white transition-colors" onClick={() => navigator.clipboard.writeText('pip install qyro\nqyro init my-app\ncd my-app\nqyro run main.qyro')}>
                  <span className="material-symbols-outlined text-[16px]">content_copy</span>
                </button>
              </div>
            </div>
            <div className="p-6 overflow-x-auto">
              <pre className="font-mono text-xs sm:text-sm leading-relaxed">
                <span className="text-gray-500"># 1. Install Qyro</span>{'\n'}
                <span className="text-green-400">$</span> pip install qyro{'\n'}
                {'\n'}
                <span className="text-gray-500"># 2. Create a new project</span>{'\n'}
                <span className="text-green-400">$</span> qyro init my-app{'\n'}
                <span className="text-blue-300">Created project 'my-app'</span>{'\n'}
                <span className="text-blue-300">Generated main.qyro</span>{'\n'}
                {'\n'}
                <span className="text-gray-500"># 3. Run the stack</span>{'\n'}
                <span className="text-green-400">$</span> cd my-app{'\n'}
                <span className="text-green-400">$</span> qyro run main.qyro{'\n'}
                <span className="text-blue-300">[Orchestrator] Parsing main.qyro...</span>{'\n'}
                <span className="text-blue-300">[Orchestrator] Generating Docker compose...</span>{'\n'}
                <span className="text-green-400">[System] Stack running at http://localhost:8080</span>
              </pre>
            </div>
          </HoloPanel>
        </div>

        {/* Supported Languages */}
        <h3 className="text-xl font-light text-white mb-4">Supported Languages</h3>
        <p className="text-sm text-gray-500 mb-8 leading-relaxed">
          Qyro currently supports the following languages with full RPC and State integration:
        </p>
        <ul className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-16">
          {[
            { title: 'Python', desc: 'FastAPI, standard library support. Use for APIs and AI.' },
            { title: 'JavaScript / Node', desc: 'React, Express. Use for Frontends and IO-heavy workers.' },
            { title: 'Rust', desc: 'High-performance computing. Use for heavy data processing.' },
            { title: 'Go', desc: 'Concurrency and microservices.' },
          ].map((item, i) => (
            <li key={i} className="flex items-start gap-4 p-4 border border-white/5 bg-white/[0.02] hover:bg-white/[0.05] transition-colors rounded-sm">
              <span className="material-symbols-outlined text-holo-blue mt-1">check_circle</span>
              <div>
                <h4 className="text-sm font-bold text-white mb-1">{item.title}</h4>
                <p className="text-xs text-gray-500">{item.desc}</p>
              </div>
            </li>
          ))}
        </ul>

        {/* Footer Navigation */}
        <div className="flex items-center justify-between pt-10 border-t border-white/10">
          <Link to="/" className="group flex items-center gap-3 text-gray-500 hover:text-white transition-colors">
            <span className="material-symbols-outlined border border-white/10 p-2 rounded-sm group-hover:border-white/40 transition-colors">arrow_back</span>
            <div className="flex flex-col items-start">
              <span className="text-[10px] uppercase tracking-widest text-gray-600">Previous</span>
              <span className="text-sm font-bold">Home</span>
            </div>
          </Link>
          <Link to="/docs/architecture" className="group flex items-center gap-3 text-gray-500 hover:text-white transition-colors text-right">
            <div className="flex flex-col items-end">
              <span className="text-[10px] uppercase tracking-widest text-gray-600">Next</span>
              <span className="text-sm font-bold">Architecture</span>
            </div>
            <span className="material-symbols-outlined border border-white/10 p-2 rounded-sm group-hover:border-white/40 transition-colors">arrow_forward</span>
          </Link>
        </div>

        <footer className="mt-20 pt-10 border-t border-white/5">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4 text-[10px] text-gray-600 uppercase tracking-widest">
            <p>© 2024 QYRO INC.</p>
            <div className="flex gap-6">
              <a href="#" className="hover:text-white transition-colors">Github</a>
              <a href="https://discord.gg/qyro" target="_blank" rel="noreferrer" className="hover:text-white transition-colors">Discord</a>
            </div>
          </div>
        </footer>
      </div>

      {/* Right Sidebar (Table of Contents) */}
      <aside className="hidden xl:block w-64 sticky top-24 h-[calc(100vh-100px)] pt-12 pr-8">
        <div className="relative">
          <div className="absolute -left-4 top-0 bottom-0 w-[1px] bg-white/5"></div>
          <h4 className="text-[10px] font-bold text-gray-400 uppercase tracking-[0.2em] mb-6 pl-2">On This Page</h4>
          <nav className="flex flex-col space-y-1">
            <a href="#" className="text-xs text-white py-1.5 pl-4 relative before:absolute before:left-0 before:top-[14px] before:size-1 before:bg-white before:rounded-full hover:text-white transition-colors block">Introduction</a>
            <a href="#" className="text-xs text-gray-500 py-1.5 pl-4 relative before:absolute before:left-0 before:top-[14px] before:size-1 before:bg-white/20 before:rounded-full hover:text-gray-300 hover:before:bg-white transition-all block">Features</a>
            <a href="#" className="text-xs text-gray-500 py-1.5 pl-4 relative before:absolute before:left-0 before:top-[14px] before:size-1 before:bg-white/20 before:rounded-full hover:text-gray-300 hover:before:bg-white transition-all block">Quick Start</a>
            <a href="#" className="text-xs text-gray-500 py-1.5 pl-4 relative before:absolute before:left-0 before:top-[14px] before:size-1 before:bg-white/20 before:rounded-full hover:text-gray-300 hover:before:bg-white transition-all block">Languages</a>
          </nav>
        </div>
      </aside>
    </div>
  );
};