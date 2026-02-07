import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { useEffect, useState } from 'react';

// Particle component for background
const Particles = () => {
  const [particles] = useState(() =>
    Array.from({ length: 50 }, (_, i) => ({
      id: i,
      x: Math.random() * 100,
      y: Math.random() * 100,
      size: Math.random() * 3 + 1,
      delay: Math.random() * 4,
    }))
  );

  return (
    <div className="particles">
      {particles.map((p) => (
        <div
          key={p.id}
          className="particle"
          style={{
            left: `${p.x}%`,
            top: `${p.y}%`,
            width: p.size,
            height: p.size,
            animationDelay: `${p.delay}s`,
          }}
        />
      ))}
    </div>
  );
};

// Language card component
const LanguageCard = ({ lang, icon, color, delay }: { lang: string; icon: string; color: string; delay: number }) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ delay, duration: 0.5 }}
    className="glass-card p-6 text-center cursor-pointer"
    style={{ borderColor: color }}
  >
    <div className="text-4xl mb-3">{icon}</div>
    <div className="font-semibold">{lang}</div>
  </motion.div>
);

// Feature card component
const FeatureCard = ({ title, desc, icon, delay }: { title: string; desc: string; icon: string; delay: number }) => (
  <motion.div
    initial={{ opacity: 0, y: 30 }}
    whileInView={{ opacity: 1, y: 0 }}
    viewport={{ once: true }}
    transition={{ delay, duration: 0.6 }}
    className="glass-card p-8"
  >
    <div className="text-3xl mb-4">{icon}</div>
    <h3 className="text-xl font-semibold mb-2">{title}</h3>
    <p className="text-textMuted">{desc}</p>
  </motion.div>
);

export default function Home() {
  return (
    <div className="relative min-h-screen overflow-hidden">
      <Particles />

      {/* Floating orbs */}
      <div className="orb orb-primary w-96 h-96 -top-48 -left-48" />
      <div className="orb orb-accent w-64 h-64 top-1/2 -right-32" />
      <div className="orb orb-magenta w-48 h-48 bottom-32 left-1/4" />

      {/* Hero Section */}
      <section className="relative z-10 max-w-6xl mx-auto px-6 pt-32 pb-20">
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="text-center"
        >
          <div className="badge mb-6">
            <span className="w-2 h-2 bg-success rounded-full animate-pulse" />
            v3.0 — Now with Cross-Language RPC
          </div>

          <h1 className="hero-title mb-6">
            <span className="gradient-text">Universal</span>
            <br />
            Polyglot Runtime
          </h1>

          <p className="hero-subtitle mx-auto mb-10">
            Build microservices in Python, Rust, Java, Go, and more — all in a single file.
            Cross-language RPC that just works.
          </p>

          <div className="flex gap-4 justify-center flex-wrap">
            <Link to="/quickstart">
              <button className="btn-primary">
                Get Started →
              </button>
            </Link>
            <a
              href="https://github.com/qyro/qyro"
              className="px-8 py-4 rounded-2xl border border-border hover:border-primary transition-colors font-semibold"
            >
              View on GitHub
            </a>
          </div>
        </motion.div>

        {/* Language pills */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5, duration: 0.8 }}
          className="grid grid-cols-3 md:grid-cols-6 gap-4 mt-20"
        >
          <LanguageCard lang="Python" icon="🐍" color="#3572A5" delay={0.6} />
          <LanguageCard lang="Rust" icon="🦀" color="#DEA584" delay={0.7} />
          <LanguageCard lang="Java" icon="☕" color="#B07219" delay={0.8} />
          <LanguageCard lang="Go" icon="🐹" color="#00ADD8" delay={0.9} />
          <LanguageCard lang="C/C++" icon="⚡" color="#555555" delay={1.0} />
          <LanguageCard lang="React" icon="⚛️" color="#61DAFB" delay={1.1} />
        </motion.div>
      </section>

      <div className="section-divider" />

      {/* Code Preview */}
      <section className="relative z-10 max-w-5xl mx-auto px-6 py-20">
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          className="text-center mb-12"
        >
          <h2 className="text-3xl font-bold mb-4">One File. Multiple Languages.</h2>
          <p className="text-textMuted">Define your entire stack in a single .qyro file</p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="glow-border"
        >
          <pre className="code-block text-sm overflow-x-auto">
            <code>{`# app.qyro - Full-stack in one file

>>>python:api [fastapi, uvicorn]
from python_adapter import expose, call

@expose
def calculate(a: int, b: int) -> int:
    return a + b

>>>rust:crypto []
Qyro::expose("hash", |args| {
    Ok(json!(sha256(args[0].as_str())))
});

>>>web:frontend [react]
const result = await call("api.calculate", 1, 2);
// result = 3 ✨`}</code>
          </pre>
        </motion.div>
      </section>

      <div className="section-divider" />

      {/* Features Grid */}
      <section className="relative z-10 max-w-6xl mx-auto px-6 py-20">
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <h2 className="text-3xl font-bold mb-4">Why Qyro?</h2>
          <p className="text-textMuted">Everything you need for polyglot microservices</p>
        </motion.div>

        <div className="feature-grid">
          <FeatureCard
            title="Cross-Language RPC"
            desc="Call functions across services. Python → Rust → Java — seamlessly."
            icon="🔗"
            delay={0.1}
          />
          <FeatureCard
            title="Single-File Definition"
            desc="Define your entire stack in one .qyro file. No boilerplate."
            icon="📄"
            delay={0.2}
          />
          <FeatureCard
            title="Docker-Native"
            desc="Auto-generates Dockerfiles and docker-compose. Just run."
            icon="🐳"
            delay={0.3}
          />
          <FeatureCard
            title="6 Languages"
            desc="Python, Rust, Java, Go, C/C++, and TypeScript/React."
            icon="🌍"
            delay={0.4}
          />
          <FeatureCard
            title="Built-in Kafka & Redis"
            desc="Event streaming and shared state out of the box."
            icon="⚡"
            delay={0.5}
          />
          <FeatureCard
            title="VS Code Extension"
            desc="Syntax highlighting and snippets for all languages."
            icon="💜"
            delay={0.6}
          />
        </div>
      </section>

      {/* Stats */}
      <section className="relative z-10 max-w-4xl mx-auto px-6 py-20">
        <div className="glass-card p-8">
          <div className="grid grid-cols-3 gap-8">
            <div className="stat-card">
              <div className="stat-value">6</div>
              <div className="stat-label">Languages</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">1</div>
              <div className="stat-label">File</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">∞</div>
              <div className="stat-label">Possibilities</div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="relative z-10 max-w-4xl mx-auto px-6 py-20 text-center">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
        >
          <h2 className="text-4xl font-bold mb-6 gradient-text">Ready to go polyglot?</h2>
          <p className="text-xl text-textMuted mb-8">
            Install Qyro and build your first cross-language app in minutes.
          </p>
          <div className="glow-border inline-block">
            <pre className="bg-surface px-8 py-4 rounded-2xl font-mono text-lg">
              pip install qyro
            </pre>
          </div>
        </motion.div>
      </section>

      {/* Footer */}
      <footer className="relative z-10 border-t border-border py-12 mt-20">
        <div className="max-w-6xl mx-auto px-6 text-center text-textMuted">
          <p>Built with 💜 by the Qyro team</p>
          <p className="mt-2 text-sm">MIT License</p>
        </div>
      </footer>
    </div>
  );
}
