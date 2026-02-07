import React from 'react';
import { HoloPanel } from '../components/HoloPanel';
import { Link } from 'react-router-dom';

export const Changelog: React.FC = () => {
    return (
        <div className="flex flex-col xl:flex-row gap-12 px-6 py-12 lg:px-12 lg:py-16">
            <div className="flex-1 max-w-4xl min-h-[100vh]">
                <div className="flex items-center gap-2 text-[10px] uppercase tracking-widest text-gray-500 mb-8 font-mono">
                    <Link to="/" className="hover:text-white transition-colors">Docs</Link>
                    <span className="text-white/20">/</span>
                    <span className="text-white">Changelog</span>
                </div>

                <h1 className="text-4xl md:text-5xl font-light tracking-tight text-white mb-12 relative">
                    Changelog
                    <span className="absolute -left-8 top-2 w-1 h-8 bg-purple-500 shadow-[0_0_10px_rgba(168,85,247,0.5)] hidden lg:block"></span>
                </h1>

                <div className="relative border-l border-white/10 ml-4 pl-8 space-y-16">

                    {/* v1.0.0 */}
                    <div className="relative">
                        <div className="absolute -left-[37px] top-2 w-4 h-4 rounded-full bg-purple-500 border-4 border-black shadow-[0_0_10px_rgba(168,85,247,0.8)]"></div>
                        <h2 className="text-2xl font-light text-white mb-2 flex items-baseline gap-4">
                            v1.0.0
                            <span className="text-xs font-mono text-gray-500 bg-white/5 px-2 py-1 rounded">Latest</span>
                        </h2>
                        <p className="text-sm text-gray-500 mb-6 font-mono">October 15, 2025</p>

                        <div className="space-y-4">
                            <div className="flex gap-4 items-start">
                                <span className="px-2 py-1 bg-green-500/10 text-green-400 text-[10px] font-bold uppercase tracking-wider rounded border border-green-500/20 mt-1">Feat</span>
                                <p className="text-gray-300 text-sm">Initial release of Qyro Universal Runtime.</p>
                            </div>
                            <div className="flex gap-4 items-start">
                                <span className="px-2 py-1 bg-green-500/10 text-green-400 text-[10px] font-bold uppercase tracking-wider rounded border border-green-500/20 mt-1">Feat</span>
                                <p className="text-gray-300 text-sm">Support for Python, Node.js, Go, Rust, Java, and C++.</p>
                            </div>
                            <div className="flex gap-4 items-start">
                                <span className="px-2 py-1 bg-green-500/10 text-green-400 text-[10px] font-bold uppercase tracking-wider rounded border border-green-500/20 mt-1">Feat</span>
                                <p className="text-gray-300 text-sm">Zero-Configuration Docker orchestration.</p>
                            </div>
                        </div>
                    </div>

                    {/* v0.9.0 (Beta) */}
                    <div className="relative opacity-60 hover:opacity-100 transition-opacity">
                        <div className="absolute -left-[37px] top-2 w-4 h-4 rounded-full bg-gray-700 border-4 border-black"></div>
                        <h2 className="text-xl font-light text-white mb-2">v0.9.0 (Beta)</h2>
                        <p className="text-sm text-gray-500 mb-6 font-mono">August 2025</p>
                        <div className="space-y-4">
                            <div className="flex gap-4 items-start">
                                <span className="px-2 py-1 bg-blue-500/10 text-blue-400 text-[10px] font-bold uppercase tracking-wider rounded border border-blue-500/20 mt-1">Fix</span>
                                <p className="text-gray-300 text-sm">Improved hot-reload reliability on Windows.</p>
                            </div>
                        </div>
                    </div>

                </div>
            </div>
        </div>
    );
};
