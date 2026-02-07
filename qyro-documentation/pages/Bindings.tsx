import React from 'react';
import { HoloPanel } from '../components/HoloPanel';
import { Link } from 'react-router-dom';

export const Bindings: React.FC = () => {
    return (
        <div className="flex flex-col xl:flex-row gap-12 px-6 py-12 lg:px-12 lg:py-16">
            <div className="flex-1 max-w-4xl min-h-[100vh]">

                {/* Breadcrumb */}
                <div className="flex items-center gap-2 text-[10px] uppercase tracking-widest text-gray-500 mb-8 font-mono">
                    <Link to="/" className="hover:text-white transition-colors">Docs</Link>
                    <span className="text-white/20">/</span>
                    <span>Core</span>
                    <span className="text-white/20">/</span>
                    <span className="text-white">Bindings</span>
                </div>

                {/* Title */}
                <h1 className="text-4xl md:text-5xl font-light tracking-tight text-white mb-6 relative">
                    Language Bindings
                    <span className="absolute -left-8 top-2 w-1 h-8 bg-white shadow-[0_0_10px_white] hidden lg:block"></span>
                </h1>

                <p className="text-lg text-gray-400 leading-relaxed font-light mb-10 max-w-3xl">
                    Qyro provides a unified interface for cross-language communication. It abstracts the complexity of serialization, network transport, and error handling, allowing you to focus on your business logic.
                </p>

                {/* Architecture */}
                <div className="mb-16">
                    <h2 className="text-2xl font-light text-white mb-6 flex items-center gap-3">
                        <span className="material-symbols-outlined text-white/50">hub</span>
                        Event-Driven Transport
                    </h2>
                    <p className="text-sm text-gray-500 mb-6 leading-relaxed">
                        Under the hood, Qyro uses a high-performance message bus (Kafka) to transport RPC calls and events between services. Data is serialized efficiently using JSON (with planned support for Protobuf/Arrow in v2).
                    </p>
                    <div className="p-4 border border-white/10 bg-white/[0.02] rounded-sm font-mono text-xs text-gray-400">
                        <span className="text-green-400">Python Service</span> (JSON) → <span className="text-holo-blue">Kafka Topic</span> → <span className="text-orange-400">Rust Service</span> (Deserialization)
                    </div>
                </div>

                {/* Type Mapping Table */}
                <div className="mb-16">
                    <h2 className="text-2xl font-light text-white mb-6 flex items-center gap-3">
                        <span className="material-symbols-outlined text-white/50">sync_alt</span>
                        Type Mapping
                    </h2>
                    <p className="text-sm text-gray-500 mb-6">
                        Qyro automatically maps native types to a common JSON-compatible schema during serialization.
                    </p>
                    <div className="border border-white/10 rounded-sm overflow-hidden">
                        <table className="w-full text-left border-collapse">
                            <thead>
                                <tr className="bg-white/5 text-xs text-gray-400 uppercase tracking-widest">
                                    <th className="p-4 border-b border-white/10 font-normal">Qyro Type</th>
                                    <th className="p-4 border-b border-white/10 font-normal">Python</th>
                                    <th className="p-4 border-b border-white/10 font-normal">JavaScript</th>
                                    <th className="p-4 border-b border-white/10 font-normal">Rust</th>
                                    <th className="p-4 border-b border-white/10 font-normal">Go</th>
                                </tr>
                            </thead>
                            <tbody className="text-sm font-mono text-gray-300">
                                <tr className="border-b border-white/5 hover:bg-white/[0.02]">
                                    <td className="p-4 text-holo-blue">String</td>
                                    <td className="p-4">str</td>
                                    <td className="p-4">String</td>
                                    <td className="p-4">String / &str</td>
                                    <td className="p-4">string</td>
                                </tr>
                                <tr className="border-b border-white/5 hover:bg-white/[0.02]">
                                    <td className="p-4 text-holo-blue">Integer</td>
                                    <td className="p-4">int</td>
                                    <td className="p-4">Number / BigInt</td>
                                    <td className="p-4">i64</td>
                                    <td className="p-4">int64</td>
                                </tr>
                                <tr className="border-b border-white/5 hover:bg-white/[0.02]">
                                    <td className="p-4 text-holo-blue">Float</td>
                                    <td className="p-4">float</td>
                                    <td className="p-4">Number</td>
                                    <td className="p-4">f64</td>
                                    <td className="p-4">float64</td>
                                </tr>
                                <tr className="border-b border-white/5 hover:bg-white/[0.02]">
                                    <td className="p-4 text-holo-blue">Map/Dict</td>
                                    <td className="p-4">dict</td>
                                    <td className="p-4">Object</td>
                                    <td className="p-4">HashMap</td>
                                    <td className="p-4">map[string]any</td>
                                </tr>
                                <tr className="border-b border-white/5 hover:bg-white/[0.02]">
                                    <td className="p-4 text-holo-blue">Buffer</td>
                                    <td className="p-4">bytes</td>
                                    <td className="p-4">Uint8Array</td>
                                    <td className="p-4">Vec&lt;u8&gt;</td>
                                    <td className="p-4">[]byte</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>

                {/* Footer Navigation */}
                <div className="border-t border-white/10 pt-10 flex justify-between">
                    <Link to="/docs/architecture" className="group flex items-center gap-3 text-gray-500 hover:text-white transition-colors">
                        <span className="material-symbols-outlined border border-white/10 p-2 rounded-sm group-hover:border-white/40 transition-colors">arrow_back</span>
                        <div className="flex flex-col items-start">
                            <span className="text-[10px] uppercase tracking-widest text-gray-600">Previous</span>
                            <span className="text-sm font-bold">Architecture</span>
                        </div>
                    </Link>
                    <Link to="/docs/sandboxing" className="group flex items-center gap-3 text-gray-500 hover:text-white transition-colors text-right">
                        <div className="flex flex-col items-end">
                            <span className="text-[10px] uppercase tracking-widest text-gray-600">Next</span>
                            <span className="text-sm font-bold">Sandboxing</span>
                        </div>
                        <span className="material-symbols-outlined border border-white/10 p-2 rounded-sm group-hover:border-white/40 transition-colors">arrow_forward</span>
                    </Link>
                </div>
            </div>
        </div>
    );
};
