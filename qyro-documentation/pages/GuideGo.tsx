import React from 'react';
import { HoloPanel } from '../components/HoloPanel';
import { Link } from 'react-router-dom';

export const GuideGo: React.FC = () => {
    return (
        <div className="flex flex-col xl:flex-row gap-12 px-6 py-12 lg:px-12 lg:py-16">
            <div className="flex-1 max-w-4xl min-h-[100vh]">

                {/* Breadcrumb */}
                <div className="flex items-center gap-2 text-[10px] uppercase tracking-widest text-gray-500 mb-8 font-mono">
                    <Link to="/" className="hover:text-white transition-colors">Docs</Link>
                    <span className="text-white/20">/</span>
                    <span>Guides</span>
                    <span className="text-white/20">/</span>
                    <span className="text-white">Go</span>
                </div>

                {/* Title */}
                <h1 className="text-4xl md:text-5xl font-light tracking-tight text-white mb-6 relative">
                    Go Guide
                    <span className="absolute -left-8 top-2 w-1 h-8 bg-cyan-500 shadow-[0_0_10px_rgba(6,182,212,0.5)] hidden lg:block"></span>
                </h1>

                <p className="text-lg text-gray-400 leading-relaxed font-light mb-10 max-w-3xl">
                    Leverage Go's concurrency for microservices and networking tasks. Qyro handles the boilerplate so you can focus on your `main` function.
                </p>

                {/* Service Definition */}
                <div className="mb-16">
                    <h2 className="text-2xl font-light text-white mb-6">Defining a Service</h2>
                    <p className="text-sm text-gray-400 mb-4">
                        Use the <code className="text-holo-blue">go</code> preset.
                    </p>
                    <HoloPanel>
                        <pre className="font-mono text-xs leading-loose">
                            <span className="text-blue-400 font-bold">&gt;&gt;&gt;go:service [default]</span>{'\n'}
                            <span className="text-purple-400">package</span> main{'\n'}
                            {'\n'}
                            <span className="text-purple-400">import</span> (<span className="text-green-300">"fmt"</span>){'\n'}
                            {'\n'}
                            <span className="text-purple-400">func</span> <span className="text-blue-300">main</span>() {'{'}{'\n'}
                            {'    '}fmt.Println(<span className="text-green-300">"Go service started"</span>){'\n'}
                            {'}'}
                        </pre>
                    </HoloPanel>
                </div>

                {/* RPC */}
                <div className="mb-16">
                    <h2 className="text-2xl font-light text-white mb-6">Calling Services</h2>
                    <p className="text-sm text-gray-400 mb-4">
                        Use <code className="text-holo-blue">qyro.Call</code>.
                    </p>
                    <HoloPanel>
                        <pre className="font-mono text-xs leading-loose">
                            <span className="text-purple-400">import</span> "github.com/qyro/adapters"{'\n'}
                            {'\n'}
                            <span className="text-gray-500">// Inside a function</span>{'\n'}
                            result, err := qyro.Call(<span className="text-green-300">"math.add"</span>, <span className="text-orange-300">10</span>, <span className="text-orange-300">20</span>){'\n'}
                            <span className="text-purple-400">if</span> err != nil {'{'}{'\n'}
                            {'    '}log.Fatal(err){'\n'}
                            {'}'}
                        </pre>
                    </HoloPanel>
                </div>

                {/* Footer Navigation */}
                <div className="border-t border-white/10 pt-10 flex justify-between">
                    <Link to="/docs/guides/rust" className="group flex items-center gap-3 text-gray-500 hover:text-white transition-colors">
                        <span className="material-symbols-outlined border border-white/10 p-2 rounded-sm group-hover:border-white/40 transition-colors">arrow_back</span>
                        <div className="flex flex-col items-start">
                            <span className="text-[10px] uppercase tracking-widest text-gray-600">Previous</span>
                            <span className="text-sm font-bold">Rust Guide</span>
                        </div>
                    </Link>
                    <Link to="/api" className="group flex items-center gap-3 text-gray-500 hover:text-white transition-colors text-right">
                        <div className="flex flex-col items-end">
                            <span className="text-[10px] uppercase tracking-widest text-gray-600">Next</span>
                            <span className="text-sm font-bold">SDK Reference</span>
                        </div>
                        <span className="material-symbols-outlined border border-white/10 p-2 rounded-sm group-hover:border-white/40 transition-colors">arrow_forward</span>
                    </Link>
                </div>
            </div>
        </div>
    );
};
