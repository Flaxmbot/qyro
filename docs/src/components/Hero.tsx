import React from 'react';
import { motion } from 'framer-motion';
import { ArrowRight, Terminal, Cpu, Zap, Globe, Shield } from 'lucide-react';
import { Link } from 'react-router-dom';

export function Hero() {
  return (
    <div className="relative mb-20 overflow-hidden">
      <div className="absolute top-0 right-0 -z-10 h-[500px] w-[500px] rounded-full bg-primary/5 blur-[120px]" aria-hidden="true" />
      <div className="absolute bottom-0 left-0 -z-10 h-[300px] w-[300px] rounded-full bg-accent/5 blur-[100px]" aria-hidden="true" />

      <div className="flex flex-col gap-6 lg:gap-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="inline-flex items-center gap-2 rounded-full border border-border bg-surfaceHighlight/50 px-3 py-1 text-xs font-medium text-primary w-fit"
        >
          <span className="relative flex h-2 w-2" aria-hidden="true">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-primary"></span>
          </span>
          v3.0.0 Now Available
        </motion.div>

        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="text-5xl font-bold tracking-tight text-white lg:text-7xl"
        >
          The <span className="text-transparent bg-clip-text bg-gradient-to-r from-white to-textMuted">Singularity</span> <br/> for Code.
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="max-w-2xl text-xl text-textMuted"
        >
          Write Python, C, Rust, Go, Java, and TypeScript in a single file.
          Orchestrate with zero-latency shared state and reliable event streams.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.3 }}
          className="flex flex-wrap gap-4 mt-4"
        >
          <Link
            to="/quick-start"
            className="inline-flex items-center gap-2 rounded-lg bg-white px-6 py-3 text-sm font-semibold text-black transition-transform hover:scale-105"
          >
            Get Started <ArrowRight size={16} />
          </Link>
          <Link
            to="/architecture"
            className="inline-flex items-center gap-2 rounded-lg border border-border bg-surface px-6 py-3 text-sm font-semibold text-text transition-colors hover:bg-surfaceHighlight"
          >
            View Architecture
          </Link>
        </motion.div>
      </div>

      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.8, delay: 0.4 }}
        className="mt-16 rounded-xl border border-border bg-[#0d1117] shadow-2xl overflow-hidden"
        role="region"
        aria-label="Code example showing Qyro syntax"
      >
        <div className="flex items-center gap-2 border-b border-border bg-surface px-4 py-3" aria-hidden="true">
          <div className="flex gap-1.5">
            <div className="h-3 w-3 rounded-full bg-danger/80" />
            <div className="h-3 w-3 rounded-full bg-[#eab308]/80" />
            <div className="h-3 w-3 rounded-full bg-accent/80" />
          </div>
          <div className="ml-4 text-xs font-mono text-textMuted">main.qyro</div>
        </div>
        <div className="p-6 font-mono text-sm overflow-x-auto">
          <CodeLine line="1" content={<><span className="text-purple-400">&gt;&gt;&gt;</span><span className="text-blue-400">schema</span>:global</>} />
          <CodeLine line="2" content={<span className="text-gray-500"># Define shared state variables</span>} />
          <CodeLine line="3" content={<><span className="text-blue-300">counter</span>: <span className="text-yellow-300">int</span></>} />
          <CodeLine line="4" content="" />
          <CodeLine line="5" content={<><span className="text-purple-400">&gt;&gt;&gt;</span><span className="text-blue-400">python</span>:p1</>} />
          <CodeLine line="6" content={<><span className="text-red-400">from</span> qyro.lib <span className="text-red-400">import</span> shared</>} />
          <CodeLine line="7" content={<><span className="text-red-400">while</span> <span className="text-blue-300">True</span>:</>} />
          <CodeLine line="8" content={<>    val = shared.get(<span className="text-green-400">"counter"</span>) or 0</>} />
          <CodeLine line="9" content={<>    shared.set(<span className="text-green-400">"counter"</span>, val + 1)</>} />
          <CodeLine line="10" content="" />
          <CodeLine line="11" content={<><span className="text-purple-400">&gt;&gt;&gt;</span><span className="text-blue-400">c</span>:p2</>} />
          <CodeLine line="12" content={<><span className="text-yellow-300">int</span> <span className="text-blue-300">main</span>() &#123;</>} />
          <CodeLine line="13" content={<>    <span className="text-yellow-300">printf</span>(<span className="text-green-400">"C watching shared memory...\n"</span>);</>} />
          <CodeLine line="14" content={<>    <span className="text-red-400">return</span> 0;</>} />
          <CodeLine line="15" content={<>&#125;</>} />
        </div>
      </motion.div>
    </div>
  );
}

function CodeLine({ line, content }: { line: string; content: React.ReactNode }) {
  return (
    <div className="flex gap-4">
      <div className="w-6 select-none text-right text-gray-600">{line}</div>
      <div className="text-gray-300 whitespace-pre">{content}</div>
    </div>
  );
}

export function FeatureGrid() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <FeatureCard
        icon={<Globe className="text-blue-500" />}
        title="True Polyglot"
        description="Write Python, C, Rust, Go, Java, and TypeScript in a single file with unified context."
      />
      <FeatureCard
        icon={<Cpu className="text-emerald-500" />}
        title="Shared Memory"
        description="Zero-latency state synchronization across processes using Redis-backed memory."
      />
      <FeatureCard
        icon={<Zap className="text-yellow-500" />}
        title="Event Driven"
        description="Built-in Kafka integration for reliable, scalable, and persistent message streams."
      />
      <FeatureCard
        icon={<Shield className="text-red-500" />}
        title="Self Healing"
        description="Automatic process supervision, crash detection, and exponential backoff strategies."
      />
      <FeatureCard
        icon={<Terminal className="text-purple-500" />}
        title="Native Speed"
        description="Compile critical paths to native C/Rust binaries automatically on runtime."
      />
      <FeatureCard
        icon={<ArrowRight className="text-white" />}
        title="API Gateway"
        description="Integrated WebSocket and HTTP gateway for seamless external connectivity."
      />
    </div>
  );
}

function FeatureCard({ icon, title, description }: { icon: React.ReactNode; title: string; description: string }) {
  return (
    <motion.div
      whileHover={{ y: -5 }}
      className="p-6 rounded-xl border border-border bg-surface transition-colors hover:border-primary/20 hover:bg-surfaceHighlight"
    >
      <div className="mb-4 inline-flex h-10 w-10 items-center justify-center rounded-lg bg-surfaceHighlight border border-border">
        {icon}
      </div>
      <h3 className="mb-2 text-lg font-semibold text-white">{title}</h3>
      <p className="text-sm text-textMuted leading-relaxed">{description}</p>
    </motion.div>
  );
}
