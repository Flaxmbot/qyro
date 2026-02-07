import React from 'react';
import { HoloPanel } from '../components/HoloPanel';
import { Link } from 'react-router-dom';

export const Architecture: React.FC = () => {
  return (
    <div className="flex flex-col xl:flex-row gap-12 px-6 py-12 lg:px-12 lg:py-16">
      <div className="flex-1 max-w-4xl min-h-[100vh]">

        {/* Breadcrumb */}
        <div className="flex items-center gap-2 text-[10px] uppercase tracking-widest text-gray-500 mb-8 font-mono">
          <Link to="/" className="hover:text-white transition-colors">Docs</Link>
          <span className="text-white/20">/</span>
          <span>Core</span>
          <span className="text-white/20">/</span>
          <span className="text-white">Architecture</span>
        </div>

        {/* Title */}
        <h1 className="text-4xl md:text-5xl font-light tracking-tight text-white mb-6 relative">
          System Architecture
          <span className="absolute -left-8 top-2 w-1 h-8 bg-white shadow-[0_0_10px_white] hidden lg:block"></span>
        </h1>

        <p className="text-lg text-gray-400 leading-relaxed font-light mb-10 max-w-3xl">
          Qyro is a distributed polyglot runtime. It connects services written in different languages through a high-performance event bus, managing lifecycle, discovery, and state automatically.
        </p>

        {/* Diagram */}
        <div className="w-full aspect-[16/9] bg-black/40 border border-white/10 rounded-sm mb-16 relative overflow-hidden backdrop-blur-md flex items-center justify-center">
          {/* Grid Background */}
          <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.03)_1px,transparent_1px)] bg-[size:40px_40px]"></div>

          <svg viewBox="0 0 800 450" className="w-full h-full p-8 z-10">
            <defs>
              <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
                <feGaussianBlur stdDeviation="3" result="blur" />
                <feComposite in="SourceGraphic" in2="blur" operator="over" />
              </filter>
              <marker id="arrow" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto" markerUnits="strokeWidth">
                <path d="M0,0 L0,6 L9,3 z" fill="rgba(255,255,255,0.3)" />
              </marker>
            </defs>

            {/* Central Hub (Kafka/Redis) */}
            <g transform="translate(400, 225)">
              <circle r="60" fill="rgba(0,0,0,0.8)" stroke="#3b82f6" strokeWidth="2" filter="url(#glow)" />
              <circle r="45" fill="none" stroke="#3b82f6" strokeWidth="1" strokeDasharray="4 4" className="animate-[spin_10s_linear_infinite]" />
              <text x="0" y="-10" textAnchor="middle" fill="#3b82f6" fontSize="12" fontWeight="bold" style={{ textShadow: "0 0 10px rgba(59,130,246,0.8)" }}>EVENT BUS</text>
              <text x="0" y="10" textAnchor="middle" fill="#a5f3fc" fontSize="10" opacity="0.8">Kafka + Redis</text>
            </g>

            {/* Language Nodes - Positioning 6 nodes in a hexagon */}

            {/* Python (Top) */}
            <g transform="translate(400, 80)">
              <path d="M400,165 L400,120" stroke="rgba(255,255,255,0.2)" strokeWidth="2" markerEnd="url(#arrow)" transform="translate(-400, -80)" />
              <path d="M400,120 L400,165" stroke="rgba(255,255,255,0.2)" strokeWidth="2" markerEnd="url(#arrow)" transform="translate(-400, -80)" />

              <rect x="-40" y="-20" width="80" height="40" rx="4" fill="rgba(59,130,246,0.1)" stroke="#3b82f6" strokeWidth="1" />
              <text x="0" y="5" textAnchor="middle" fill="#fff" fontSize="12" fontWeight="bold">Python</text>
            </g>

            {/* Node.js (Top Right) */}
            <g transform="translate(525, 152)">
              <line x1="-35" y1="20" x2="-80" y2="50" stroke="rgba(255,255,255,0.2)" strokeWidth="2" />
              <rect x="-40" y="-20" width="80" height="40" rx="4" fill="rgba(34,197,94,0.1)" stroke="#22c55e" strokeWidth="1" />
              <text x="0" y="5" textAnchor="middle" fill="#fff" fontSize="12" fontWeight="bold">Node.js</text>
            </g>

            {/* Go (Bottom Right) */}
            <g transform="translate(525, 297)">
              <line x1="-35" y1="-20" x2="-80" y2="-50" stroke="rgba(255,255,255,0.2)" strokeWidth="2" />
              <rect x="-40" y="-20" width="80" height="40" rx="4" fill="rgba(6,182,212,0.1)" stroke="#06b6d4" strokeWidth="1" />
              <text x="0" y="5" textAnchor="middle" fill="#fff" fontSize="12" fontWeight="bold">Go</text>
            </g>

            {/* Java (Bottom) */}
            <g transform="translate(400, 370)">
              <line x1="0" y1="-40" x2="0" y2="-85" stroke="rgba(255,255,255,0.2)" strokeWidth="2" />
              <rect x="-40" y="-20" width="80" height="40" rx="4" fill="rgba(239,68,68,0.1)" stroke="#ef4444" strokeWidth="1" />
              <text x="0" y="5" textAnchor="middle" fill="#fff" fontSize="12" fontWeight="bold">Java</text>
            </g>

            {/* C++ (Bottom Left) */}
            <g transform="translate(275, 297)">
              <line x1="35" y1="-20" x2="80" y2="-50" stroke="rgba(255,255,255,0.2)" strokeWidth="2" />
              <rect x="-40" y="-20" width="80" height="40" rx="4" fill="rgba(168,85,247,0.1)" stroke="#a855f7" strokeWidth="1" />
              <text x="0" y="5" textAnchor="middle" fill="#fff" fontSize="12" fontWeight="bold">C++</text>
            </g>

            {/* Rust (Top Left) */}
            <g transform="translate(275, 152)">
              <line x1="35" y1="20" x2="80" y2="50" stroke="rgba(255,255,255,0.2)" strokeWidth="2" />
              <rect x="-40" y="-20" width="80" height="40" rx="4" fill="rgba(249,115,22,0.1)" stroke="#f97316" strokeWidth="1" />
              <text x="0" y="5" textAnchor="middle" fill="#fff" fontSize="12" fontWeight="bold">Rust</text>
            </g>

          </svg>
        </div>

        {/* Explanation Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-16">
          <HoloPanel>
            <div className="flex flex-col h-full">
              <h3 className="text-lg font-bold text-white mb-2 flex items-center gap-2">
                <span className="material-symbols-outlined text-green-400">check_circle</span>
                Orchestrator
              </h3>
              <p className="text-sm text-gray-400 flex-1">
                The Qyro CLI parses your `.qyro` file, builds Docker containers for each service, and manages their lifecycle. It handles hot-reloading and log aggregation.
              </p>
            </div>
          </HoloPanel>

          <HoloPanel>
            <div className="flex flex-col h-full">
              <h3 className="text-lg font-bold text-white mb-2 flex items-center gap-2">
                <span className="material-symbols-outlined text-blue-400">compare_arrows</span>
                Event Bus
              </h3>
              <p className="text-sm text-gray-400 flex-1">
                Services communicate via a central Kafka message bus. RPC calls are serialized to JSON and routed asynchronously. Redis handles shared state and service discovery.
              </p>
            </div>
          </HoloPanel>
        </div>


        {/* Footer Navigation */}
        <div className="border-t border-white/10 pt-10 flex justify-between">
          <Link to="/docs/introduction" className="group flex items-center gap-3 text-gray-500 hover:text-white transition-colors">
            <span className="material-symbols-outlined border border-white/10 p-2 rounded-sm group-hover:border-white/40 transition-colors">arrow_back</span>
            <div className="flex flex-col items-start">
              <span className="text-[10px] uppercase tracking-widest text-gray-600">Previous</span>
              <span className="text-sm font-bold">Introduction</span>
            </div>
          </Link>
          <Link to="/docs/bindings" className="group flex items-center gap-3 text-gray-500 hover:text-white transition-colors text-right">
            <div className="flex flex-col items-end">
              <span className="text-[10px] uppercase tracking-widest text-gray-600">Next</span>
              <span className="text-sm font-bold">Bindings</span>
            </div>
            <span className="material-symbols-outlined border border-white/10 p-2 rounded-sm group-hover:border-white/40 transition-colors">arrow_forward</span>
          </Link>
        </div>
      </div>
    </div>
  );
};