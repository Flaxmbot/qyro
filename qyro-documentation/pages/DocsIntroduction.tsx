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
          Qyro is a universal polyglot runtime designed for modern SaaS architectures. It unifies execution layers across languages, providing zero-latency bindings and secure sandboxing out of the box.
        </p>

        {/* Info Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-12">
          {[
            { title: 'Zero Latency', icon: 'speed', desc: 'Direct memory access eliminating serialization overhead between guest languages.' },
            { title: 'Sandboxed', icon: 'security', desc: 'Granular permission controls for file system, network, and environment access.' }
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
          Initialize the runtime and load your modules. Qyro automatically detects language bindings and optimizes the execution path.
        </p>

        {/* Code Block */}
        <div className="relative mb-16 group">
          <div className="absolute -inset-0.5 bg-gradient-to-r from-white/20 to-white/5 rounded-sm blur opacity-20 group-hover:opacity-40 transition duration-1000"></div>
          <HoloPanel noPadding className="rounded-sm">
            <div className="flex items-center justify-between px-4 py-3 border-b border-white/10 bg-white/5">
              <div className="flex items-center gap-4">
                <div className="flex gap-1.5">
                  <div className="size-2.5 rounded-full bg-red-500/20 border border-red-500/50"></div>
                  <div className="size-2.5 rounded-full bg-yellow-500/20 border border-yellow-500/50"></div>
                  <div className="size-2.5 rounded-full bg-green-500/20 border border-green-500/50"></div>
                </div>
                <span className="text-[10px] text-gray-400 font-mono uppercase tracking-wider">server.js</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-[10px] text-gray-600 font-mono">Qyro v2.4</span>
                <button className="text-gray-500 hover:text-white transition-colors">
                  <span className="material-symbols-outlined text-[16px]">content_copy</span>
                </button>
              </div>
            </div>
            <div className="p-6 overflow-x-auto">
              <pre className="font-mono text-xs sm:text-sm leading-relaxed">
                <span className="text-purple-400">import</span> {'{ Qyro, Buffer }'} <span className="text-purple-400">from</span> <span className="text-green-300">'@qyro/sdk'</span>;{'\n'}
                <span className="text-gray-500">// Initialize high-performance runtime</span>{'\n'}
                <span className="text-purple-400">const</span> runtime = <span className="text-purple-400">new</span> <span className="text-blue-300">Qyro</span>{'{'}{'\n'}
                {'    '}<span className="text-yellow-200">memory_limit</span>: <span className="text-orange-300">512</span>, <span className="text-gray-500">// MB</span>{'\n'}
                {'    '}<span className="text-yellow-200">jit_optimization</span>: <span className="text-blue-300">true</span>{'\n'}
                {'}'});{'\n'}
                <span className="text-gray-500">// Load Rust module with zero-copy binding</span>{'\n'}
                <span className="text-purple-400">await</span> runtime.<span className="text-blue-300">loadModule</span>(<span className="text-green-300">'./processor.rs'</span>);{'\n'}
                <span className="text-purple-400">export</span> <span className="text-purple-400">default</span> <span className="text-purple-400">async</span> <span className="text-purple-400">function</span> <span className="text-blue-300">handler</span>(<span className="text-orange-300">req</span>) {'{'}{'\n'}
                {'    '}<span className="text-purple-400">const</span> data = <span className="text-purple-400">new</span> <span className="text-blue-300">Buffer</span>(req.body);{'\n'}
                {'    '}<span className="text-gray-500">// Cross-language execution</span>{'\n'}
                {'    '}<span className="text-purple-400">return</span> runtime.<span className="text-blue-300">invoke</span>(<span className="text-green-300">'process_secure'</span>, data);{'\n'}
                {'}'}
              </pre>
            </div>
          </HoloPanel>
        </div>

        {/* Supported Architectures */}
        <h3 className="text-xl font-light text-white mb-4">Supported Architectures</h3>
        <p className="text-sm text-gray-500 mb-8 leading-relaxed">
          Qyro runs anywhere. From edge devices to massive server clusters, the runtime adapts to the underlying hardware capabilities.
        </p>
        <ul className="space-y-4 mb-16">
          {[
            { title: 'x86_64 Support', desc: 'Native optimization for Intel and AMD processors with AVX-512 acceleration.' },
            { title: 'ARM64 / Apple Silicon', desc: 'First-class support for M1/M2/M3 chips and AWS Graviton instances.' }
          ].map((item, i) => (
            <li key={i} className="flex items-start gap-4 p-4 border border-white/5 bg-white/[0.02] hover:bg-white/[0.05] transition-colors rounded-sm">
              <span className="material-symbols-outlined text-green-400 mt-1">check_circle</span>
              <div>
                <h4 className="text-sm font-bold text-white mb-1">{item.title}</h4>
                <p className="text-xs text-gray-500">{item.desc}</p>
              </div>
            </li>
          ))}
        </ul>

        {/* Footer Navigation */}
        <div className="flex items-center justify-between pt-10 border-t border-white/10">
          <Link to="/docs/installation" className="group flex items-center gap-3 text-gray-500 hover:text-white transition-colors">
            <span className="material-symbols-outlined border border-white/10 p-2 rounded-sm group-hover:border-white/40 transition-colors">arrow_back</span>
            <div className="flex flex-col items-start">
              <span className="text-[10px] uppercase tracking-widest text-gray-600">Previous</span>
              <span className="text-sm font-bold">Installation</span>
            </div>
          </Link>
          <Link to="/docs/hello-world" className="group flex items-center gap-3 text-gray-500 hover:text-white transition-colors text-right">
            <div className="flex flex-col items-end">
              <span className="text-[10px] uppercase tracking-widest text-gray-600">Next</span>
              <span className="text-sm font-bold">Hello World</span>
            </div>
            <span className="material-symbols-outlined border border-white/10 p-2 rounded-sm group-hover:border-white/40 transition-colors">arrow_forward</span>
          </Link>
        </div>

        <footer className="mt-20 pt-10 border-t border-white/5">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4 text-[10px] text-gray-600 uppercase tracking-widest">
            <p>© 2024 QYRO INC.</p>
            <div className="flex gap-6">
              <a href="#" className="hover:text-white transition-colors">Github</a>
              <a href="#" className="hover:text-white transition-colors">Twitter</a>
              <a href="#" className="hover:text-white transition-colors">Discord</a>
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
            <a href="#" className="text-xs text-gray-500 py-1.5 pl-4 relative before:absolute before:left-0 before:top-[14px] before:size-1 before:bg-white/20 before:rounded-full hover:text-gray-300 hover:before:bg-white transition-all block">Architectures</a>
          </nav>

          <div className="mt-12 p-4 border border-white/10 bg-white/[0.02] rounded-sm">
            <h5 className="text-[10px] font-bold text-white uppercase tracking-wider mb-2 flex items-center gap-2">
              <span className="size-1.5 bg-green-500 rounded-full animate-pulse"></span>
              Community
            </h5>
            <p className="text-[10px] text-gray-500 leading-relaxed mb-3">Join our Discord server for real-time support.</p>
            <button className="w-full py-1.5 text-[10px] font-bold uppercase tracking-widest border border-white/20 text-gray-400 hover:text-white hover:border-white/50 hover:bg-white/5 transition-all">
              Join Discord
            </button>
          </div>
        </div>
      </aside>
    </div>
  );
};