import React from 'react';
import { HoloPanel } from '../components/HoloPanel';
import { Link } from 'react-router-dom';

export const CliReference: React.FC = () => {
    return (
        <div className="flex flex-col xl:flex-row gap-12 px-6 py-12 lg:px-12 lg:py-16">
            <div className="flex-1 max-w-4xl min-h-[100vh]">
                <div className="flex items-center gap-2 text-[10px] uppercase tracking-widest text-gray-500 mb-8 font-mono">
                    <Link to="/" className="hover:text-white transition-colors">Docs</Link>
                    <span className="text-white/20">/</span>
                    <span>Reference</span>
                    <span className="text-white/20">/</span>
                    <span className="text-white">CLI</span>
                </div>

                <h1 className="text-4xl md:text-5xl font-light tracking-tight text-white mb-6 relative">
                    CLI Reference
                    <span className="absolute -left-8 top-2 w-1 h-8 bg-purple-500 shadow-[0_0_10px_rgba(168,85,247,0.5)] hidden lg:block"></span>
                </h1>

                <p className="text-lg text-gray-400 leading-relaxed font-light mb-10 max-w-3xl">
                    The `qyro` command-line tool is your main interface for developing, building, and running applications.
                </p>

                <div className="space-y-12">
                    <section>
                        <h2 className="text-2xl font-light text-white mb-6 flex items-center gap-3">
                            <span className="material-symbols-outlined text-purple-400">terminal</span>
                            Primary Commands
                        </h2>

                        <div className="space-y-6">
                            <HoloPanel>
                                <div className="mb-4 flex items-baseline gap-4">
                                    <code className="text-purple-400 font-bold font-mono">qyro init [name]</code>
                                </div>
                                <p className="text-sm text-gray-400 mb-4">Initialize a new Qyro project in the current directory (or a new folder if name is provided).</p>
                                <div className="text-xs text-gray-500 font-mono bg-black/40 p-3 rounded border border-white/5">
                                    $ qyro init my-app --template python-react
                                </div>
                            </HoloPanel>

                            <HoloPanel>
                                <div className="mb-4 flex items-baseline gap-4">
                                    <code className="text-green-400 font-bold font-mono">qyro run [file]</code>
                                </div>
                                <p className="text-sm text-gray-400 mb-4">Compiles and runs the specified `.qyro` file (defaults to main.qyro). Starts the orchestrator and all services.</p>
                                <div className="text-xs text-gray-500 font-mono bg-black/40 p-3 rounded border border-white/5">
                                    $ qyro run main.qyro --watch --port 8080
                                </div>
                            </HoloPanel>

                            <HoloPanel>
                                <div className="mb-4 flex items-baseline gap-4">
                                    <code className="text-blue-400 font-bold font-mono">qyro build</code>
                                </div>
                                <p className="text-sm text-gray-400 mb-4">Builds production artifacts (Docker images) without running them.</p>
                            </HoloPanel>
                        </div>
                    </section>
                </div>
            </div>
        </div>
    );
};
