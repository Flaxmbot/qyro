import React from 'react';
import { HoloPanel } from '../components/HoloPanel';
import { Link } from 'react-router-dom';

export const Architecture: React.FC = () => {
  return (
    <div className="max-w-6xl mx-auto px-6 py-12 lg:py-16 flex flex-col min-h-screen">
      <div className="mb-12 border-b border-white/10 pb-8 relative animate-slide-up">
        <h1 className="text-4xl md:text-5xl font-light tracking-tighter text-white mb-4">Architecture</h1>
        <p className="text-gray-400 max-w-2xl font-light text-lg">
          The Qyro Runtime orchestrates multi-language execution through a shared-memory buffer system, eliminating serialization overhead.
        </p>
        <div className="absolute bottom-0 left-0 w-32 h-[1px] bg-white shadow-[0_0_10px_white]"></div>
      </div>

      {/* SVG Reactor Diagram */}
      <div className="relative w-full aspect-[16/9] md:h-[600px] bg-black/40 border border-white/10 rounded-lg overflow-hidden mb-16 shadow-2xl animate-fade-in group">
        <div className="absolute inset-0 bg-grid-holographic opacity-20"></div>
        <div className="absolute inset-0 bg-radial-gradient from-blue-900/10 via-transparent to-black"></div>
        
        <svg viewBox="0 0 800 500" className="w-full h-full relative z-10" preserveAspectRatio="xMidYMid meet">
          <defs>
            <linearGradient id="grad-pipe" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.1" />
              <stop offset="50%" stopColor="#a5f3fc" stopOpacity="0.8" />
              <stop offset="100%" stopColor="#3b82f6" stopOpacity="0.1" />
            </linearGradient>
            <linearGradient id="grad-core" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#1e3a8a" />
              <stop offset="100%" stopColor="#000000" />
            </linearGradient>
            <filter id="glow-blue" x="-50%" y="-50%" width="200%" height="200%">
              <feGaussianBlur stdDeviation="3" result="coloredBlur" />
              <feMerge>
                <feMergeNode in="coloredBlur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
            <mask id="mask-ring">
               <rect x="0" y="0" width="800" height="500" fill="white" />
               <circle cx="400" cy="250" r="40" fill="black" />
            </mask>
          </defs>

          {/* Central Hub Rings */}
          <g transform="translate(400, 250)">
             {/* Outer Spinner */}
             <circle cx="0" cy="0" r="140" fill="none" stroke="#1e40af" strokeWidth="1" strokeDasharray="10 20" opacity="0.3" className="animate-spin-slow" />
             <circle cx="0" cy="0" r="120" fill="none" stroke="#a5f3fc" strokeWidth="1" strokeDasharray="4 4" opacity="0.2" className="animate-reverse-spin" />
             
             {/* Core */}
             <circle cx="0" cy="0" r="60" fill="url(#grad-core)" stroke="#a5f3fc" strokeWidth="2" filter="url(#glow-blue)" />
             <text x="0" y="5" textAnchor="middle" fill="#ffffff" fontSize="12" fontFamily="monospace" letterSpacing="2" className="animate-pulse">KERNEL</text>
             
             {/* Core Particles */}
             <circle cx="0" cy="0" r="45" fill="none" stroke="white" strokeWidth="1" strokeDasharray="60 120" className="animate-spin-slow" opacity="0.5" />
          </g>

          {/* Connections & Data Flow */}
          {/* Defined paths for data flow */}
          <g fill="none" stroke="url(#grad-pipe)" strokeWidth="2" filter="url(#glow-blue)">
            {/* Top Left (Python) */}
            <path d="M 150 100 L 250 100 L 400 200" opacity="0.3" />
            <path d="M 150 100 L 250 100 L 400 200" strokeDasharray="10 100" className="animate-dash" strokeLinecap="round" />
            
            {/* Top Right (Rust) */}
            <path d="M 650 100 L 550 100 L 400 200" opacity="0.3" />
            <path d="M 650 100 L 550 100 L 400 200" strokeDasharray="10 100" className="animate-dash" strokeLinecap="round" style={{animationDelay: '1s'}} />

            {/* Bottom Left (Node) */}
            <path d="M 150 400 L 250 400 L 400 300" opacity="0.3" />
            <path d="M 150 400 L 250 400 L 400 300" strokeDasharray="10 100" className="animate-dash" strokeLinecap="round" style={{animationDelay: '0.5s'}} />

            {/* Bottom Right (Go) */}
            <path d="M 650 400 L 550 400 L 400 300" opacity="0.3" />
            <path d="M 650 400 L 550 400 L 400 300" strokeDasharray="10 100" className="animate-dash" strokeLinecap="round" style={{animationDelay: '1.5s'}} />
          </g>

          {/* Language Nodes - REFACTORED FOR STABLE HOVER */}
          {/* Node 1: Python */}
          <g transform="translate(150, 100)" className="group cursor-pointer">
            {/* Invisible stable hit area - Increased radius to prevent jitter */}
            <circle r="50" fill="transparent" />
            {/* Animated content */}
            <g className="transition-transform duration-300 group-hover:scale-110 origin-center">
                <polygon points="0,-30 26,-15 26,15 0,30 -26,15 -26,-15" fill="#000" stroke="#3776AB" strokeWidth="2" filter="url(#glow-blue)" />
                <foreignObject x="-15" y="-15" width="30" height="30">
                  <div className="flex items-center justify-center w-full h-full text-[#3776AB]">
                    <span className="material-symbols-outlined" style={{fontSize: '24px'}}>code</span>
                  </div>
                </foreignObject>
                <text x="0" y="45" textAnchor="middle" fill="#3776AB" fontSize="10" fontFamily="monospace">PYTHON</text>
            </g>
          </g>

          {/* Node 2: Rust */}
          <g transform="translate(650, 100)" className="group cursor-pointer">
             <circle r="50" fill="transparent" />
             <g className="transition-transform duration-300 group-hover:scale-110 origin-center">
                <polygon points="0,-30 26,-15 26,15 0,30 -26,15 -26,-15" fill="#000" stroke="#DEA584" strokeWidth="2" filter="url(#glow-blue)" />
                <foreignObject x="-15" y="-15" width="30" height="30">
                  <div className="flex items-center justify-center w-full h-full text-[#DEA584]">
                    <span className="material-symbols-outlined" style={{fontSize: '24px'}}>settings</span>
                  </div>
                </foreignObject>
                <text x="0" y="45" textAnchor="middle" fill="#DEA584" fontSize="10" fontFamily="monospace">RUST</text>
            </g>
          </g>

          {/* Node 3: Node.js */}
          <g transform="translate(150, 400)" className="group cursor-pointer">
             <circle r="50" fill="transparent" />
             <g className="transition-transform duration-300 group-hover:scale-110 origin-center">
                <polygon points="0,-30 26,-15 26,15 0,30 -26,15 -26,-15" fill="#000" stroke="#68A063" strokeWidth="2" filter="url(#glow-blue)" />
                 <foreignObject x="-15" y="-15" width="30" height="30">
                  <div className="flex items-center justify-center w-full h-full text-[#68A063]">
                    <span className="material-symbols-outlined" style={{fontSize: '24px'}}>javascript</span>
                  </div>
                </foreignObject>
                <text x="0" y="45" textAnchor="middle" fill="#68A063" fontSize="10" fontFamily="monospace">NODE</text>
            </g>
          </g>

          {/* Node 4: Go */}
          <g transform="translate(650, 400)" className="group cursor-pointer">
             <circle r="50" fill="transparent" />
             <g className="transition-transform duration-300 group-hover:scale-110 origin-center">
                <polygon points="0,-30 26,-15 26,15 0,30 -26,15 -26,-15" fill="#000" stroke="#00D8FF" strokeWidth="2" filter="url(#glow-blue)" />
                 <foreignObject x="-15" y="-15" width="30" height="30">
                  <div className="flex items-center justify-center w-full h-full text-[#00D8FF]">
                    <span className="material-symbols-outlined" style={{fontSize: '24px'}}>terminal</span>
                  </div>
                </foreignObject>
                <text x="0" y="45" textAnchor="middle" fill="#00D8FF" fontSize="10" fontFamily="monospace">GO</text>
            </g>
          </g>
        </svg>

        <div className="absolute bottom-4 right-4 text-[10px] text-gray-500 font-mono bg-black/50 px-2 py-1 rounded border border-white/10">
            SYSTEM_STATUS: ACTIVE<br/>
            LINK_INTEGRITY: 99.9%
        </div>
      </div>

      {/* Feature Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-16 animate-slide-up" style={{ animationDelay: '200ms' }}>
        <HoloPanel className="h-full">
            <div className="absolute top-0 right-0 p-4 opacity-20 group-hover:opacity-40 transition-opacity">
                <span className="material-symbols-outlined text-9xl text-holo-blue">bolt</span>
            </div>
            <h3 className="text-xl font-bold text-white mb-2 flex items-center gap-3 relative z-10">
                <span className="material-symbols-outlined text-holo-blue">bolt</span>
                Zero-Copy Bindings
            </h3>
            <p className="text-sm text-gray-400 leading-relaxed mb-6 relative z-10">
                Traditional FFI requires expensive serialization. Qyro maps data structures directly into shared memory pages, allowing different languages to read/write the same bytes without copying.
            </p>
            <div className="w-full h-32 bg-black/50 border border-white/10 rounded flex items-center justify-center relative overflow-hidden z-10">
                <div className="absolute inset-0 bg-grid-holographic opacity-30"></div>
                <div className="flex items-center gap-8 relative z-10">
                    <div className="text-center">
                        <div className="text-[10px] text-gray-500 mb-1">PYTHON</div>
                        <div className="w-16 h-12 border border-blue-500/50 bg-blue-500/10 rounded flex items-center justify-center text-[10px] font-mono text-blue-300">0x7F...A1</div>
                    </div>
                    <div className="flex-1 h-[1px] w-20 bg-gradient-to-r from-blue-500/50 to-orange-500/50"></div>
                    <div className="text-center">
                        <div className="text-[10px] text-gray-500 mb-1">RUST</div>
                        <div className="w-16 h-12 border border-orange-500/50 bg-orange-500/10 rounded flex items-center justify-center text-[10px] font-mono text-orange-300">0x7F...A1</div>
                    </div>
                </div>
                <div className="absolute bottom-2 left-0 right-0 text-center text-[9px] text-gray-600 font-mono uppercase tracking-widest">Same Physical Address</div>
            </div>
        </HoloPanel>

        <HoloPanel className="h-full">
            <div className="absolute top-0 right-0 p-4 opacity-20 group-hover:opacity-40 transition-opacity">
                 <span className="material-symbols-outlined text-9xl text-green-400">memory</span>
            </div>
            <h3 className="text-xl font-bold text-white mb-2 flex items-center gap-3 relative z-10">
                <span className="material-symbols-outlined text-green-400">memory</span>
                Shared State Atomicity
            </h3>
            <p className="text-sm text-gray-400 leading-relaxed mb-6 relative z-10">
                Manage global state across module boundaries with built-in atomic primitives. Qyro handles the locking mechanisms, ensuring thread-safe access from any guest language.
            </p>
            <div className="w-full h-32 bg-black/50 border border-white/10 rounded flex items-center justify-center relative overflow-hidden z-10">
                <div className="absolute inset-0 bg-grid-holographic opacity-30"></div>
                <div className="relative z-10 w-full px-8">
                    <div className="flex justify-between mb-2">
                        <div className="text-[9px] text-gray-500 font-mono">THREAD A (JS)</div>
                        <div className="text-[9px] text-gray-500 font-mono">THREAD B (GO)</div>
                    </div>
                    <div className="h-10 w-full border border-white/20 rounded bg-white/5 relative flex items-center justify-center">
                        <div className="absolute left-0 top-0 bottom-0 w-1/2 bg-green-500/10 border-r border-green-500/30 flex items-center justify-center">
                            <span className="text-[10px] text-green-400 font-mono">READ</span>
                        </div>
                        <div className="absolute right-0 top-0 bottom-0 w-1/2 bg-red-500/10 border-l border-red-500/30 flex items-center justify-center">
                            <span className="text-[10px] text-red-400 font-mono">BLOCKED</span>
                        </div>
                        <div className="absolute inset-0 flex items-center justify-center">
                            <span className="material-symbols-outlined text-white/50 text-sm">lock</span>
                        </div>
                    </div>
                </div>
            </div>
        </HoloPanel>
      </div>

      <div className="border-t border-white/10 pt-10 mt-auto">
        <div className="flex items-center justify-between">
          <Link to="/docs/introduction" className="flex items-center gap-2 text-gray-500 hover:text-white transition-colors group">
            <span className="material-symbols-outlined text-lg group-hover:-translate-x-1 transition-transform">arrow_back</span>
            <span className="text-xs uppercase tracking-widest font-bold">Introduction</span>
          </Link>
          <a href="#" className="flex items-center gap-2 text-gray-500 hover:text-white transition-colors group">
            <span className="text-xs uppercase tracking-widest font-bold">Memory Safety</span>
            <span className="material-symbols-outlined text-lg group-hover:translate-x-1 transition-transform">arrow_forward</span>
          </a>
        </div>
      </div>
      
      <footer className="mt-20 pt-10 border-t border-white/5">
        <div className="flex flex-col md:flex-row justify-between items-center gap-4 text-[10px] text-gray-600 uppercase tracking-widest">
            <p>© 2024 QYRO INC.</p>
            <div className="flex gap-6">
                <a href="#" className="hover:text-white transition-colors">Privacy</a>
                <a href="#" className="hover:text-white transition-colors">Terms</a>
                <a href="#" className="hover:text-white transition-colors">Status</a>
            </div>
        </div>
      </footer>
    </div>
  );
};