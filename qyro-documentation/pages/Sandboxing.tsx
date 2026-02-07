import React from 'react';
import { HoloPanel } from '../components/HoloPanel';
import { Link } from 'react-router-dom';

export const Sandboxing: React.FC = () => {
    return (
        <div className="flex flex-col xl:flex-row gap-12 px-6 py-12 lg:px-12 lg:py-16">
            <div className="flex-1 max-w-4xl min-h-[100vh]">

                {/* Breadcrumb */}
                <div className="flex items-center gap-2 text-[10px] uppercase tracking-widest text-gray-500 mb-8 font-mono">
                    <Link to="/" className="hover:text-white transition-colors">Docs</Link>
                    <span className="text-white/20">/</span>
                    <span>Core</span>
                    <span className="text-white/20">/</span>
                    <span className="text-white">Sandboxing</span>
                </div>

                {/* Title */}
                <h1 className="text-4xl md:text-5xl font-light tracking-tight text-white mb-6 relative">
                    Security & Sandboxing
                    <span className="absolute -left-8 top-2 w-1 h-8 bg-white shadow-[0_0_10px_white] hidden lg:block"></span>
                </h1>

                <p className="text-lg text-gray-400 leading-relaxed font-light mb-10 max-w-3xl">
                    Qyro enforces strict isolation between services. Each component runs in its own containerized environment with explicit permissions for network and file system access.
                </p>

                {/* Default Policy */}
                <div className="mb-12">
                    <h2 className="text-2xl font-light text-white mb-4">Default Deny Policy</h2>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="p-6 border border-red-500/20 bg-red-500/5 rounded-sm">
                            <div className="flex items-center gap-2 mb-2 text-red-400">
                                <span className="material-symbols-outlined">block</span>
                                <h3 className="font-bold text-sm uppercase">Network</h3>
                            </div>
                            <p className="text-xs text-gray-400">Incoming connections blocked. Outbound limited to whitelist.</p>
                        </div>
                        <div className="p-6 border border-red-500/20 bg-red-500/5 rounded-sm">
                            <div className="flex items-center gap-2 mb-2 text-red-400">
                                <span className="material-symbols-outlined">folder_off</span>
                                <h3 className="font-bold text-sm uppercase">File System</h3>
                            </div>
                            <p className="text-xs text-gray-400">Read-only root filesystem. Ephemeral /tmp only.</p>
                        </div>
                        <div className="p-6 border border-red-500/20 bg-red-500/5 rounded-sm">
                            <div className="flex items-center gap-2 mb-2 text-red-400">
                                <span className="material-symbols-outlined">memory</span>
                                <h3 className="font-bold text-sm uppercase">Resources</h3>
                            </div>
                            <p className="text-xs text-gray-400">Hard limits on CPU cycles and Memory usage.</p>
                        </div>
                    </div>
                </div>

                {/* Configuration */}
                <div className="mb-16">
                    <h2 className="text-2xl font-light text-white mb-6">Configuration</h2>
                    <p className="text-sm text-gray-400 mb-6">
                        Permissions are requested in the manifest via capabilities blocks.
                    </p>
                    <HoloPanel>
                        <div className="font-mono text-xs leading-loose">
                            <span className="text-blue-400 font-bold">&gt;&gt;&gt;python:worker</span>{'\n'}
                            <span className="text-gray-500">
                                # Request specific permissions{'\n'}
                                # capabilities: {'{'}{'\n'}
                                #   "network": ["https://api.stripe.com"],{'\n'}
                                #   "fs": ["/data/uploads:rw"]{'\n'}
                                # {'}'}
                            </span>
                            {'\n'}
                            <span className="text-purple-400">def</span> <span className="text-blue-300">process_payment</span>():{'\n'}
                            {'    '}...
                        </div>
                    </HoloPanel>
                </div>

                {/* Footer Navigation */}
                <div className="border-t border-white/10 pt-10 flex justify-between">
                    <Link to="/docs/bindings" className="group flex items-center gap-3 text-gray-500 hover:text-white transition-colors">
                        <span className="material-symbols-outlined border border-white/10 p-2 rounded-sm group-hover:border-white/40 transition-colors">arrow_back</span>
                        <div className="flex flex-col items-start">
                            <span className="text-[10px] uppercase tracking-widest text-gray-600">Previous</span>
                            <span className="text-sm font-bold">Bindings</span>
                        </div>
                    </Link>
                    <Link to="/docs/guides/python" className="group flex items-center gap-3 text-gray-500 hover:text-white transition-colors text-right">
                        <div className="flex flex-col items-end">
                            <span className="text-[10px] uppercase tracking-widest text-gray-600">Next</span>
                            <span className="text-sm font-bold">Python Guide</span>
                        </div>
                        <span className="material-symbols-outlined border border-white/10 p-2 rounded-sm group-hover:border-white/40 transition-colors">arrow_forward</span>
                    </Link>
                </div>
            </div>
        </div>
    );
};
