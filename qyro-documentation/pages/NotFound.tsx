import React from 'react';
import { Link } from 'react-router-dom';

export const NotFound: React.FC = () => {
    return (
        <div className="flex items-center justify-center min-h-[80vh] flex-col text-center px-4">
            <h1 className="text-9xl font-black text-white/5 select-none absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 pointer-events-none">
                404
            </h1>

            <div className="relative z-10 bg-black/50 backdrop-blur-sm p-12 border border-white/10 rounded-sm shadow-[0_0_50px_rgba(0,0,0,0.5)]">
                <div className="text-6xl mb-6 animate-pulse">👾</div>
                <h2 className="text-3xl font-light text-white mb-4">Page Not Found</h2>
                <p className="text-gray-400 mb-8 max-w-md mx-auto">
                    The requested signal was lost in the void. Valid coordinates are required for transport.
                </p>

                <Link to="/" className="inline-flex items-center gap-3 px-8 py-3 bg-white text-black font-bold uppercase tracking-widest text-xs hover:bg-gray-200 transition-colors">
                    <span className="material-symbols-outlined text-sm">home</span>
                    Return to Base
                </Link>
            </div>
        </div>
    );
};
