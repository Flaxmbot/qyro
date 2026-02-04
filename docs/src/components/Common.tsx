import React from 'react';
import { motion } from 'framer-motion';

interface CodeBlockProps {
  language: string;
  code: string;
  title?: string;
}

export function CodeBlock({ language, code, title }: CodeBlockProps) {
  return (
    <div className="my-6 rounded-lg border border-border bg-[#0d1117] overflow-hidden">
      {title && (
        <div className="flex items-center justify-between border-b border-border bg-surface px-4 py-2">
          <span className="text-xs font-mono text-textMuted">{title}</span>
          <span className="text-xs font-medium text-textMuted uppercase">{language}</span>
        </div>
      )}
      <div className="p-4 overflow-x-auto">
        <pre className="font-mono text-sm text-gray-300">
          <code>{code}</code>
        </pre>
      </div>
    </div>
  );
}

export function PageHeader({ title, description }: { title: string; description: string }) {
  return (
    <div className="mb-10 border-b border-border pb-10">
      <motion.h1
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-4xl font-bold tracking-tight text-white mb-4"
      >
        {title}
      </motion.h1>
      <motion.p
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="text-xl text-textMuted"
      >
        {description}
      </motion.p>
    </div>
  );
}

export function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="mb-12">
      <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-2">
        {title}
      </h2>
      <div className="text-textMuted leading-relaxed space-y-4">
        {children}
      </div>
    </section>
  );
}
