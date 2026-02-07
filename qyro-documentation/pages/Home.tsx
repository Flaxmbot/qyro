import React from 'react';
import { Link } from 'react-router-dom';
import { HoloPanel } from '../components/HoloPanel';

export const Home: React.FC = () => {
  return (
    <div className="flex flex-col items-center justify-center min-h-[85vh] text-center relative px-4 py-16">
      {/* Vertical Line Decoration */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[1px] h-20 bg-gradient-to-b from-white/20 to-transparent"></div>

      {/* System Status Badge */}
      <div className="animate-slide-up inline-flex items-center gap-3 px-4 py-2 border border-white/10 bg-black/60 backdrop-blur-md text-xs font-mono uppercase tracking-widest mb-10 shadow-[0_0_15px_rgba(255,255,255,0.05)] hover:border-white/40 transition-colors text-gray-300">
        <span className="size-1.5 bg-green-500 shadow-[0_0_8px_#22c55e] rounded-full animate-pulse"></span>
        <span>Runtime Active</span>
      </div>

      {/* Main Hero Title */}
      <h1
        className="text-7xl md:text-9xl font-light tracking-tighter mb-8 relative z-10 text-white mix-blend-screen animate-flicker select-none"
        style={{ textShadow: "0 0 30px rgba(255,255,255,0.1)" }}
      >
        QYRO
      </h1>

      <div className="h-[1px] w-32 bg-white/50 mb-8 shadow-[0_0_10px_white] animate-fade-in" style={{ animationDelay: "0.2s" }}></div>

      <p className="animate-slide-up text-lg md:text-xl text-gray-300 font-light mb-4 max-w-2xl leading-relaxed tracking-wide" style={{ animationDelay: "0.3s" }}>
        The Universal Polyglot Runtime
      </p>

      <p className="animate-slide-up text-sm text-gray-500 mb-12 max-w-lg leading-relaxed font-mono" style={{ animationDelay: "0.4s" }}>
        // BUILD DISTRIBUTED SYSTEMS IN A SINGLE FILE <br />
        // PYTHON • RUST • NODE • GO • JAVA • C++
      </p>

      {/* Language Icons */}
      <div className="flex flex-wrap justify-center items-center gap-10 mb-16 relative animate-slide-up" style={{ animationDelay: "0.5s" }}>
        <div className="absolute top-1/2 left-0 right-0 h-[1px] bg-white/10 -z-10"></div>
        {[
          { icon: 'code', label: 'Python', color: '#3776AB' },
          { icon: 'settings', label: 'Rust', color: '#DEA584' },
          { icon: 'terminal', label: 'Go', color: '#00D8FF' },
          { icon: 'coffee', label: 'Java', color: '#5382A1' },
          { icon: 'javascript', label: 'Node', color: '#68A063' },
          { icon: 'integration_instructions', label: 'C++', color: '#00599C' },
        ].map((lang) => (
          <div key={lang.label} className="group relative flex flex-col items-center gap-3 cursor-default p-2 bg-black rounded-none border border-transparent transition-transform hover:scale-110 duration-300">
            <div
              className="size-10 flex items-center justify-center transition-all duration-300 filter grayscale brightness-125 group-hover:grayscale-0 group-hover:drop-shadow-[0_0_8px_currentColor]"
              style={{ color: lang.color }}
            >
              <span className="material-symbols-outlined text-4xl">{lang.icon}</span>
            </div>
            <span className="text-[10px] uppercase tracking-widest text-gray-600 group-hover:text-white transition-colors absolute -bottom-8 opacity-0 group-hover:opacity-100">
              {lang.label}
            </span>
          </div>
        ))}
      </div>

      {/* CTA Buttons */}
      <div className="flex flex-col sm:flex-row items-center gap-6 w-full sm:w-auto mb-20 animate-slide-up" style={{ animationDelay: "0.6s" }}>
        <Link to="/docs/introduction" className="relative group w-full sm:w-auto overflow-hidden">
          <div className="absolute inset-0 bg-white translate-y-full group-hover:translate-y-0 transition-transform duration-300"></div>
          <div className="relative flex items-center justify-center gap-3 px-10 py-4 bg-transparent border border-white text-white group-hover:text-black transition-colors font-bold uppercase tracking-[0.15em] text-sm">
            <span>Get Started</span>
            <span className="material-symbols-outlined text-[18px] group-hover:translate-x-1 transition-transform">arrow_forward</span>
          </div>
        </Link>
        <a href="https://github.com/Flaxmbot/qyro" target="_blank" rel="noreferrer" className="flex items-center justify-center gap-3 w-full sm:w-auto px-10 py-4 bg-transparent border border-white/20 text-gray-400 hover:text-white hover:border-white/60 transition-all font-mono text-xs uppercase tracking-widest group">
          <span>GitHub</span>
          <span className="material-symbols-outlined text-[16px] group-hover:rotate-45 transition-transform">arrow_outward</span>
        </a>
      </div>

      {/* Code Snippet */}
      <div className="w-full max-w-3xl relative mt-8 perspective-1000 group animate-fade-in" style={{ animationDelay: "0.8s" }}>
        <div className="absolute -top-20 left-1/2 -translate-x-1/2 w-[1px] h-20 bg-gradient-to-b from-transparent to-white/30"></div>
        <div className="absolute -top-1 left-1/2 -translate-x-1/2 w-2 h-2 bg-white rounded-full shadow-[0_0_10px_white]"></div>

        <HoloPanel>
          <div className="flex items-center justify-between mb-6 border-b border-white/10 pb-4">
            <div className="text-[10px] text-gray-500 font-mono uppercase tracking-widest">
              <span className="text-white mr-2">&gt;&gt;&gt;</span>myapp.qyro
            </div>
            <div className="flex gap-1.5">
              <div className="size-1 bg-white/30 rounded-full"></div>
              <div className="size-1 bg-white/30 rounded-full"></div>
              <div className="size-1 bg-white/30 rounded-full"></div>
            </div>
          </div>
          <pre className="font-mono text-xs sm:text-sm leading-loose text-left overflow-x-auto whitespace-pre-wrap">
            <span className="text-gray-500"># Define your entire stack in one file</span>{'\n'}
            {'\n'}
            <span className="text-blue-400 font-bold">&gt;&gt;&gt;python:api [fastapi]</span>{'\n'}
            <span className="text-purple-400">from</span> qyro_adapters <span className="text-purple-400">import</span> expose{'\n'}
            {'\n'}
            <span className="text-yellow-300">@expose</span>{'\n'}
            <span className="text-purple-400">def</span> <span className="text-blue-300">hello</span>(name: <span className="text-green-300">str</span>):{'\n'}
            {'    '}<span className="text-purple-400">return</span> <span className="text-green-300">f"Hello {'{name}'} from Python!"</span>{'\n'}
            {'\n'}
            <span className="text-blue-400 font-bold">&gt;&gt;&gt;web:frontend [react]</span>{'\n'}
            <span className="text-purple-400">import</span> {'{ call }'} <span className="text-purple-400">from</span> <span className="text-green-300">'./qyro_adapters/js_adapter'</span>;{'\n'}
            {'\n'}
            <span className="text-purple-400">export</span> <span className="text-purple-400">default</span> <span className="text-purple-400">function</span> <span className="text-blue-300">App</span>() {'{'}{'\n'}
            {'  '}<span className="text-purple-400">const</span> [msg, setMsg] = <span className="text-blue-300">useState</span>(<span className="text-green-300">""</span>);{'\n'}
            {'  '}<span className="text-purple-400">return</span> <span className="text-blue-300">&lt;button</span> <span className="text-orange-300">onClick</span>={'{}'}=&gt; call(<span className="text-green-300">"api.hello"</span>, <span className="text-green-300">"User"</span>).then(setMsg){'}'}&gt;{'\n'}
            {'    '}Call Backend{'\n'}
            {'  '}<span className="text-blue-300">&lt;/button&gt;</span>;{'\n'}
            {'}'}
          </pre>
        </HoloPanel>

        <div className="absolute -bottom-10 left-0 right-0 h-20 bg-gradient-to-b from-white/5 to-transparent blur-xl transform scale-y-[-0.5] opacity-30"></div>
      </div>

      {/* Feature Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-px bg-white/10 mt-32 w-full max-w-5xl border border-white/10 rounded-sm overflow-hidden animate-slide-up" style={{ animationDelay: "1s" }}>
        {[
          { title: 'Single File', icon: 'description', desc: 'Define backend, frontend, and workers in a single .qyro file. Qyro handles the Docker generation.' },
          { title: 'Cross-Lang RPC', icon: 'hub', desc: 'Call functions across languages naturally. Python calls Rust, Node calls Go—no API boilerplate needed.' },
          { title: 'Hot Reload', icon: 'sync', desc: 'Instant feedback loop. Edit your .qyro file and services update automatically in real-time.' },
        ].map((feature, i) => (
          <div key={i} className="bg-black p-8 hover:bg-white/5 transition-colors group/card relative overflow-hidden">
            <div className="absolute top-0 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-white/50 to-transparent translate-x-[-100%] group-hover/card:translate-x-[100%] transition-transform duration-1000"></div>
            <div className="mb-6 text-white group-hover/card:scale-110 transition-transform duration-500 origin-left">
              <span className="material-symbols-outlined font-light text-4xl">{feature.icon}</span>
            </div>
            <h3 className="text-sm font-bold text-white uppercase tracking-widest mb-3">{feature.title}</h3>
            <p className="text-xs text-gray-500 leading-relaxed">{feature.desc}</p>
          </div>
        ))}
      </div>

      <footer className="w-full border-t border-white/10 py-12 px-8 bg-black z-10 relative mt-32">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row justify-between items-center gap-6">
          <div className="flex items-center gap-2">
            <span className="size-2 bg-blue-500 rounded-full animate-pulse"></span>
            <p className="text-gray-600 text-xs font-mono uppercase">Qyro v1.0.0</p>
          </div>
          <p className="text-gray-800 text-xs font-mono">© 2024 QYRO TEAM</p>
        </div>
      </footer>
    </div>
  );
};