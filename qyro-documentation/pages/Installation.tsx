import React from 'react';
import { HoloPanel } from '../components/HoloPanel';
import { Link } from 'react-router-dom';

export const Installation: React.FC = () => {
    return (
        <div className="flex flex-col xl:flex-row gap-12 px-6 py-12 lg:px-12 lg:py-16">
            <div className="flex-1 max-w-4xl min-h-[100vh]">

                {/* Breadcrumb */}
                <div className="flex items-center gap-2 text-[10px] uppercase tracking-widest text-gray-500 mb-8 font-mono">
                    <Link to="/" className="hover:text-white transition-colors">Docs</Link>
                    <span className="text-white/20">/</span>
                    <span>Start</span>
                    <span className="text-white/20">/</span>
                    <span className="text-white">Installation</span>
                </div>

                {/* Title */}
                <h1 className="text-4xl md:text-5xl font-light tracking-tight text-white mb-6 relative">
                    Installation
                    <span className="absolute -left-8 top-2 w-1 h-8 bg-white shadow-[0_0_10px_white] hidden lg:block"></span>
                </h1>

                <p className="text-lg text-gray-400 leading-relaxed font-light mb-10 max-w-3xl">
                    Get Qyro up and running in seconds. The runtime is distributed as a Python package and requires Docker for container orchestration.
                </p>

                {/* Prerequisites */}
                <h2 className="text-2xl font-light text-white mb-6 flex items-center gap-3">
                    <span className="material-symbols-outlined text-white/50">checklist</span>
                    Prerequisites
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-12">
                    <div className="p-4 border border-white/10 bg-white/[0.02] rounded-sm">
                        <div className="flex items-center gap-3 mb-2">
                            <span className="material-symbols-outlined text-holo-blue">terminal</span>
                            <h3 className="font-bold text-white text-sm">Python 3.9+</h3>
                        </div>
                        <p className="text-xs text-gray-500">Required for the CLI and Orchestrator.</p>
                    </div>
                    <div className="p-4 border border-white/10 bg-white/[0.02] rounded-sm">
                        <div className="flex items-center gap-3 mb-2">
                            <span className="material-symbols-outlined text-blue-400">layers</span>
                            <h3 className="font-bold text-white text-sm">Docker Engine</h3>
                        </div>
                        <p className="text-xs text-gray-500">Required for building and running services.</p>
                    </div>
                </div>

                {/* Install Command */}
                <h2 className="text-2xl font-light text-white mb-6 flex items-center gap-3">
                    <span className="material-symbols-outlined text-white/50">download</span>
                    Install via PIP
                </h2>

                <HoloPanel noPadding className="mb-12">
                    <div className="bg-black/40 p-6 flex items-center justify-between">
                        <code className="font-mono text-sm text-green-300">pip install qyro</code>
                        <button
                            onClick={() => navigator.clipboard.writeText('pip install qyro')}
                            className="text-gray-500 hover:text-white transition-colors"
                        >
                            <span className="material-symbols-outlined text-[18px]">content_copy</span>
                        </button>
                    </div>
                </HoloPanel>

                {/* Verification */}
                <h2 className="text-2xl font-light text-white mb-6 flex items-center gap-3">
                    <span className="material-symbols-outlined text-white/50">verified</span>
                    Verify Installation
                </h2>
                <p className="text-sm text-gray-500 mb-4 leading-relaxed">
                    Run the version command to ensure Qyro is correctly installed.
                </p>
                <div className="bg-black/40 border-l-2 border-holo-blue p-4 mb-16 font-mono text-xs">
                    <div className="mb-2"><span className="text-gray-500">$</span> qyro --version</div>
                    <div className="text-white">Qyro v1.0.0</div>
                </div>

                {/* Next Steps */}
                <div className="border-t border-white/10 pt-10 flex justify-between">
                    <Link to="/docs/introduction" className="group flex items-center gap-3 text-gray-500 hover:text-white transition-colors">
                        <span className="material-symbols-outlined border border-white/10 p-2 rounded-sm group-hover:border-white/40 transition-colors">arrow_back</span>
                        <div className="flex flex-col items-start">
                            <span className="text-[10px] uppercase tracking-widest text-gray-600">Previous</span>
                            <span className="text-sm font-bold">Introduction</span>
                        </div>
                    </Link>
                    <Link to="/docs/hello-world" className="group flex items-center gap-3 text-gray-500 hover:text-white transition-colors text-right">
                        <div className="flex flex-col items-end">
                            <span className="text-[10px] uppercase tracking-widest text-gray-600">Next</span>
                            <span className="text-sm font-bold">Hello World</span>
                        </div>
                        <span className="material-symbols-outlined border border-white/10 p-2 rounded-sm group-hover:border-white/40 transition-colors">arrow_forward</span>
                    </Link>
                </div>
            </div>

            {/* Right Sidebar */}
            <aside className="hidden xl:block w-64 sticky top-24 h-[calc(100vh-100px)] pt-12 pr-8">
                <div className="relative">
                    <div className="absolute -left-4 top-0 bottom-0 w-[1px] bg-white/5"></div>
                    <h4 className="text-[10px] font-bold text-gray-400 uppercase tracking-[0.2em] mb-6 pl-2">Contents</h4>
                    <nav className="flex flex-col space-y-1">
                        <a href="#" className="text-xs text-white py-1.5 pl-4 block border-l-2 border-white">Installation</a>
                        <a href="#" className="text-xs text-gray-500 py-1.5 pl-4 block border-l-2 border-transparent hover:text-gray-300">Prerequisites</a>
                        <a href="#" className="text-xs text-gray-500 py-1.5 pl-4 block border-l-2 border-transparent hover:text-gray-300">Troubleshooting</a>
                    </nav>
                </div>
            </aside>
        </div>
    );
};
