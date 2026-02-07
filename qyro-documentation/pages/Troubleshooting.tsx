import React, { useEffect, useState } from 'react';
import { HoloPanel } from '../components/HoloPanel';
import { Link } from 'react-router-dom';

export const Troubleshooting: React.FC = () => {
    return (
        <div className="flex flex-col xl:flex-row gap-12 px-6 py-12 lg:px-12 lg:py-16">
            <div className="flex-1 max-w-4xl min-h-[100vh]">
                <div className="flex items-center gap-2 text-[10px] uppercase tracking-widest text-gray-500 mb-8 font-mono">
                    <Link to="/" className="hover:text-white transition-colors">Docs</Link>
                    <span className="text-white/20">/</span>
                    <span>Resources</span>
                    <span className="text-white/20">/</span>
                    <span className="text-white">Troubleshooting</span>
                </div>

                <h1 className="text-4xl md:text-5xl font-light tracking-tight text-white mb-6 relative">
                    Troubleshooting
                    <span className="absolute -left-8 top-2 w-1 h-8 bg-orange-500 shadow-[0_0_10px_rgba(249,115,22,0.5)] hidden lg:block"></span>
                </h1>

                <p className="text-lg text-gray-400 leading-relaxed font-light mb-10 max-w-3xl">
                    Common issues and how to resolve them when developing with Qyro.
                </p>

                <div className="space-y-8">
                    <HoloPanel>
                        <h3 className="text-lg font-bold text-white mb-2 flex items-center gap-2">
                            <span className="material-symbols-outlined text-red-400">error</span>
                            Docker Connection Refused
                        </h3>
                        <p className="text-sm text-gray-400 mb-4">
                            If you see `ConnectionError: Docker daemon is not running`, ensure Docker Desktop is started.
                        </p>
                        <pre className="text-xs text-gray-500 font-mono bg-black/40 p-3 rounded border border-white/5">
                            # Verify Docker status{'\n'}
                            $ docker info
                        </pre>
                    </HoloPanel>

                    <HoloPanel>
                        <h3 className="text-lg font-bold text-white mb-2 flex items-center gap-2">
                            <span className="material-symbols-outlined text-yellow-400">warning</span>
                            Port Conflicts (8080/9092)
                        </h3>
                        <p className="text-sm text-gray-400 mb-4">
                            Qyro uses ports 8080 (API), 9092 (Kafka), and 6379 (Redis) by default. If these are in use, specify custom ports in `.qyro` config or stop conflicting services.
                        </p>
                    </HoloPanel>

                    <HoloPanel>
                        <h3 className="text-lg font-bold text-white mb-2 flex items-center gap-2">
                            <span className="material-symbols-outlined text-blue-400">help</span>
                            Hot Reload Not Working
                        </h3>
                        <p className="text-sm text-gray-400 mb-4">
                            Ensure you are running `qyro run --watch`. Make sure your file system supports file watching events (some networked drives do not).
                        </p>
                    </HoloPanel>
                </div>
            </div>
        </div>
    );
};
