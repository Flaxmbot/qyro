import React, { useState } from 'react';
import { NavLink, Outlet, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Menu, X, Github, Command, ChevronRight } from 'lucide-react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: (string | undefined | null | false)[]) {
  return twMerge(clsx(inputs));
}

export function Layout() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const location = useLocation();

  const toggleSidebar = () => setIsSidebarOpen(!isSidebarOpen);
  const closeSidebar = () => setIsSidebarOpen(false);

  return (
    <div className="flex h-screen overflow-hidden bg-background text-text font-sans">
      {/* Mobile Sidebar Overlay */}
      <AnimatePresence>
        {isSidebarOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={closeSidebar}
            className="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm lg:hidden"
          />
        )}
      </AnimatePresence>

      {/* Sidebar */}
      <motion.aside
        className={cn(
          "fixed inset-y-0 left-0 z-50 w-72 transform border-r border-border bg-surface px-6 py-6 transition-transform duration-300 lg:static lg:translate-x-0",
          isSidebarOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-3">
            <img src="/assets/qyro_logo.svg" alt="Qyro" className="h-8 w-auto" />
          </div>
          <button onClick={closeSidebar} className="lg:hidden p-2 hover:bg-surfaceHighlight rounded-md text-textMuted hover:text-text">
            <X size={20} />
          </button>
        </div>

        <nav className="space-y-6">
          <div className="space-y-1">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-textMuted mb-2 px-2">Getting Started</h3>
            <NavItem to="/" icon={<Command size={16} />} onClick={closeSidebar}>Introduction</NavItem>
            <NavItem to="/quick-start" icon={<ChevronRight size={16} />} onClick={closeSidebar}>Quick Start</NavItem>
          </div>

          <div className="space-y-1">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-textMuted mb-2 px-2">Concepts</h3>
            <NavItem to="/architecture" icon={<ChevronRight size={16} />} onClick={closeSidebar}>Architecture</NavItem>
            <NavItem to="/polyglot" icon={<ChevronRight size={16} />} onClick={closeSidebar}>Polyglot Runtime</NavItem>
          </div>

          <div className="space-y-1">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-textMuted mb-2 px-2">Reference</h3>
            <NavItem to="/configuration" icon={<ChevronRight size={16} />} onClick={closeSidebar}>Configuration</NavItem>
            <NavItem to="/api" icon={<ChevronRight size={16} />} onClick={closeSidebar}>API Reference</NavItem>
          </div>
        </nav>

        <div className="absolute bottom-6 left-6 right-6">
          <a
            href="https://github.com/Flaxmbot/qyro"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 w-full justify-center rounded-lg border border-border bg-surfaceHighlight px-4 py-2 text-sm font-medium transition-colors hover:bg-border hover:text-white"
          >
            <Github size={16} />
            GitHub
          </a>
        </div>
      </motion.aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col h-full overflow-hidden relative">
        {/* Header (Mobile) */}
        <header className="flex items-center justify-between border-b border-border bg-surface/50 px-6 py-4 backdrop-blur-md lg:hidden">
          <div className="flex items-center gap-2">
            <img src="/assets/qyro_logo.svg" alt="Qyro" className="h-6 w-auto" />
          </div>
          <button onClick={toggleSidebar} className="p-2 hover:bg-surfaceHighlight rounded-md text-text">
            <Menu size={20} />
          </button>
        </header>

        {/* Scrollable Content Area */}
        <main className="flex-1 overflow-y-auto scroll-smooth">
          <div className="container mx-auto max-w-5xl px-6 py-12 lg:px-12 lg:py-16">
            <AnimatePresence mode="wait">
              <motion.div
                key={location.pathname}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.3 }}
              >
                <Outlet />
              </motion.div>
            </AnimatePresence>
          </div>
        </main>
      </div>
    </div>
  );
}

function NavItem({ to, children, icon, onClick }: { to: string; children: React.ReactNode; icon: React.ReactNode; onClick?: () => void }) {
  return (
    <NavLink
      to={to}
      onClick={onClick}
      className={({ isActive }) =>
        cn(
          "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-all duration-200",
          isActive
            ? "bg-primary/10 text-primary"
            : "text-textMuted hover:bg-surfaceHighlight hover:text-text"
        )
      }
    >
      {icon}
      {children}
    </NavLink>
  );
}
