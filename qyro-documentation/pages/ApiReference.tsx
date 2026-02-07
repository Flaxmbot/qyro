import React, { useState } from 'react';
import { HoloPanel } from '../components/HoloPanel';

// --- Components ---

const MethodBadge: React.FC<{ method: string }> = ({ method }) => {
  const styles: Record<string, string> = {
    GET: 'text-blue-400 border-blue-500/30 bg-blue-500/5 shadow-[0_0_10px_rgba(59,130,246,0.1)]',
    POST: 'text-green-400 border-green-500/30 bg-green-500/5 shadow-[0_0_10px_rgba(34,197,94,0.1)]',
    PUT: 'text-orange-400 border-orange-500/30 bg-orange-500/5 shadow-[0_0_10px_rgba(249,115,22,0.1)]',
    DELETE: 'text-red-400 border-red-500/30 bg-red-500/5 shadow-[0_0_10px_rgba(239,68,68,0.1)]',
  };
  
  return (
    <span className={`font-mono font-bold tracking-widest text-[0.6rem] px-2.5 py-1 border rounded-[2px] backdrop-blur-md ${styles[method] || 'text-gray-500 border-gray-500/30'}`}>
      {method}
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

// --- Simulation Logic ---

interface ApiConsoleProps {
    response: React.ReactNode;
}

const ApiConsole: React.FC<ApiConsoleProps> = ({ response }) => {
    const [status, setStatus] = useState<'idle' | 'loading' | 'success'>('idle');

    const handleRun = () => {
        setStatus('loading');
        setTimeout(() => setStatus('success'), 1500);
    };

    return (
        <div className="flex flex-col h-full">
            <div className="flex items-center justify-between p-2 border-b border-white/5 bg-white/[0.02] flex-none">
                <div className="flex gap-2">
                    <div className="size-2 rounded-full bg-red-500/20"></div>
                    <div className="size-2 rounded-full bg-yellow-500/20"></div>
                    <div className="size-2 rounded-full bg-green-500/20"></div>
                </div>
                <button 
                    onClick={handleRun}
                    disabled={status === 'loading'}
                    className={`flex items-center gap-2 px-3 py-1 rounded-[2px] text-[10px] font-bold uppercase tracking-wider transition-all
                        ${status === 'loading' ? 'bg-white/5 text-gray-500 cursor-wait' : 'bg-holo-blue/10 text-holo-blue border border-holo-blue/30 hover:bg-holo-blue/20 hover:shadow-[0_0_10px_rgba(165,243,252,0.2)]'}
                    `}
                >
                    <span className="material-symbols-outlined text-[14px]">{status === 'loading' ? 'progress_activity' : 'play_arrow'}</span>
                    {status === 'loading' ? 'Sending...' : 'Send Request'}
                </button>
            </div>
            
            <div className="flex-1 bg-black/40 p-4 font-mono text-xs overflow-auto custom-scrollbar relative min-h-[200px]">
                {status === 'idle' && (
                    <div className="h-full flex flex-col items-center justify-center text-gray-600 gap-2">
                        <span className="material-symbols-outlined text-3xl opacity-20">terminal</span>
                        <span>Ready to simulate request</span>
                    </div>
                )}
                
                {status === 'loading' && (
                     <div className="h-full flex flex-col items-center justify-center text-gray-500 gap-4">
                        <div className="w-48 h-1 bg-white/10 rounded-full overflow-hidden">
                            <div className="h-full bg-holo-blue/50 animate-progress-indeterminate"></div>
                        </div>
                        <span className="text-[10px] uppercase tracking-widest animate-pulse">Connecting to Runtime...</span>
                    </div>
                )}

                {status === 'success' && (
                    <div className="animate-fade-in">
                        <div className="flex items-center gap-2 mb-2 text-green-400 text-[10px] uppercase tracking-widest">
                            <span className="material-symbols-outlined text-sm">check_circle</span>
                            200 OK <span className="text-gray-600 ml-2">124ms</span>
                        </div>
                        <div className="leading-loose text-gray-300 whitespace-pre-wrap break-all">
                            {response}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}

// --- Data ---

interface Endpoint {
    id: string;
    method: string;
    path: string;
    title: string;
    description: string;
    params?: { name: string; type: string; required: boolean; desc: string }[];
    responseCode: React.ReactNode;
}

interface Section {
    title: string;
    endpoints: Endpoint[];
}

const sections: Section[] = [
    {
        title: "Runtime Management",
        endpoints: [
            {
                id: "create-runtime",
                method: "POST",
                path: "/v1/runtimes/create",
                title: "Create Runtime",
                description: "Provisions a new isolated execution environment. The runtime is created in a cold state and warms up upon the first execution request.",
                params: [
                    { name: "language", type: "string", required: true, desc: "Target language (python, rust, node, go)" },
                    { name: "version", type: "string", required: false, desc: "Specific version tag (e.g., '3.11')" },
                    { name: "memory_mb", type: "integer", required: false, desc: "Memory allocation limit (default: 128)" }
                ],
                responseCode: (
                    <>
                        <span className="text-gray-500">{'{'}</span><br/>
                        &nbsp;&nbsp;<span className="text-purple-400">"id"</span>: <span className="text-green-300">"rt_8f92ns92"</span>,<br/>
                        &nbsp;&nbsp;<span className="text-purple-400">"status"</span>: <span className="text-green-300">"provisioning"</span>,<br/>
                        &nbsp;&nbsp;<span className="text-purple-400">"region"</span>: <span className="text-green-300">"us-east-1"</span>,<br/>
                        &nbsp;&nbsp;<span className="text-purple-400">"expires_at"</span>: <span className="text-orange-300">1709238492</span><br/>
                        <span className="text-gray-500">{'}'}</span>
                    </>
                )
            },
            {
                id: "execute-code",
                method: "POST",
                path: "/v1/runtimes/{id}/execute",
                title: "Execute Code",
                description: "Synchronously executes a code snippet within the specified runtime context. Supports stdout/stderr capturing.",
                params: [
                    { name: "code", type: "string", required: true, desc: "Base64 encoded source code" },
                    { name: "timeout", type: "integer", required: false, desc: "Execution timeout in ms" }
                ],
                responseCode: (
                    <>
                        <span className="text-gray-500">{'{'}</span><br/>
                        &nbsp;&nbsp;<span className="text-purple-400">"stdout"</span>: <span className="text-green-300">"Hello World\n"</span>,<br/>
                        &nbsp;&nbsp;<span className="text-purple-400">"stderr"</span>: <span className="text-green-300">""</span>,<br/>
                        &nbsp;&nbsp;<span className="text-purple-400">"duration_ms"</span>: <span className="text-orange-300">42</span>,<br/>
                        &nbsp;&nbsp;<span className="text-purple-400">"exit_code"</span>: <span className="text-orange-300">0</span><br/>
                        <span className="text-gray-500">{'}'}</span>
                    </>
                )
            }
        ]
    },
    {
        title: "Ephemeral Storage",
        endpoints: [
            {
                id: "set-key",
                method: "PUT",
                path: "/v1/store/{key}",
                title: "Set Value",
                description: "Sets a value in the high-speed ephemeral key-value store. Values are automatically evicted after the TTL expires.",
                params: [
                    { name: "value", type: "string", required: true, desc: "Data payload (max 1MB)" },
                    { name: "ttl", type: "integer", required: false, desc: "Time to live in seconds" }
                ],
                responseCode: (
                    <>
                        <span className="text-gray-500">{'{'}</span><br/>
                        &nbsp;&nbsp;<span className="text-purple-400">"key"</span>: <span className="text-green-300">"session_user_1"</span>,<br/>
                        &nbsp;&nbsp;<span className="text-purple-400">"updated"</span>: <span className="text-blue-300">true</span><br/>
                        <span className="text-gray-500">{'}'}</span>
                    </>
                )
            }
        ]
    }
];

export const ApiReference: React.FC = () => {
    const [searchTerm, setSearchTerm] = useState('');

    const scrollToSection = (id: string) => {
        const element = document.getElementById(id);
        if (element) {
            element.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    };

    return (
        <div className="flex flex-col xl:flex-row min-h-screen">
            
            {/* LEFT SIDEBAR: Navigation (Sticky) */}
            <aside className="w-full xl:w-80 border-b xl:border-b-0 xl:border-r border-white/10 bg-black/40 backdrop-blur-md sticky top-16 xl:h-[calc(100vh-64px)] z-20 overflow-y-auto custom-scrollbar">
                <div className="p-6">
                    <div className="relative mb-8 group">
                        <span className="material-symbols-outlined absolute left-3 top-2.5 text-gray-500 group-focus-within:text-holo-blue transition-colors text-[18px]">search</span>
                        <input 
                            type="text" 
                            placeholder="Filter endpoints..." 
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
                                                <span className={`text-[9px] font-mono font-bold opacity-0 group-hover:opacity-100 transition-opacity ${
                                                    ep.method === 'GET' ? 'text-blue-400' :
                                                    ep.method === 'POST' ? 'text-green-400' :
                                                    ep.method === 'PUT' ? 'text-orange-400' : 'text-red-400'
                                                }`}>{ep.method}</span>
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
                        <h1 className="text-3xl md:text-4xl font-light text-white tracking-tight">API Reference</h1>
                        <div className="px-3 py-1 bg-green-500/10 border border-green-500/20 rounded-full flex items-center gap-2">
                            <span className="size-1.5 bg-green-500 rounded-full animate-pulse"></span>
                            <span className="text-[10px] font-bold text-green-400 uppercase tracking-widest">v2.4 Live</span>
                        </div>
                    </div>
                    <p className="text-gray-400 max-w-2xl font-light text-sm md:text-base">
                        The Qyro API allows you to programmatically manage runtimes and execute code. Base URL: <code className="text-holo-blue bg-holo-blue/10 px-1 py-0.5 rounded text-xs">https://api.qyro.io</code>
                    </p>
                </div>

                <div className="space-y-24">
                    {sections.map((section) => (
                        <div key={section.title}>
                            <h2 className="text-xl md:text-2xl font-light text-white mb-8 flex items-center gap-3">
                                <span className="material-symbols-outlined text-gray-600">{section.title === 'Runtime Management' ? 'memory' : 'dataset'}</span>
                                {section.title}
                            </h2>

                            <div className="space-y-16">
                                {section.endpoints.map((ep) => (
                                    <div key={ep.id} id={ep.id} className="scroll-mt-24 group">
                                        <HoloPanel noPadding className="overflow-hidden">
                                            <div className="flex flex-col lg:flex-row w-full">
                                                
                                                {/* Left: Documentation - Dynamic flex-1 */}
                                                <div className="flex-1 p-6 md:p-8 border-b lg:border-b-0 lg:border-r border-white/10 bg-gradient-to-br from-white/[0.02] to-transparent">
                                                    
                                                    {/* Header */}
                                                    <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4 mb-6">
                                                        <div className="space-y-2 w-full">
                                                            <div className="flex flex-wrap items-center gap-3">
                                                                <MethodBadge method={ep.method} />
                                                                <span className="font-mono text-xs md:text-sm text-white/90 break-all">{ep.path}</span>
                                                                <button 
                                                                    onClick={() => navigator.clipboard.writeText(ep.path)}
                                                                    className="text-gray-600 hover:text-white transition-colors"
                                                                    title="Copy path"
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
                                                            <h4 className="text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-4">Body Parameters</h4>
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

                                                {/* Right: Interactive Console / Preview - Dynamic height */}
                                                <div className="w-full lg:w-[45%] xl:w-[40%] bg-black/40 flex flex-col border-l border-white/5">
                                                    <EndpointPreview ep={ep} />
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

// Sub-component to manage state for each endpoint preview
const EndpointPreview: React.FC<{ ep: Endpoint }> = ({ ep }) => {
    const [activeTab, setActiveTab] = useState<'response' | 'console'>('response');

    return (
        <>
            <div className="flex items-center border-b border-white/5 bg-white/[0.02] flex-none">
                <TabButton active={activeTab === 'response'} onClick={() => setActiveTab('response')}>Example Response</TabButton>
                <TabButton active={activeTab === 'console'} onClick={() => setActiveTab('console')}>Live Console</TabButton>
            </div>

            <div className="flex-1 relative">
                {activeTab === 'response' ? (
                    <div className="p-6 bg-black/20 h-full">
                         <div className="font-mono text-xs leading-loose whitespace-pre-wrap break-all text-gray-300">
                            {ep.responseCode}
                         </div>
                    </div>
                ) : (
                    <div className="bg-black/30 h-full min-h-[300px]">
                        <ApiConsole response={ep.responseCode} />
                    </div>
                )}
            </div>
        </>
    );
};