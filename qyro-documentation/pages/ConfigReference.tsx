import React from 'react';
import { HoloPanel } from '../components/HoloPanel';
import { Link } from 'react-router-dom';

export const ConfigReference: React.FC = () => {
    return (
        <div className="flex flex-col xl:flex-row gap-12 px-6 py-12 lg:px-12 lg:py-16">
            <div className="flex-1 max-w-4xl min-h-[100vh]">
                <div className="flex items-center gap-2 text-[10px] uppercase tracking-widest text-gray-500 mb-8 font-mono">
                    <Link to="/" className="hover:text-white transition-colors">Docs</Link>
                    <span className="text-white/20">/</span>
                    <span>Reference</span>
                    <span className="text-white/20">/</span>
                    <span className="text-white">Configuration</span>
                </div>

                <h1 className="text-4xl md:text-5xl font-light tracking-tight text-white mb-6 relative">
                    Configuration
                    <span className="absolute -left-8 top-2 w-1 h-8 bg-blue-500 shadow-[0_0_10px_rgba(59,130,246,0.5)] hidden lg:block"></span>
                </h1>

                <p className="text-lg text-gray-400 leading-relaxed font-light mb-10 max-w-3xl">
                    The `.qyro` file is the heart of your project. It defines your services, dependencies, and infrastructure requirements in a custom DSL.
                </p>

                <div className="space-y-12">
                    <section>
                        <h2 className="text-2xl font-light text-white mb-6">File Structure</h2>
                        <HoloPanel>
                            <pre className="font-mono text-xs leading-loose text-gray-300">
                                <span className="text-gray-500"># Define a service</span>{'\n'}
                                <span className="text-blue-400 font-bold">&gt;&gt;&gt;python:backend [production]</span>{'\n'}
                                {'\n'}
                                <span className="text-gray-500"># Service code follows immediately</span>{'\n'}
                                import os{'\n'}
                                ...{'\n'}
                                {'\n'}
                                <span className="text-gray-500"># Define another service</span>{'\n'}
                                <span className="text-green-400 font-bold">&gt;&gt;&gt;node:frontend</span>{'\n'}
                                ...
                            </pre>
                        </HoloPanel>
                    </section>

                    <section>
                        <h2 className="text-2xl font-light text-white mb-6">Directives</h2>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="p-4 border border-white/10 bg-white/[0.02] rounded-sm">
                                <div className="font-mono text-holo-blue mb-2">Capabilities</div>
                                <p className="text-xs text-gray-400">Request permissions for network or file system access.</p>
                                <pre className="mt-2 text-[10px] text-gray-500"># capabilities: {"{"} "network": ["*"] {"}"}</pre>
                            </div>
                            <div className="p-4 border border-white/10 bg-white/[0.02] rounded-sm">
                                <div className="font-mono text-holo-blue mb-2">Env</div>
                                <p className="text-xs text-gray-400">Set environment variables for the service.</p>
                                <pre className="mt-2 text-[10px] text-gray-500"># env: {"{"} "DEBUG": "true" {"}"}</pre>
                            </div>
                        </div>
                    </section>
                </div>
            </div>
        </div>
    );
};
