import React from 'react';
import { Link } from 'react-router-dom';

export const Roadmap: React.FC = () => {
    return (
        <div className="flex flex-col xl:flex-row gap-12 px-6 py-12 lg:px-12 lg:py-16">
            <div className="flex-1 max-w-4xl min-h-[100vh]">
                <div className="flex items-center gap-2 text-[10px] uppercase tracking-widest text-gray-500 mb-8 font-mono">
                    <Link to="/" className="hover:text-white transition-colors">Docs</Link>
                    <span className="text-white/20">/</span>
                    <span className="text-white">Roadmap</span>
                </div>

                <h1 className="text-4xl md:text-5xl font-light tracking-tight text-white mb-12 relative">
                    Roadmap
                    <span className="absolute -left-8 top-2 w-1 h-8 bg-blue-500 shadow-[0_0_10px_rgba(59,130,246,0.5)] hidden lg:block"></span>
                </h1>

                <div className="grid gap-8">
                    {/* Q4 2025 */}
                    <div className="border border-white/10 bg-white/[0.02] p-8 rounded-sm relative overflow-hidden group">
                        <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                            <span className="text-6xl font-black text-white/20">Q4</span>
                        </div>
                        <h2 className="text-2xl font-light text-white mb-6">Q4 2025: Cloud & Scale</h2>
                        <ul className="space-y-4">
                            <li className="flex items-center gap-3 text-gray-400 group-hover:text-white transition-colors">
                                <span className="material-symbols-outlined text-green-400">check_circle</span>
                                <div>
                                    <strong className="block text-white text-sm">Kubernetes Operator</strong>
                                    <span className="text-xs">Native K8s CRDs for defining Qyro services.</span>
                                </div>
                            </li>
                            <li className="flex items-center gap-3 text-gray-400 group-hover:text-white transition-colors">
                                <span className="material-symbols-outlined text-gray-600">radio_button_unchecked</span>
                                <div>
                                    <strong className="block text-white text-sm">Managed Cloud</strong>
                                    <span className="text-xs">One-click deploy to Qyro Cloud (beta).</span>
                                </div>
                            </li>
                        </ul>
                    </div>

                    {/* 2026 */}
                    <div className="border border-white/10 bg-white/[0.02] p-8 rounded-sm relative overflow-hidden group opacity-80 hover:opacity-100 transition-opacity">
                        <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                            <span className="text-6xl font-black text-white/20">26</span>
                        </div>
                        <h2 className="text-2xl font-light text-white mb-6">2026: The AI Era</h2>
                        <ul className="space-y-4">
                            <li className="flex items-center gap-3 text-gray-400 group-hover:text-white transition-colors">
                                <span className="material-symbols-outlined text-gray-600">radio_button_unchecked</span>
                                <div>
                                    <strong className="block text-white text-sm">AI Agent Protocols</strong>
                                    <span className="text-xs">Standardized headers for agent-to-agent negotiation.</span>
                                </div>
                            </li>
                            <li className="flex items-center gap-3 text-gray-400 group-hover:text-white transition-colors">
                                <span className="material-symbols-outlined text-gray-600">radio_button_unchecked</span>
                                <div>
                                    <strong className="block text-white text-sm">WASM Runtime</strong>
                                    <span className="text-xs">Run untrusted code safely in WebAssembly sandboxes.</span>
                                </div>
                            </li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    );
};
