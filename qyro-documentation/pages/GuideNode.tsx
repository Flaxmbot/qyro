import React from 'react';
import { HoloPanel } from '../components/HoloPanel';
import { Link } from 'react-router-dom';

export const GuideNode: React.FC = () => {
    return (
        <div className="flex flex-col xl:flex-row gap-12 px-6 py-12 lg:px-12 lg:py-16">
            <div className="flex-1 max-w-4xl min-h-[100vh]">

                {/* Breadcrumb */}
                <div className="flex items-center gap-2 text-[10px] uppercase tracking-widest text-gray-500 mb-8 font-mono">
                    <Link to="/" className="hover:text-white transition-colors">Docs</Link>
                    <span className="text-white/20">/</span>
                    <span>Guides</span>
                    <span className="text-white/20">/</span>
                    <span className="text-white">Node.js</span>
                </div>

                {/* Title */}
                <h1 className="text-4xl md:text-5xl font-light tracking-tight text-white mb-6 relative">
                    Node.js Guide
                    <span className="absolute -left-8 top-2 w-1 h-8 bg-green-500 shadow-[0_0_10px_rgba(34,197,94,0.5)] hidden lg:block"></span>
                </h1>

                <p className="text-lg text-gray-400 leading-relaxed font-light mb-10 max-w-3xl">
                    Use Node.js for high-performance I/O workers, real-time services, or Server-Side Rendering (SSR) in React/Next.js applications.
                </p>

                {/* Service Definition */}
                <div className="mb-16">
                    <h2 className="text-2xl font-light text-white mb-6">Defining a Service</h2>
                    <p className="text-sm text-gray-400 mb-4">
                        Use the <code className="text-holo-blue">node</code> or <code className="text-holo-blue">react</code> presets.
                    </p>
                    <HoloPanel>
                        <pre className="font-mono text-xs leading-loose">
                            <span className="text-blue-400 font-bold">&gt;&gt;&gt;node:worker [default]</span>{'\n'}
                            <span className="text-gray-500">// Your Node.js code here</span>{'\n'}
                            <span className="text-purple-400">console</span>.log(<span className="text-green-300">"Worker started"</span>);
                        </pre>
                    </HoloPanel>
                </div>

                {/* RPC */}
                <div className="mb-16">
                    <h2 className="text-2xl font-light text-white mb-6">Using RPC</h2>
                    <p className="text-sm text-gray-400 mb-4">
                        The adapter is injected automatically. Import types from <code className="text-white">./qyro_adapters/js_adapter</code>.
                    </p>
                    <HoloPanel>
                        <pre className="font-mono text-xs leading-loose">
                            <span className="text-purple-400">import</span> {'{'} call {'}'} <span className="text-purple-400">from</span> <span className="text-green-300">'./qyro_adapters/js_adapter'</span>;{'\n'}
                            {'\n'}
                            <span className="text-purple-400">async function</span> <span className="text-blue-300">fetchUser</span>(id) {'{'}{'\n'}
                            {'  '}<span className="text-gray-500">// Call Python service</span>{'\n'}
                            {'  '}<span className="text-purple-400">const</span> user = <span className="text-purple-400">await</span> call(<span className="text-green-300">"backend.get_user"</span>, id);{'\n'}
                            {'  '}<span className="text-purple-400">return</span> user;{'\n'}
                            {'}'}
                        </pre>
                    </HoloPanel>
                </div>

                {/* Footer Navigation */}
                <div className="border-t border-white/10 pt-10 flex justify-between">
                    <Link to="/docs/guides/python" className="group flex items-center gap-3 text-gray-500 hover:text-white transition-colors">
                        <span className="material-symbols-outlined border border-white/10 p-2 rounded-sm group-hover:border-white/40 transition-colors">arrow_back</span>
                        <div className="flex flex-col items-start">
                            <span className="text-[10px] uppercase tracking-widest text-gray-600">Previous</span>
                            <span className="text-sm font-bold">Python Guide</span>
                        </div>
                    </Link>
                    <Link to="/docs/guides/rust" className="group flex items-center gap-3 text-gray-500 hover:text-white transition-colors text-right">
                        <div className="flex flex-col items-end">
                            <span className="text-[10px] uppercase tracking-widest text-gray-600">Next</span>
                            <span className="text-sm font-bold">Rust Guide</span>
                        </div>
                        <span className="material-symbols-outlined border border-white/10 p-2 rounded-sm group-hover:border-white/40 transition-colors">arrow_forward</span>
                    </Link>
                </div>
            </div>
        </div>
    );
};
