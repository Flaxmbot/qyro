import React from 'react';
import { HoloPanel } from '../components/HoloPanel';
import { Link } from 'react-router-dom';

export const Blog: React.FC = () => {
    const posts = [
        {
            title: "Announcing Qyro 2.0: The Universal Polyglot Runtime",
            date: "October 15, 2025",
            summary: "Today we are releasing Qyro 2.0, rewriting the core in Rust and introducing zero-config support for Node.js and Go.",
            tag: "Release"
        },
        {
            title: "Why we chose Kafka over HTTP for Microservices",
            date: "September 28, 2025",
            summary: "HTTP/REST is great for public APIs, but for internal service communication, event-driven architectures offer superior decoupling and resilience.",
            tag: "Engineering"
        },
        {
            title: "Building High-Frequency Trading Bots with Qyro",
            date: "August 10, 2025",
            summary: "A community case study on how HedgeFundX reduced latency by 40% using Qyro's shared memory transport.",
            tag: "Case Study"
        }
    ];

    return (
        <div className="flex flex-col xl:flex-row gap-12 px-6 py-12 lg:px-12 lg:py-16">
            <div className="flex-1 max-w-4xl min-h-[100vh]">
                <div className="flex items-center gap-2 text-[10px] uppercase tracking-widest text-gray-500 mb-8 font-mono">
                    <Link to="/" className="hover:text-white transition-colors">Docs</Link>
                    <span className="text-white/20">/</span>
                    <span className="text-white">Blog</span>
                </div>

                <h1 className="text-4xl md:text-5xl font-light tracking-tight text-white mb-12 relative">
                    Latest Updates
                    <span className="absolute -left-8 top-2 w-1 h-8 bg-cyan-500 shadow-[0_0_10px_rgba(6,182,212,0.5)] hidden lg:block"></span>
                </h1>

                <div className="grid gap-8">
                    {posts.map((post, idx) => (
                        <div key={idx} className="group relative p-8 border border-white/10 bg-white/[0.02] hover:bg-white/[0.04] transition-colors rounded-sm overflow-hidden">
                            <div className="absolute top-0 left-0 w-[2px] h-full bg-holo-blue opacity-0 group-hover:opacity-100 transition-opacity"></div>

                            <div className="flex items-center gap-4 text-xs font-mono mb-4 text-gray-500">
                                <span>{post.date}</span>
                                <span className="w-1 h-1 rounded-full bg-white/20"></span>
                                <span className="text-holo-blue uppercase tracking-wider">{post.tag}</span>
                            </div>

                            <h2 className="text-2xl font-light text-white mb-4 group-hover:text-holo-blue transition-colors">
                                {post.title}
                            </h2>

                            <p className="text-gray-400 mb-6 leading-relaxed">
                                {post.summary}
                            </p>

                            <div className="flex items-center gap-2 text-sm text-holo-blue font-bold group-hover:gap-3 transition-all">
                                Read Article <span className="material-symbols-outlined text-sm">arrow_forward</span>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};
