"use client";

import React, { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import { Check, Copy } from "lucide-react";

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

const CodeBlock: React.FC<{ language?: string; value: string }> = ({ language, value }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(value);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="my-2.5 rounded-md border border-[#232a3b] bg-[#0b0e16] overflow-hidden text-xs">
      <div className="flex items-center justify-between px-3 py-1.5 bg-[#121624] border-b border-[#1f2638] text-[11px] text-zinc-400 font-mono">
        <span>{language || "code"}</span>
        <button
          onClick={handleCopy}
          className="flex items-center gap-1 hover:text-zinc-200 transition text-[10px]"
        >
          {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
          <span>{copied ? "Nusxalandi" : "Nusxa"}</span>
        </button>
      </div>
      <pre className="p-3 overflow-x-auto font-mono text-[11.5px] leading-relaxed text-zinc-300">
        <code>{value}</code>
      </pre>
    </div>
  );
};

export const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({ content, className = "" }) => {
  return (
    <div className={`prose prose-invert max-w-none text-xs leading-relaxed ${className}`}>
      <ReactMarkdown
        remarkPlugins={[remarkMath]}
        rehypePlugins={[rehypeKatex]}
        components={{
          p({ children }) {
            return <p className="mb-2 last:mb-0 leading-relaxed text-zinc-200">{children}</p>;
          },
          h1({ children }) {
            return <h1 className="text-base font-semibold text-zinc-100 mt-4 mb-2 pb-1 border-b border-zinc-800">{children}</h1>;
          },
          h2({ children }) {
            return <h2 className="text-sm font-semibold text-zinc-100 mt-3 mb-1.5">{children}</h2>;
          },
          h3({ children }) {
            return <h3 className="text-xs font-semibold text-indigo-300 mt-2 mb-1">{children}</h3>;
          },
          ul({ children }) {
            return <ul className="list-disc pl-4 mb-2 space-y-1 text-zinc-300">{children}</ul>;
          },
          ol({ children }) {
            return <ol className="list-decimal pl-4 mb-2 space-y-1 text-zinc-300">{children}</ol>;
          },
          li({ children }) {
            return <li className="leading-relaxed">{children}</li>;
          },
          blockquote({ children }) {
            return (
              <blockquote className="border-l-2 border-indigo-500/60 pl-3 my-2 text-zinc-400 italic bg-indigo-950/20 py-1 rounded-r">
                {children}
              </blockquote>
            );
          },
          table({ children }) {
            return (
              <div className="overflow-x-auto my-3 rounded border border-zinc-800 bg-[#0c0f17]">
                <table className="min-w-full divide-y divide-zinc-800 text-left text-xs">{children}</table>
              </div>
            );
          },
          thead({ children }) {
            return <thead className="bg-[#141926] text-zinc-200 font-semibold">{children}</thead>;
          },
          th({ children }) {
            return <th className="px-3 py-2 text-left text-[11px] uppercase tracking-wider text-zinc-300">{children}</th>;
          },
          td({ children }) {
            return <td className="px-3 py-2 border-t border-zinc-800/60 text-zinc-300 text-[11.5px]">{children}</td>;
          },
          code({ className, children, ...props }) {
            const match = /language-(\w+)/.exec(className || "");
            const isInline = !match && !String(children).includes("\n");

            if (isInline) {
              return (
                <code className="px-1.5 py-0.5 rounded bg-[#171d2b] border border-[#283247] text-indigo-300 font-mono text-[11px]">
                  {children}
                </code>
              );
            }

            return (
              <CodeBlock
                language={match ? match[1] : undefined}
                value={String(children).replace(/\n$/, "")}
              />
            );
          },
          a({ href, children }) {
            return (
              <a
                href={href}
                target="_blank"
                rel="noopener noreferrer"
                className="text-cyan-400 hover:text-cyan-300 underline underline-offset-2 transition"
              >
                {children}
              </a>
            );
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
};
