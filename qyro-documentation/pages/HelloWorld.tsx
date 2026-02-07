import React from 'react';
import { HoloPanel } from '../components/HoloPanel';
import { Link } from 'react-router-dom';

export const HelloWorld: React.FC = () => {
    return (
        <div className="flex flex-col xl:flex-row gap-12 px-6 py-12 lg:px-12 lg:py-16">
            <div className="flex-1 max-w-4xl min-h-[100vh]">

                {/* Breadcrumb */}
                <div className="flex items-center gap-2 text-[10px] uppercase tracking-widest text-gray-500 mb-8 font-mono">
                    <Link to="/" className="hover:text-white transition-colors">Docs</Link>
                    <span className="text-white/20">/</span>
                    <span>Start</span>
                    <span className="text-white/20">/</span>
                    <span className="text-white">Hello World</span>
                </div>

                {/* Title */}
                <h1 className="text-4xl md:text-5xl font-light tracking-tight text-white mb-6 relative">
                    Hello World
                    <span className="absolute -left-8 top-2 w-1 h-8 bg-white shadow-[0_0_10px_white] hidden lg:block"></span>
                </h1>

                <p className="text-lg text-gray-400 leading-relaxed font-light mb-10 max-w-3xl">
                    Build your first microservice in under 2 minutes. We'll create a simple Python API that returns a JSON response.
                </p>

                {/* Step 1 */}
                <div className="mb-16">
                    <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-3">
                        <span className="flex items-center justify-center size-8 rounded-full border border-white/20 bg-white/5 text-sm font-mono">1</span>
                        Create the Project
                    </h2>
                    <p className="text-sm text-gray-400 mb-6 ml-11">Initialize a new Qyro project structure.</p>
                    <div className="ml-11">
                        <HoloPanel noPadding>
                            <div className="bg-black/40 p-4 font-mono text-xs">
                                <span className="text-gray-500">$</span> qyro init hello-world<br />
                                <span className="text-gray-500">$</span> cd hello-world
                            </div>
                        </HoloPanel>
                    </div>
                </div>

                {/* Step 2 */}
                <div className="mb-16">
                    <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-3">
                        <span className="flex items-center justify-center size-8 rounded-full border border-white/20 bg-white/5 text-sm font-mono">2</span>
                        Define the Service
                    </h2>
                    <p className="text-sm text-gray-400 mb-6 ml-11">Open <code>main.qyro</code> and paste the following code. This defines a Python service using FastAPI.</p>
                    <div className="ml-11">
                        <HoloPanel>
                            <pre className="font-mono text-xs leading-loose">
                                <span className="text-blue-400 font-bold">&gt;&gt;&gt;python:api [fastapi]</span>{'\n'}
                                <span className="text-purple-400">from</span> fastapi <span className="text-purple-400">import</span> FastAPI{'\n'}
                                <span className="text-purple-400">from</span> qyro_adapters <span className="text-purple-400">import</span> expose{'\n'}
                                {'\n'}
                                <span className="text-white">app</span> = FastAPI(){'\n'}
                                {'\n'}
                                <span className="text-yellow-300">@app.get</span>(<span className="text-green-300">"/"</span>){'\n'}
                                <span className="text-purple-400">def</span> <span className="text-blue-300">root</span>():{'\n'}
                                {'    '}<span className="text-purple-400">return</span> {'{'}<span className="text-green-300">"message"</span>: <span className="text-green-300">"Hello from Qyro!"</span>{'}'}
                            </pre>
                        </HoloPanel>
                    </div>
                </div>

                {/* Step 3 */}
                <div className="mb-16">
                    <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-3">
                        <span className="flex items-center justify-center size-8 rounded-full border border-white/20 bg-white/5 text-sm font-mono">3</span>
                        Run It
                    </h2>
                    <p className="text-sm text-gray-400 mb-6 ml-11">Qyro will compile the file, build the Docker images, and start the cluster.</p>
                    <div className="ml-11">
                        <HoloPanel noPadding>
                            <div className="bg-black/40 p-4 font-mono text-xs">
                                <span className="text-gray-500">$</span> qyro run main.qyro<br />
                                <span className="text-blue-400">... Building python:api ...</span><br />
                                <span className="text-green-400">✔ Stack running at http://localhost:8000</span>
                            </div>
                        </HoloPanel>
                    </div>
                </div>

                {/* Next Steps */}
                <div className="border-t border-white/10 pt-10 flex justify-between">
                    <Link to="/docs/installation" className="group flex items-center gap-3 text-gray-500 hover:text-white transition-colors">
                        <span className="material-symbols-outlined border border-white/10 p-2 rounded-sm group-hover:border-white/40 transition-colors">arrow_back</span>
                        <div className="flex flex-col items-start">
                            <span className="text-[10px] uppercase tracking-widest text-gray-600">Previous</span>
                            <span className="text-sm font-bold">Installation</span>
                        </div>
                    </Link>
                    <Link to="/docs/architecture" className="group flex items-center gap-3 text-gray-500 hover:text-white transition-colors text-right">
                        <div className="flex flex-col items-end">
                            <span className="text-[10px] uppercase tracking-widest text-gray-600">Next</span>
                            <span className="text-sm font-bold">Architecture</span>
                        </div>
                        <span className="material-symbols-outlined border border-white/10 p-2 rounded-sm group-hover:border-white/40 transition-colors">arrow_forward</span>
                    </Link>
                </div>
            </div>
        </div>
    );
};
