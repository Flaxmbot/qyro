import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Sidebar } from './Sidebar';

interface LayoutProps {
  children: React.ReactNode;
  type: 'docs' | 'api';
}

export const Layout: React.FC<LayoutProps> = ({ children, type }) => {
  // Sidebar state
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const location = useLocation();

  const isActive = (path: string) => location.pathname.startsWith(path);

  // Handlers
  const handleSidebarEnter = () => setIsSidebarOpen(true);
  const handleSidebarLeave = () => setIsSidebarOpen(false);

  return (
    <div className="min-h-screen flex flex-col relative selection:bg-white selection:text-black">
      
      {/* Sidebar Trigger Zone (Left Edge) - Desktop only hover trigger */}
      <div 
        className="fixed inset-y-0 left-0 w-6 z-[60] cursor-pointer hover:bg-white/5 transition-colors hidden lg:block"
        onMouseEnter={handleSidebarEnter}
      />

      {/* Sidebar Overlay (Mobile Only) */}
      <div 
        className={`fixed inset-0 z-[55] bg-black/60 transition-opacity duration-500 lg:hidden ${isSidebarOpen ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'}`}
        onClick={() => setIsSidebarOpen(false)}
      />

      {/* Sidebar Component - Moved to root level to ensure proper z-index stacking above overlay */}
      <Sidebar 
        type={type} 
        isOpen={isSidebarOpen} 
        onMouseLeave={handleSidebarLeave}
      />

      {/* Background Elements */}
      <div className="fixed inset-0 pointer-events-none z-0 bg-black">
        <div className="absolute inset-0 bg-grid-holographic opacity-60 bg-[length:60px_60px]"></div>
        <div className="absolute top-[20%] left-[50%] -translate-x-1/2 w-[600px] h-[600px] bg-white/5 rounded-full blur-[150px] animate-pulse-slow"></div>
        <div className="absolute top-0 left-1/4 w-[1px] h-screen bg-gradient-to-b from-transparent via-white/5 to-transparent"></div>
        <div className="absolute top-0 right-1/4 w-[1px] h-screen bg-gradient-to-b from-transparent via-white/5 to-transparent"></div>
      </div>

      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-40 bg-black/80 backdrop-blur-md border-b border-white/10 h-16">
        <div className="max-w-[1600px] mx-auto h-full px-6 flex items-center justify-between relative">
          <div className="flex items-center gap-8 pl-4 lg:pl-6">
            <Link to="/" className="flex items-center gap-3 group">
              <div className="size-8 relative flex items-center justify-center border border-white/20 rounded-sm bg-black/50 group-hover:border-white/60 group-hover:shadow-[0_0_15px_rgba(255,255,255,0.3)] transition-all duration-300">
                <span className="material-symbols-outlined relative z-10 text-white text-[20px]">deployed_code</span>
              </div>
              <span className="text-xl font-bold tracking-[0.2em] uppercase text-white text-shadow-glow">Qyro</span>
            </Link>
            
            <div className="hidden md:flex items-center relative group/search">
              <div className="absolute inset-y-0 left-3 flex items-center pointer-events-none">
                <span className="material-symbols-outlined text-gray-500 group-focus-within/search:text-white transition-colors" style={{fontSize: '18px'}}>search</span>
              </div>
              <input 
                type="text" 
                className="bg-black/50 border border-white/10 text-xs text-gray-300 rounded-sm pl-10 pr-4 py-1.5 w-64 focus:ring-0 focus:border-white/40 focus:outline-none transition-all placeholder-gray-600 focus:shadow-[0_0_10px_rgba(255,255,255,0.1)] font-mono uppercase tracking-wide"
                placeholder={type === 'api' ? "SEARCH API..." : "SEARCH DOCS..."}
              />
              <div className="absolute inset-y-0 right-3 flex items-center pointer-events-none">
                <span className="text-[10px] text-gray-600 border border-gray-800 rounded-sm px-1 py-0.5 font-mono">/</span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-8">
            <nav className="hidden lg:flex items-center gap-8">
              <Link 
                to="/docs/introduction" 
                className={`text-xs font-bold uppercase tracking-widest transition-all ${isActive('/docs') || location.pathname === '/' ? 'text-white drop-shadow-[0_0_5px_rgba(255,255,255,0.5)]' : 'text-gray-400 hover:text-white'}`}
              >
                Docs
              </Link>
              <Link 
                to="/api" 
                className={`text-xs font-bold uppercase tracking-widest transition-all ${isActive('/api') ? 'text-white drop-shadow-[0_0_5px_rgba(255,255,255,0.5)]' : 'text-gray-400 hover:text-white'}`}
              >
                API
              </Link>
              <a href="#" className="text-xs font-bold uppercase tracking-widest text-gray-400 hover:text-white transition-all">
                Blog
              </a>
            </nav>
            <div className="h-4 w-[1px] bg-white/20 hidden lg:block"></div>
            <div className="flex items-center gap-4">
              <a href="https://github.com" target="_blank" rel="noreferrer" className="text-gray-400 hover:text-white transition-colors">
                <span className="material-symbols-outlined" style={{fontSize: '20px'}}>code</span>
              </a>
              <button className="bg-white text-black hover:bg-gray-200 text-xs font-bold uppercase tracking-wider px-5 py-2 rounded-sm transition-all shadow-[0_0_15px_rgba(255,255,255,0.2)] hover:shadow-[0_0_25px_rgba(255,255,255,0.5)]">
                Sign In
              </button>
              {/* Mobile Menu Button - Manually open sidebar */}
              <button 
                className="lg:hidden text-white"
                onClick={(e) => {
                  e.stopPropagation(); // Prevent immediate closing due to any bubble up
                  setIsSidebarOpen(!isSidebarOpen);
                }}
              >
                <span className="material-symbols-outlined">menu</span>
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="flex flex-1 pt-16 max-w-[1600px] mx-auto w-full relative z-10">
        {/* Main Content */}
        <main className="flex-1 relative min-h-[calc(100vh-64px)] overflow-x-hidden w-full px-6">
            {children}
        </main>
      </div>
    </div>
  );
};