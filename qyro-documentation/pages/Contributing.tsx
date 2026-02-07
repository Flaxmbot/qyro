import React from 'react';
import { HoloPanel } from '../components/HoloPanel';
import { Link } from 'react-router-dom';

export const Contributing: React.FC = () => {
    return (
        <div className="flex flex-col xl:flex-row gap-12 px-6 py-12 lg:px-12 lg:py-16">
            <div className="flex-1 max-w-4xl min-h-[100vh]">
                <div className="flex items-center gap-2 text-[10px] uppercase tracking-widest text-gray-500 mb-8 font-mono">
                    <Link to="/" className="hover:text-white transition-colors">Docs</Link>
                    <span className="text-white/20">/</span>
                    <span>Resources</span>
                    <span className="text-white/20">/</span>
                    <span className="text-white">Contributing</span>
                </div>

                <h1 className="text-4xl md:text-5xl font-light tracking-tight text-white mb-6 relative">
                    Contributing
                    <span className="absolute -left-8 top-2 w-1 h-8 bg-pink-500 shadow-[0_0_10px_rgba(236,72,153,0.5)] hidden lg:block"></span>
                </h1>

                <p className="text-lg text-gray-400 leading-relaxed font-light mb-10 max-w-3xl">
                    We welcome contributions from the community! Qyro is open-source and we love pull requests.
                </p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-16">
                    <HoloPanel>
                        <h3 className="text-lg font-bold text-white mb-2">Report Bugs</h3>
                        <p className="text-sm text-gray-400 mb-4">
                            Found a bug? Open an issue on our GitHub repository with a reproduction case.
                        </p>
                        <a href="#" className="text-pink-400 text-xs hover:text-pink-300 uppercase tracking-widest font-bold">Open Issue &rarr;</a>
                    </HoloPanel>

                    <HoloPanel>
                        <h3 className="text-lg font-bold text-white mb-2">Submit PRs</h3>
                        <p className="text-sm text-gray-400 mb-4">
                            Fix bugs or add features. Please ensure you add tests for any new functionality.
                        </p>
                        <a href="#" className="text-pink-400 text-xs hover:text-pink-300 uppercase tracking-widest font-bold">View Pull Requests &rarr;</a>
                    </HoloPanel>
                </div>

                <div className="p-6 border border-white/10 bg-white/[0.02] rounded-sm">
                    <h3 className="text-white font-bold mb-4">Development Setup</h3>
                    <pre className="text-xs text-gray-500 font-mono leading-loose">
                        $ git clone https://github.com/qyro/qyro.git{'\n'}
                        $ cd qyro{'\n'}
                        $ pip install -e .{'\n'}
                        $ pytest
                    </pre>
                </div>
            </div>
        </div>
    );
};
