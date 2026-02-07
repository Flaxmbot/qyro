import React, { useState } from 'react';
import { useLocation } from 'react-router-dom';
import { HoloPanel } from '../components/HoloPanel';

// --- Components ---

const MethodBadge: React.FC<{ type: string }> = ({ type }) => {
    const styles: Record<string, string> = {
        FUNC: 'text-blue-400 border-blue-500/30 bg-blue-500/5 shadow-[0_0_10px_rgba(59,130,246,0.1)]',
        ASYNC: 'text-purple-400 border-purple-500/30 bg-purple-500/5 shadow-[0_0_10px_rgba(168,85,247,0.1)]',
        EVENT: 'text-orange-400 border-orange-500/30 bg-orange-500/5 shadow-[0_0_10px_rgba(249,115,22,0.1)]',
        STATE: 'text-green-400 border-green-500/30 bg-green-500/5 shadow-[0_0_10px_rgba(34,197,94,0.1)]',
    };

    return (
        <span className={`font-mono font-bold tracking-widest text-[0.6rem] px-2.5 py-1 border rounded-[2px] backdrop-blur-md ${styles[type] || 'text-gray-500 border-gray-500/30'}`}>
            {type}
        </span>
    );
};

const TabButton: React.FC<{ active: boolean; onClick: () => void; children: React.ReactNode }> = ({ active, onClick, children }) => (
    <button
        onClick={onClick}
        className={`text-[10px] font-bold uppercase tracking-wider py-2 px-4 border-b-2 transition-all ${active ? 'text-white border-white' : 'text-gray-600 border-transparent hover:text-gray-400'}`}
    >
        {children}
    </button>
);

// --- Data ---

interface Endpoint {
    id: string;
    type: string;
    signature: string;
    title: string;
    description: string;
    params?: { name: string; type: string; required: boolean; desc: string }[];
    exampleCode: React.ReactNode;
}

interface Section {
    title: string;
    endpoints: Endpoint[];
}

const sections: Section[] = [
    {
        title: "Microservices & RPC",
        endpoints: [
            {
                id: "expose",
                type: "FUNC",
                signature: "@expose(name=None)",
                title: "Expose Function",
                description: "Decorator to register a function as an RPC endpoint. Makes the function callable from other services.",
                params: [
                    { name: "name", type: "str", required: false, desc: "Custom name for the endpoint. Defaults to function name." }
                ],
                exampleCode: (
                    <>
                        <span className="text-yellow-300">@expose</span>{'\n'}
                        <span className="text-purple-400">def</span> <span className="text-blue-300">calculate_tax</span>(amount: <span className="text-green-300">float</span>):{'\n'}
                        {'    '}<span className="text-gray-500">"""Available as 'billing.calculate_tax'"""</span>{'\n'}
                        {'    '}<span className="text-purple-400">return</span> amount * <span className="text-orange-300">0.2</span>
                    </>
                )
            },
            {
                id: "call",
                type: "ASYNC",
                signature: "call(func_name, *args, **kwargs)",
                title: "Call Service",
                description: "Invokes a remote function on another service. Handles serialization and transport transparently.",
                params: [
                    { name: "func_name", type: "str", required: true, desc: "Full path 'service.function'" },
                    { name: "*args", type: "any", required: false, desc: "Positional arguments" }
                ],
                exampleCode: (
                    <>
                        <span className="text-gray-500"># Call the billing service from Python</span>{'\n'}
                        <span className="text-purple-400">from</span> qyro_adapters <span className="text-purple-400">import</span> call{'\n'}
                        {'\n'}
                        <span className="text-white">total</span> = call(<span className="text-green-300">"billing.calculate_tax"</span>, <span className="text-orange-300">100.0</span>)
                    </>
                )
            }
        ]
    },
    {
        title: "Shared State (Redis)",
        endpoints: [
            {
                id: "set",
                type: "STATE",
                signature: "set(key, value, ttl=None)",
                title: "Set Value",
                description: "Writes a value to the shared distributed memory. Atomic across all services.",
                params: [
                    { name: "key", type: "str", required: true, desc: "Unique identifier" },
                    { name: "value", type: "any", required: true, desc: "Serializable object" }
                ],
                exampleCode: (
                    <>
                        <span className="text-gray-500"># Set user session</span>{'\n'}
                        <span className="text-purple-400">await</span> qyro.set(<span className="text-green-300">"session:123"</span>, {'{'}<span className="text-green-300">"uid"</span>: <span className="text-orange-300">99</span>{'}'})
                    </>
                )
            },
            {
                id: "get",
                type: "STATE",
                signature: "get(key)",
                title: "Get Value",
                description: "Retrieves a value from shared memory. Returns None if key does not exist.",
                params: [
                    { name: "key", type: "str", required: true, desc: "Key to lookup" }
                ],
                exampleCode: (
                    <>
                        <span className="text-white">user</span> = qyro.get(<span className="text-green-300">"session:123"</span>)
                    </>
                )
            }
        ]
    },
    {
        title: "Event Bus (Kafka)",
        endpoints: [
            {
                id: "publish",
                type: "EVENT",
                signature: "publish(topic, message)",
                title: "Publish Event",
                description: "Broadcasts a message to a named topic. Fire-and-forget pattern.",
                params: [
                    { name: "topic", type: "str", required: true, desc: "Event channel name" },
                    { name: "message", type: "dict", required: true, desc: "Event payload" }
                ],
                exampleCode: (
                    <>
                        <span className="text-purple-400">from</span> qyro_adapters <span className="text-purple-400">import</span> publish{'\n'}
                        {'\n'}
                        publish(<span className="text-green-300">"user_signups"</span>, {'{'}<span className="text-green-300">"email"</span>: <span className="text-green-300">"test@qyro.io"</span>{'}'})
                    </>
                )
            }
        ]
    }
];

export const ApiReference: React.FC = () => {
    const [searchTerm, setSearchTerm] = useState('');
    const location = useLocation();

    const scrollToSection = (id: string) => {
        const element = document.getElementById(id);
        if (element) {
            element.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    };

    React.useEffect(() => {
        if (location.hash) {
            const id = location.hash.replace('#', '');
            // Small delay to ensure DOM is ready
            setTimeout(() => scrollToSection(id), 100);
        }
    }, [location]);

    return (
        <div className="flex flex-col xl:flex-row min-h-screen">

            {/* LEFT SIDEBAR: Navigation (Sticky) */}
            <aside className="w-full xl:w-80 border-b xl:border-b-0 xl:border-r border-white/10 bg-black/40 backdrop-blur-md sticky top-16 xl:h-[calc(100vh-64px)] z-20 overflow-y-auto custom-scrollbar">
                <div className="p-6">
                    <div className="relative mb-8 group">
                        <span className="material-symbols-outlined absolute left-3 top-2.5 text-gray-500 group-focus-within:text-holo-blue transition-colors text-[18px]">search</span>
                        <input
                            type="text"
                            placeholder="Filter functions..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className="w-full bg-white/5 border border-white/10 rounded-sm py-2 pl-10 pr-4 text-xs text-white placeholder-gray-600 focus:outline-none focus:border-holo-blue/30 focus:bg-white/10 transition-all font-mono"
                        />
                    </div>

                    <div className="space-y-8">
                        {sections.map((section) => (
                            <div key={section.title}>
                                <h3 className="text-[10px] font-bold text-gray-500 uppercase tracking-[0.2em] mb-4 pl-2 border-l-2 border-transparent">{section.title}</h3>
                                <ul className="space-y-1">
                                    {section.endpoints.filter(e => e.title.toLowerCase().includes(searchTerm.toLowerCase())).map((ep) => (
                                        <li key={ep.id}>
                                            <button
                                                onClick={() => scrollToSection(ep.id)}
                                                className="w-full text-left px-3 py-2 rounded-sm hover:bg-white/5 group transition-colors flex items-center justify-between"
                                            >
                                                <span className="text-xs text-gray-400 group-hover:text-white transition-colors">{ep.title}</span>
                                                <span className={`text-[9px] font-mono font-bold opacity-0 group-hover:opacity-100 transition-opacity ${ep.type === 'FUNC' ? 'text-blue-400' :
                                                    ep.type === 'ASYNC' ? 'text-purple-400' :
                                                        ep.type === 'STATE' ? 'text-green-400' : 'text-orange-400'
                                                    }`}>{ep.type}</span>
                                            </button>
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        ))}
                    </div>
                </div>
            </aside>

            {/* MAIN CONTENT */}
            <main className="flex-1 p-4 md:p-8 lg:p-12 w-full min-w-0">
                <div className="mb-16">
                    <div className="flex items-center gap-4 mb-4">
                        <h1 className="text-3xl md:text-4xl font-light text-white tracking-tight">SDK Reference</h1>
                        <div className="px-3 py-1 bg-green-500/10 border border-green-500/20 rounded-full flex items-center gap-2">
                            <span className="size-1.5 bg-green-500 rounded-full animate-pulse"></span>
                            <span className="text-[10px] font-bold text-green-400 uppercase tracking-widest">v1.0.0</span>
                        </div>
                    </div>
                    <p className="text-gray-400 max-w-2xl font-light text-sm md:text-base">
                        Standard library documentation for Qyro Adapters. These functions are available in all guest languages (Python, JS, Rust, Go).
                    </p>
                </div>

                <div className="space-y-24">
                    {sections.map((section) => (
                        <div key={section.title}>
                            <h2 className="text-xl md:text-2xl font-light text-white mb-8 flex items-center gap-3">
                                <span className="material-symbols-outlined text-gray-600">{section.title.includes('RPC') ? 'cloud_sync' : section.title.includes('State') ? 'database' : 'hub'}</span>
                                {section.title}
                            </h2>

                            <div className="space-y-16">
                                {section.endpoints.map((ep) => (
                                    <div key={ep.id} id={ep.id} className="scroll-mt-24 group">
                                        <HoloPanel noPadding className="overflow-hidden">
                                            <div className="flex flex-col lg:flex-row w-full">

                                                {/* Left: Documentation */}
                                                <div className="flex-1 p-6 md:p-8 border-b lg:border-b-0 lg:border-r border-white/10 bg-gradient-to-br from-white/[0.02] to-transparent">

                                                    {/* Header */}
                                                    <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4 mb-6">
                                                        <div className="space-y-2 w-full">
                                                            <div className="flex flex-wrap items-center gap-3">
                                                                <MethodBadge type={ep.type} />
                                                                <span className="font-mono text-xs md:text-sm text-white/90 break-all">{ep.signature}</span>
                                                                <button
                                                                    onClick={() => navigator.clipboard.writeText(ep.signature)}
                                                                    className="text-gray-600 hover:text-white transition-colors"
                                                                    title="Copy signature"
                                                                >
                                                                    <span className="material-symbols-outlined text-[14px]">content_copy</span>
                                                                </button>
                                                            </div>
                                                            <h3 className="text-lg md:text-xl font-bold text-white">{ep.title}</h3>
                                                        </div>
                                                    </div>

                                                    <p className="text-xs md:text-sm text-gray-400 leading-relaxed mb-8 border-b border-white/5 pb-8">
                                                        {ep.description}
                                                    </p>

                                                    {/* Parameters Table */}
                                                    {ep.params && (
                                                        <div>
                                                            <h4 className="text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-4">Parameters</h4>
                                                            <div className="space-y-3">
                                                                {ep.params.map((param) => (
                                                                    <div key={param.name} className="flex flex-col sm:flex-row sm:items-baseline gap-2 sm:gap-8 text-sm">
                                                                        <div className="min-w-[140px] flex items-center gap-2">
                                                                            <code className="text-holo-blue font-mono text-xs">{param.name}</code>
                                                                            {param.required && <span className="text-[9px] text-red-400 uppercase tracking-wider font-bold">Req</span>}
                                                                        </div>
                                                                        <div className="flex-1 flex flex-col sm:flex-row gap-2 sm:gap-4">
                                                                            <span className="text-gray-500 font-mono text-xs italic">{param.type}</span>
                                                                            <span className="text-gray-400 text-xs">{param.desc}</span>
                                                                        </div>
                                                                    </div>
                                                                ))}
                                                            </div>
                                                        </div>
                                                    )}
                                                </div>

                                                {/* Right: Code Example */}
                                                <div className="w-full lg:w-[45%] xl:w-[40%] bg-black/40 flex flex-col border-l border-white/5">
                                                    <div className="p-6 bg-black/20 h-full">
                                                        <div className="font-mono text-xs leading-loose whitespace-pre-wrap break-all text-gray-300">
                                                            {ep.exampleCode}
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        </HoloPanel>
                                    </div>
                                ))}
                            </div>
                        </div>
                    ))}
                </div>
            </main>
        </div>
    );
};