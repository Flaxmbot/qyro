import React from 'react';
import { HoloPanel } from '../components/HoloPanel';
import { Link } from 'react-router-dom';

export const Deployment: React.FC = () => {
    return (
        <div className="flex flex-col xl:flex-row gap-12 px-6 py-12 lg:px-12 lg:py-16">
            <div className="flex-1 max-w-4xl min-h-[100vh]">
                <div className="flex items-center gap-2 text-[10px] uppercase tracking-widest text-gray-500 mb-8 font-mono">
                    <Link to="/" className="hover:text-white transition-colors">Docs</Link>
                    <span className="text-white/20">/</span>
                    <span>Resources</span>
                    <span className="text-white/20">/</span>
                    <span className="text-white">Deployment</span>
                </div>

                <h1 className="text-4xl md:text-5xl font-light tracking-tight text-white mb-6 relative">
                    Deployment Guide
                    <span className="absolute -left-8 top-2 w-1 h-8 bg-green-500 shadow-[0_0_10px_rgba(34,197,94,0.5)] hidden lg:block"></span>
                </h1>

                <p className="text-lg text-gray-400 leading-relaxed font-light mb-10 max-w-3xl">
                    Deploy your Qyro applications to any infrastructure that supports Docker.
                </p>

                <div className="space-y-12">
                    <section>
                        <h2 className="text-2xl font-light text-white mb-6">Build for Production</h2>
                        <p className="text-sm text-gray-400 mb-4">
                            Run the build command to generate optimized Docker images for all your services.
                        </p>
                        <HoloPanel>
                            <div className="text-sm font-mono text-gray-300">
                                $ qyro build --prod
                            </div>
                        </HoloPanel>
                    </section>

                    <section>
                        <h2 className="text-2xl font-light text-white mb-6">Docker Compose</h2>
                        <p className="text-sm text-gray-400 mb-4">
                            Qyro generates a `docker-compose.prod.yml` that you can use on any server.
                        </p>
                        <HoloPanel>
                            <pre className="font-mono text-xs leading-loose text-gray-300">
                                <span className="text-purple-400">version:</span> <span className="text-green-300">"3.8"</span>{'\n'}
                                <span className="text-purple-400">services:</span>{'\n'}
                                {'  '}<span className="text-blue-400">backend:</span>{'\n'}
                                {'    '}<span className="text-purple-400">image:</span> <span className="text-green-300">my-app/backend:latest</span>{'\n'}
                                {'    '}<span className="text-purple-400">environment:</span>{'\n'}
                                {'      '}- KAFKA_BOOTSTRAP_SERVERS=kafka:9092
                            </pre>
                        </HoloPanel>
                    </section>

                    <section>
                        <h2 className="text-2xl font-light text-white mb-6">Kubernetes</h2>
                        <p className="text-sm text-gray-400 mb-4">
                            For K8s, use the experimental helm chart generator.
                        </p>
                        <HoloPanel>
                            <div className="text-sm font-mono text-gray-300">
                                $ qyro build --k8s
                            </div>
                        </HoloPanel>
                    </section>
                </div>
            </div>
        </div>
    );
};
