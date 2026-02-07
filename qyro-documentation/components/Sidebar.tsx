import React from 'react';
import { NavLink } from 'react-router-dom';

interface SidebarProps {
  type: 'docs' | 'api';
  isOpen: boolean;
  onMouseLeave?: () => void;
}

interface NavItem {
  label: string;
  path: string;
}

interface NavSection {
  title: string;
  items: NavItem[];
}

const docsNav: NavSection[] = [
  {
    title: 'Start',
    items: [
      { label: 'Introduction', path: '/docs/introduction' },
      { label: 'Installation', path: '/docs/installation' },
      { label: 'Hello World', path: '/docs/hello-world' },
    ],
  },
  {
    title: 'Core',
    items: [
      { label: 'Architecture', path: '/docs/architecture' },
      { label: 'Bindings', path: '/docs/bindings' },
      { label: 'Sandboxing', path: '/docs/sandboxing' },
    ],
  },
  {
    title: 'Guides',
    items: [
      { label: 'Python', path: '/docs/guides/python' },
      { label: 'Rust', path: '/docs/guides/rust' },
      { label: 'Java', path: '/docs/guides/java' },
      { label: 'Node.js', path: '/docs/guides/node' },
    ],
  },
];

const apiNav: NavSection[] = [
  {
    title: 'General',
    items: [
      { label: 'Overview', path: '/api' },
      { label: 'Authentication', path: '/api/auth' },
      { label: 'Rate Limits', path: '/api/limits' },
    ],
  },
  {
    title: 'Runtimes',
    items: [
      { label: 'List Runtimes', path: '/api/runtimes/list' },
      { label: 'Create Runtime', path: '/api/runtimes/create' },
      { label: 'Execute Code', path: '/api/runtimes/execute' },
    ],
  },
  {
    title: 'Storage',
    items: [
      { label: 'KV Store', path: '/api/storage/kv' },
      { label: 'Blob Storage', path: '/api/storage/blob' },
    ],
  },
];

export const Sidebar: React.FC<SidebarProps> = ({ type, isOpen, onMouseLeave }) => {
  const sections = type === 'api' ? apiNav : docsNav;

  return (
    <aside 
      onMouseLeave={onMouseLeave}
      className={`
        fixed inset-y-0 left-0 z-[60] w-72 pt-20 pb-10 
        bg-black/90 backdrop-blur-2xl border-r border-white/10 
        transform transition-transform duration-500 cubic-bezier(0.16, 1, 0.3, 1) shadow-2xl
        ${isOpen ? 'translate-x-0' : '-translate-x-full'}
      `}
    >
      <div className="absolute top-0 right-0 p-4 opacity-50 lg:hidden">
        <span className="material-symbols-outlined text-white/20">dock_to_right</span>
      </div>

      <div className="p-8 space-y-10 h-full overflow-y-auto custom-scrollbar">
        {sections.map((section, idx) => (
          <div key={idx} className="relative group animate-slide-up" style={{ animationDelay: `${idx * 100}ms` }}>
            <div className="absolute -left-8 top-0 bottom-0 w-[1px] bg-gradient-to-b from-transparent via-white/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
            <h3 className="text-[10px] font-bold text-gray-500 uppercase tracking-[0.2em] mb-4 pl-2 border-l border-transparent transition-colors group-hover:text-white">
              {section.title}
            </h3>
            <ul className="space-y-2 border-l border-white/5 ml-2 pl-6">
              {section.items.map((item, itemIdx) => (
                <li key={itemIdx}>
                  <NavLink 
                    to={item.path}
                    end={item.path === '/api' || item.path === '/'}
                    className={({ isActive }) => `
                      block py-1.5 text-xs font-medium hover:translate-x-1 transition-all duration-300 relative group/link
                      ${isActive ? 'text-white' : 'text-gray-500 hover:text-gray-300'}
                    `}
                  >
                    {({ isActive }) => (
                      <>
                        {isActive && (
                          <span className="absolute -left-[29px] top-1/2 -translate-y-1/2 w-1.5 h-1.5 bg-white rounded-full shadow-[0_0_10px_white]"></span>
                        )}
                        <span className={`relative ${isActive ? 'tracking-wide' : ''} transition-all`}>{item.label}</span>
                      </>
                    )}
                  </NavLink>
                </li>
              ))}
            </ul>
          </div>
        ))}
        
        <div className="pt-8 border-t border-white/5 mt-auto">
          <div className="flex items-center justify-between text-[10px] uppercase tracking-wider text-gray-500 font-mono">
            <span>Version</span>
            <span className="text-white">v2.4.0</span>
          </div>
        </div>
      </div>
    </aside>
  );
};