"use client";

import React, { useState } from "react";
import { ToolCall } from "@/types";
import {
  Terminal,
  Check,
  AlertCircle,
  ChevronDown,
  ChevronRight,
  FileCode,
  Sparkles,
  Search,
  FolderTree,
  RotateCcw,
  Wrench,
  Globe,
  BookOpen,
  FileText,
  Bookmark,
  Download,
  Languages,
  Layers,
  ShieldCheck,
  Scissors,
} from "lucide-react";

export const ToolCallCard: React.FC<{ toolCall: ToolCall }> = ({ toolCall }) => {
  const [isExpanded, setIsExpanded] = useState(true);

  // Determine tool category & icon
  const getToolMeta = () => {
    switch (toolCall.name) {
      case "search_arxiv":
        return {
          title: "arXiv Preprint Search",
          icon: BookOpen,
          badgeColor: "text-rose-400 border-rose-800/50 bg-rose-950/40",
          cmdPrefix: "🔬 arXiv: ",
          cmd: toolCall.args?.query || "",
        };
      case "search_web":
        return {
          title: "Web Discovery (DuckDuckGo)",
          icon: Globe,
          badgeColor: "text-amber-400 border-amber-800/50 bg-amber-950/40",
          cmdPrefix: "🌐 Search: ",
          cmd: toolCall.args?.query || "",
        };
      case "fetch_web_page":
        return {
          title: "Web Article Reader",
          icon: FileText,
          badgeColor: "text-sky-400 border-sky-800/50 bg-sky-950/40",
          cmdPrefix: "📖 Read URL: ",
          cmd: toolCall.args?.url || "",
        };
      case "download_paper":
        return {
          title: "Academic Paper Downloader",
          icon: Download,
          badgeColor: "text-emerald-400 border-emerald-800/50 bg-emerald-950/40",
          cmdPrefix: "📥 Download: ",
          cmd: toolCall.args?.identifier_or_url || "",
        };
      case "download_and_extract_paper":
        return {
          title: "Paper Deep Reader & Extractor",
          icon: BookOpen,
          badgeColor: "text-indigo-400 border-indigo-800/50 bg-indigo-950/40",
          cmdPrefix: "📄 PDF: ",
          cmd: toolCall.args?.pdf_url_or_path || "",
        };
      case "decompose_paper_to_latex":
        return {
          title: "LaTeX Section Decomposer",
          icon: Scissors,
          badgeColor: "text-purple-400 border-purple-800/50 bg-purple-950/40",
          cmdPrefix: "✂️ Split to LaTeX: ",
          cmd: toolCall.args?.pdf_path || "",
        };
      case "translate_academic_latex":
        return {
          title: "Academic LaTeX Translator",
          icon: Languages,
          badgeColor: "text-teal-400 border-teal-800/50 bg-teal-950/40",
          cmdPrefix: "🌍 Translate: ",
          cmd: `${toolCall.args?.target_lang || "uz"} -> ${String(toolCall.args?.content_or_file || "").slice(0, 40)}`,
        };
      case "reassemble_latex_document":
        return {
          title: "LaTeX Document Reassembler",
          icon: Layers,
          badgeColor: "text-indigo-400 border-indigo-800/50 bg-indigo-950/40",
          cmdPrefix: "🧩 Reassemble: ",
          cmd: toolCall.args?.sections_dir || "",
        };
      case "audit_and_verify_latex":
        return {
          title: "LaTeX Syntax & Citation Auditor",
          icon: ShieldCheck,
          badgeColor: "text-amber-400 border-amber-800/50 bg-amber-950/40",
          cmdPrefix: "🧐 Audit: ",
          cmd: toolCall.args?.tex_file || "",
        };
      case "auto_fix_latex_errors":
        return {
          title: "Autonomous LaTeX Self-Healer",
          icon: Wrench,
          badgeColor: "text-green-400 border-green-800/50 bg-green-950/40",
          cmdPrefix: "🛠️ Auto-Fix: ",
          cmd: toolCall.args?.tex_file || "",
        };
      case "manage_bibtex":
        return {
          title: "BibTeX Citation Manager",
          icon: Bookmark,
          badgeColor: "text-emerald-400 border-emerald-800/50 bg-emerald-950/40",
          cmdPrefix: "📚 BibTeX: ",
          cmd: `${toolCall.args?.action || "manage"} ${toolCall.args?.query || ""}`,
        };
      case "extract_pdf_page":
        return {
          title: "PDF Page Extractor",
          icon: FileText,
          badgeColor: "text-blue-400 border-blue-800/50 bg-blue-950/40",
          cmdPrefix: "📑 Page: ",
          cmd: `${toolCall.args?.pdf_file || ""} (Page ${toolCall.args?.page_number || 1})`,
        };
      case "run_shell_command":
        return {
          title: "Terminal (PowerShell)",
          icon: Terminal,
          badgeColor: "text-emerald-400 border-emerald-800/50 bg-emerald-950/40",
          cmdPrefix: "$ ",
          cmd: toolCall.args?.command || "powershell",
        };
      case "edit_file":
        return {
          title: "File Patch (Surgical Edit)",
          icon: FileCode,
          badgeColor: "text-amber-400 border-amber-800/50 bg-amber-950/40",
          cmdPrefix: "⚡ Edit: ",
          cmd: toolCall.args?.path || "",
        };
      case "write_file":
        return {
          title: "Draft / File Creation",
          icon: FileCode,
          badgeColor: "text-blue-400 border-blue-800/50 bg-blue-950/40",
          cmdPrefix: "✍ Write: ",
          cmd: toolCall.args?.path || "",
        };
      case "compile_latex":
        return {
          title: "LaTeX Compiler (Tectonic)",
          icon: Sparkles,
          badgeColor: "text-purple-400 border-purple-800/50 bg-purple-950/40",
          cmdPrefix: "🔨 Tectonic: ",
          cmd: toolCall.args?.tex_file || "",
        };
      case "find_symbol":
      case "get_file_outline":
      case "find_references":
        return {
          title: "AST Symbol Engine",
          icon: Search,
          badgeColor: "text-cyan-400 border-cyan-800/50 bg-cyan-950/40",
          cmdPrefix: "🔍 Inspect: ",
          cmd: toolCall.args?.symbol_name || toolCall.args?.path || "",
        };
      case "undo_last_action":
        return {
          title: "Rollback (Undo)",
          icon: RotateCcw,
          badgeColor: "text-amber-400 border-amber-800/50 bg-amber-950/40",
          cmdPrefix: "⏪ Revert",
          cmd: "",
        };
      case "search_crossref":
        return {
          title: "CrossRef Global Journals",
          icon: Globe,
          badgeColor: "text-orange-400 border-orange-800/50 bg-orange-950/40",
          cmdPrefix: "🌐 CrossRef: ",
          cmd: toolCall.args?.query || "",
        };
      case "search_europepmc":
        return {
          title: "Europe PMC / PubMed Biomedical",
          icon: BookOpen,
          badgeColor: "text-teal-400 border-teal-800/50 bg-teal-950/40",
          cmdPrefix: "🧬 PubMed: ",
          cmd: toolCall.args?.query || "",
        };
      case "export_latex_to_docx":
        return {
          title: "Word (.docx) Export Engine",
          icon: FileText,
          badgeColor: "text-blue-400 border-blue-800/50 bg-blue-950/40",
          cmdPrefix: "📝 DOCX: ",
          cmd: toolCall.args?.tex_file || "",
        };
      case "verify_claims_against_sources":
        return {
          title: "Anti-Hallucination Fact Checker",
          icon: ShieldCheck,
          badgeColor: "text-emerald-400 border-emerald-800/50 bg-emerald-950/40",
          cmdPrefix: "🛡 Verify: ",
          cmd: toolCall.args?.source_pdf || "",
        };
      case "run_deep_research":
        return {
          title: "Autonomous Deep Research Studio",
          icon: Sparkles,
          badgeColor: "text-fuchsia-400 border-fuchsia-800/50 bg-fuchsia-950/40",
          cmdPrefix: "🚀 Deep Research: ",
          cmd: toolCall.args?.topic || "",
        };
      default:
        return {
          title: toolCall.name,
          icon: Wrench,
          badgeColor: "text-cyan-400 border-cyan-800/50 bg-cyan-950/40",
          cmdPrefix: "> ",
          cmd: Object.entries(toolCall.args || {}).map(([k, v]) => `${k}=${JSON.stringify(v)}`).join(" "),
        };
    }
  };

  const meta = getToolMeta();
  const IconComponent = meta.icon;

  return (
    <div className="my-2 rounded-lg border border-[#212638] bg-[#0c0e16] overflow-hidden text-xs shadow-md">
      {/* Sleek Terminal Title Bar without window dots */}
      <div
        onClick={() => setIsExpanded(!isExpanded)}
        className="px-3 py-1.5 bg-[#121622] border-b border-[#1f2536] flex items-center justify-between cursor-pointer hover:bg-[#161a29] transition select-none"
      >
        {/* Left: Tool Header */}
        <div className="flex items-center gap-2 truncate max-w-[75%]">
          <IconComponent className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
          <span className="font-semibold text-zinc-200 shrink-0 font-mono">{meta.title}</span>
          {meta.cmd && (
            <span className="text-[10.5px] text-zinc-400 truncate opacity-80 font-mono">
              ({meta.cmdPrefix}{meta.cmd})
            </span>
          )}
        </div>

        {/* Right: Status badge & Toggle */}
        <div className="flex items-center gap-2 shrink-0">
          {toolCall.status === "running" ? (
            <span className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-cyan-950/90 border border-cyan-500/60 text-cyan-300 text-[10px] font-mono animate-pulse shadow-xs">
              <span className="w-2 h-2 rounded-full border-2 border-cyan-400 border-t-transparent animate-spin"></span>
              <span className="font-semibold">Working...</span>
            </span>
          ) : toolCall.status === "error" ? (
            <span className="flex items-center gap-1 px-1.5 py-0.5 rounded bg-red-950/80 border border-red-700/60 text-red-300 text-[10px] font-mono">
              <AlertCircle className="w-3 h-3" />
              Xato
            </span>
          ) : (
            <span className="flex items-center gap-1 px-1.5 py-0.5 rounded bg-emerald-950/80 border border-emerald-700/60 text-emerald-300 text-[10px] font-mono">
              <Check className="w-3 h-3" />
              Tayyor
            </span>
          )}

          {isExpanded ? (
            <ChevronDown className="w-3 h-3 text-zinc-400" />
          ) : (
            <ChevronRight className="w-3 h-3 text-zinc-400" />
          )}
        </div>
      </div>

      {/* Terminal Body - Half Window Height (max-h-52) */}
      {isExpanded && (
        <div className="p-3 bg-[#06080e] font-mono text-[11px] space-y-2">
          {/* Active Command Line */}
          {meta.cmd && (
            <div className="flex items-start gap-1.5 text-cyan-300/90 bg-[#0d101a] px-2.5 py-1.5 rounded border border-[#1b2132]">
              <span className="text-zinc-500 font-bold select-none shrink-0">{meta.cmdPrefix}</span>
              <span className="whitespace-pre-wrap break-all">{meta.cmd}</span>
            </div>
          )}

          {/* If edit_file: Show Target and Replacement Snippets */}
          {toolCall.name === "edit_file" && toolCall.args?.target_snippet && (
            <div className="space-y-1">
              <div className="text-[10px] font-sans text-red-400 font-bold uppercase tracking-wider">
                - Search Snippet:
              </div>
              <pre className="p-1.5 rounded bg-red-950/20 border border-red-900/30 text-red-200/80 max-h-24 overflow-y-auto whitespace-pre-wrap">
                {toolCall.args.target_snippet}
              </pre>

              <div className="text-[10px] font-sans text-emerald-400 font-bold uppercase tracking-wider mt-0.5">
                + Replacement Snippet:
              </div>
              <pre className="p-1.5 rounded bg-emerald-950/20 border border-emerald-900/30 text-emerald-200/80 max-h-24 overflow-y-auto whitespace-pre-wrap">
                {toolCall.args.replacement}
              </pre>
            </div>
          )}

          {/* Active Working indicator when running and no result yet */}
          {toolCall.status === "running" && !toolCall.result && (
            <div className="p-2.5 rounded bg-[#090b12] border border-[#1a1f30] text-cyan-300 font-mono text-[11px] flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping"></span>
                <span className="animate-pulse font-medium">Working... so'rov bajarilmoqda va ma'lumotlar tahlil qilinmoqda</span>
              </div>
              <span className="text-[10px] text-zinc-500 font-mono">Real-time</span>
            </div>
          )}

          {/* Live Terminal Output - Half-window max-h-52 */}
          {toolCall.result && (
            <div>
              <div className="text-zinc-500 uppercase text-[9px] font-sans font-bold tracking-wider mb-1 flex items-center justify-between">
                <span>Natija (Terminal Output):</span>
                <span className="text-emerald-400 text-[10px]">Tugallandi</span>
              </div>
              <pre className="p-2.5 rounded-lg bg-[#090b12] border border-[#1a1f30] text-zinc-300 max-h-52 overflow-y-auto whitespace-pre-wrap leading-relaxed select-text">
                {toolCall.result}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
