import React from 'react';
import { HoloPanel } from '../components/HoloPanel';
import { Link } from 'react-router-dom';

export const AdvancedPatterns: React.FC = () => {
    return (
        <div className="flex flex-col xl:flex-row gap-12 px-6 py-12 lg:px-12 lg:py-16">
            <div className="flex-1 max-w-4xl min-h-[100vh]">
                <div className="flex items-center gap-2 text-[10px] uppercase tracking-widest text-gray-500 mb-8 font-mono">
                    <Link to="/" className="hover:text-white transition-colors">Docs</Link>
                    <span className="text-white/20">/</span>
                    <span>Advanced</span>
                    <span className="text-white/20">/</span>
                    <span className="text-white">Patterns</span>
                </div>

                <h1 className="text-4xl md:text-5xl font-light tracking-tight text-white mb-6 relative">
                    Advanced Patterns
                    <span className="absolute -left-8 top-2 w-1 h-8 bg-red-500 shadow-[0_0_10px_rgba(239,68,68,0.5)] hidden lg:block"></span>
                </h1>

                <p className="text-lg text-gray-400 leading-relaxed font-light mb-10 max-w-3xl">
                    Build resilient systems with built-in patterns for failure handling, scaling, and observability.
                </p>

                <div className="space-y-12">
                    <section>
                        <h2 className="text-2xl font-light text-white mb-6">Circuit Breakers</h2>
                        <p className="text-sm text-gray-400 mb-4">
                            Qyro automatically wraps RPC calls in circuit breakers. If a service fails repeatedly (default: 5 failures), the breaker opens to prevent cascading failures.
                        </p>
                        <HoloPanel>
                            <pre className="font-mono text-xs leading-loose text-gray-300">
                                <span className="text-gray-500">// Example trace</span>{'\n'}
                                [Qyro RPC] Circuit breaker OPEN for service 'payment' (failures=5){'\n'}
                                <span className="text-red-400">RuntimeError: Circuit breaker OPEN for service 'payment'</span>
                            </pre>
                        </HoloPanel>
                    </section>

                    <section>
                        <h2 className="text-2xl font-light text-white mb-6">Async/Await & Futures</h2>
                        <p className="text-sm text-gray-400 mb-4">
                            For non-blocking operations, use `call_async`. It returns a Future that you can check later.
                        </p>
                        <HoloPanel>
                            <pre className="font-mono text-xs leading-loose text-gray-300">
                                future = qyro.call_async("video.process", file_id){'\n'}
                                {'\n'}
                                <span className="text-purple-400"># Do other work...</span>{'\n'}
                                {'\n'}
                                result = future.result(timeout=60)
                            </pre>
                        </HoloPanel>
                    </section>
                </div>
            </div>
        </div>
    );
};
