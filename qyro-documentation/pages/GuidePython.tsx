import React from 'react';
import { HoloPanel } from '../components/HoloPanel';
import { Link } from 'react-router-dom';

export const GuidePython: React.FC = () => {
    return (
        <div className="flex flex-col xl:flex-row gap-12 px-6 py-12 lg:px-12 lg:py-16">
            <div className="flex-1 max-w-4xl min-h-[100vh]">

                {/* Breadcrumb */}
                <div className="flex items-center gap-2 text-[10px] uppercase tracking-widest text-gray-500 mb-8 font-mono">
                    <Link to="/" className="hover:text-white transition-colors">Docs</Link>
                    <span className="text-white/20">/</span>
                    <span>Guides</span>
                    <span className="text-white/20">/</span>
                    <span className="text-white">Python</span>
                </div>

                {/* Title */}
                <h1 className="text-4xl md:text-5xl font-light tracking-tight text-white mb-6 relative">
                    Python Guide
                    <span className="absolute -left-8 top-2 w-1 h-8 bg-blue-500 shadow-[0_0_10px_rgba(59,130,246,0.5)] hidden lg:block"></span>
                </h1>

                <p className="text-lg text-gray-400 leading-relaxed font-light mb-10 max-w-3xl">
                    Python is a first-class citizen in Qyro. It's ideal for building backend APIs, data processing workers, and AI agents using libraries like FastAPI, NumPy, and PyTorch.
                </p>

                {/* Service Definition */}
                <div className="mb-16">
                    <h2 className="text-2xl font-light text-white mb-6">Defining a Service</h2>
                    <p className="text-sm text-gray-400 mb-4">
                        Use the <code className="text-holo-blue">production</code> or <code className="text-holo-blue">api</code> presets.
                    </p>
                    <HoloPanel>
                        <pre className="font-mono text-xs leading-loose">
                            <span className="text-blue-400 font-bold">&gt;&gt;&gt;python:backend [production]</span>{'\n'}
                            <span className="text-gray-500"># Standard Python code here</span>{'\n'}
                            <span className="text-purple-400">import</span> os{'\n'}
                            <span className="text-purple-400">print</span>(<span className="text-green-300">f"Service running in </span>{'{'}os.getpid(){'}'}<span className="text-green-300">"</span>)
                        </pre>
                    </HoloPanel>
                </div>

                {/* RPC */}
                <div className="mb-16">
                    <h2 className="text-2xl font-light text-white mb-6">RPC & Exposing Functions</h2>
                    <p className="text-sm text-gray-400 mb-4">
                        Import <code className="text-holo-blue">expose</code> from <code className="text-white">qyro_adapters</code> to make functions callable by other services.
                    </p>
                    <HoloPanel>
                        <pre className="font-mono text-xs leading-loose">
                            <span className="text-purple-400">from</span> qyro_adapters <span className="text-purple-400">import</span> expose{'\n'}
                            {'\n'}
                            <span className="text-yellow-300">@expose</span>{'\n'}
                            <span className="text-purple-400">def</span> <span className="text-blue-300">add</span>(a: <span className="text-green-300">int</span>, b: <span className="text-green-300">int</span>) -&gt; <span className="text-green-300">int</span>:{'\n'}
                            {'    '}<span className="text-purple-400">return</span> a + b
                        </pre>
                    </HoloPanel>
                </div>

                {/* Footer Navigation */}
                <div className="border-t border-white/10 pt-10 flex justify-between">
                    <Link to="/docs/sandboxing" className="group flex items-center gap-3 text-gray-500 hover:text-white transition-colors">
                        <span className="material-symbols-outlined border border-white/10 p-2 rounded-sm group-hover:border-white/40 transition-colors">arrow_back</span>
                        <div className="flex flex-col items-start">
                            <span className="text-[10px] uppercase tracking-widest text-gray-600">Previous</span>
                            <span className="text-sm font-bold">Sandboxing</span>
                        </div>
                    </Link>
                    <Link to="/docs/guides/node" className="group flex items-center gap-3 text-gray-500 hover:text-white transition-colors text-right">
                        <div className="flex flex-col items-end">
                            <span className="text-[10px] uppercase tracking-widest text-gray-600">Next</span>
                            <span className="text-sm font-bold">Node.js Guide</span>
                        </div>
                        <span className="material-symbols-outlined border border-white/10 p-2 rounded-sm group-hover:border-white/40 transition-colors">arrow_forward</span>
                    </Link>
                </div>
            </div>
        </div>
    );
};
