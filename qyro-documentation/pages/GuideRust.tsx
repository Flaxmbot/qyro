import React from 'react';
import { HoloPanel } from '../components/HoloPanel';
import { Link } from 'react-router-dom';

export const GuideRust: React.FC = () => {
    return (
        <div className="flex flex-col xl:flex-row gap-12 px-6 py-12 lg:px-12 lg:py-16">
            <div className="flex-1 max-w-4xl min-h-[100vh]">

                {/* Breadcrumb */}
                <div className="flex items-center gap-2 text-[10px] uppercase tracking-widest text-gray-500 mb-8 font-mono">
                    <Link to="/" className="hover:text-white transition-colors">Docs</Link>
                    <span className="text-white/20">/</span>
                    <span>Guides</span>
                    <span className="text-white/20">/</span>
                    <span className="text-white">Rust</span>
                </div>

                {/* Title */}
                <h1 className="text-4xl md:text-5xl font-light tracking-tight text-white mb-6 relative">
                    Rust Guide
                    <span className="absolute -left-8 top-2 w-1 h-8 bg-orange-500 shadow-[0_0_10px_rgba(249,115,22,0.5)] hidden lg:block"></span>
                </h1>

                <p className="text-lg text-gray-400 leading-relaxed font-light mb-10 max-w-3xl">
                    Build safe, high-performance services with Rust. Qyro generates type-safe bindings for your RPC calls and handles the async runtime setup.
                </p>

                {/* Service Definition */}
                <div className="mb-16">
                    <h2 className="text-2xl font-light text-white mb-6">Defining a Service</h2>
                    <p className="text-sm text-gray-400 mb-4">
                        Use the <code className="text-holo-blue">rust</code> preset.
                    </p>
                    <HoloPanel>
                        <pre className="font-mono text-xs leading-loose">
                            <span className="text-blue-400 font-bold">&gt;&gt;&gt;rust:service [default]</span>{'\n'}
                            <span className="text-gray-500">// main.rs content</span>{'\n'}
                            <span className="text-purple-400">use</span> qyro_adapters::prelude::*;{'\n'}
                            {'\n'}
                            <span className="text-yellow-300">#[tokio::main]</span>{'\n'}
                            <span className="text-purple-400">async fn</span> <span className="text-blue-300">main</span>() -&gt; Result&lt;(), Box&lt;dyn std::error::Error&gt;&gt; {'{'}{'\n'}
                            {'    '}println!(<span className="text-green-300">"Rust service ready"</span>);{'\n'}
                            {'    '}<span className="text-purple-400">Ok</span>((){'\n'}
                            {'}'}
                        </pre>
                    </HoloPanel>
                </div>

                {/* RPC */}
                <div className="mb-16">
                    <h2 className="text-2xl font-light text-white mb-6">Type-Safe RPC</h2>
                    <p className="text-sm text-gray-400 mb-4">
                        Use the <code className="text-holo-blue">call!</code> macro for RPC.
                    </p>
                    <HoloPanel>
                        <pre className="font-mono text-xs leading-loose">
                            <span className="text-gray-500">// Define response struct</span>{'\n'}
                            <span className="text-yellow-300">#[derive(Deserialize)]</span>{'\n'}
                            <span className="text-purple-400">struct</span> <span className="text-blue-300">User</span> {'{'}{'\n'}
                            {'    '}id: <span className="text-purple-400">i32</span>,{'\n'}
                            {'    '}name: <span className="text-purple-400">String</span>,{'\n'}
                            {'}'}{'\n'}
                            {'\n'}
                            <span className="text-gray-500">// Call remote service</span>{'\n'}
                            <span className="text-purple-400">let</span> user: User = <span className="text-blue-300">call!</span>(<span className="text-green-300">"auth.get_user"</span>, <span className="text-orange-300">123</span>).<span className="text-purple-400">await</span>?;
                        </pre>
                    </HoloPanel>
                </div>

                {/* Footer Navigation */}
                <div className="border-t border-white/10 pt-10 flex justify-between">
                    <Link to="/docs/guides/node" className="group flex items-center gap-3 text-gray-500 hover:text-white transition-colors">
                        <span className="material-symbols-outlined border border-white/10 p-2 rounded-sm group-hover:border-white/40 transition-colors">arrow_back</span>
                        <div className="flex flex-col items-start">
                            <span className="text-[10px] uppercase tracking-widest text-gray-600">Previous</span>
                            <span className="text-sm font-bold">Node.js Guide</span>
                        </div>
                    </Link>
                    <Link to="/docs/guides/go" className="group flex items-center gap-3 text-gray-500 hover:text-white transition-colors text-right">
                        <div className="flex flex-col items-end">
                            <span className="text-[10px] uppercase tracking-widest text-gray-600">Next</span>
                            <span className="text-sm font-bold">Go Guide</span>
                        </div>
                        <span className="material-symbols-outlined border border-white/10 p-2 rounded-sm group-hover:border-white/40 transition-colors">arrow_forward</span>
                    </Link>
                </div>
            </div>
        </div>
    );
};
