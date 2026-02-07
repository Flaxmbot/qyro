import React from 'react';

interface HoloPanelProps {
  children: React.ReactNode;
  className?: string;
  noPadding?: boolean;
}

export const HoloPanel: React.FC<HoloPanelProps> = ({ children, className = '', noPadding = false }) => {
  return (
    <div className={`glass-panel-holo holo-panel relative group ${className}`}>
      {/* Animated Corners */}
      <div className="holo-corner holo-corner-tl top-0 left-0 border-t border-l" />
      <div className="holo-corner holo-corner-tr top-0 right-0 border-t border-r" />
      <div className="holo-corner holo-corner-bl bottom-0 left-0 border-b border-l" />
      <div className="holo-corner holo-corner-br bottom-0 right-0 border-b border-r" />
      
      {/* Content */}
      <div className={`${noPadding ? '' : 'p-6'} bg-black/60 backdrop-blur-xl relative z-10 h-full border border-transparent transition-all duration-300`}>
        {children}
      </div>
    </div>
  );
};