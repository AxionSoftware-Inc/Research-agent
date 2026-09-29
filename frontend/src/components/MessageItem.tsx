"use client";

import React, { useState } from "react";
import { Message } from "@/types";
import { ToolCallCard } from "@/components/ToolCallCard";
import { MarkdownRenderer } from "@/components/MarkdownRenderer";
import { Bot, User, Brain, ChevronDown, ChevronRight, Copy, Check, FileText, Image as ImageIcon, BookOpen, Loader2, Sparkles, Activity } from "lucide-react";

export const MessageItem: React.FC<{ message: Message }> = ({ message }) => {
  const isUser = message.role === "user";
  const [showThinking, setShowThinking] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // USER MESSAGE: Right-Aligned, clean blue bubble
  if (isUser) {
    return (
      <div className="py-2.5 px-4 md:px-6 flex justify-end gap-2.5 group">
        <div className="flex flex-col items-end max-w-2xl space-y-1">
          <span className="text-[10px] font-medium text-zinc-400 select-none mr-1">
            Foydalanuvchi
          </span>

          <div className="rounded-lg bg-[#1e40af] text-white px-3.5 py-2 text-xs leading-relaxed whitespace-pre-wrap font-sans border border-[#3b82f6]/40 shadow-xs">
            {message.content}
          </div>

          {/* Attachments if any */}
          {message.attachments && message.attachments.length > 0 && (
            <div className="flex flex-wrap gap-1 justify-end">
              {message.attachments.map((att) => (
                <div
                  key={att.path}
                  className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-[#131926] border border-[#25324d] text-[11px] text-blue-200"
                >
                  {att.is_image ? (
                    <ImageIcon className="w-3 h-3 text-blue-400" />
                  ) : (
                    <FileText className="w-3 h-3 text-amber-400" />
                  )}
                  <span className="truncate max-w-[140px]">{att.file_name}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="shrink-0 mt-0.5">
          <div className="w-6 h-6 rounded border border-[#2b3c61] bg-[#172554] flex items-center justify-center text-blue-200">
            <User className="w-3.5 h-3.5" />
          </div>
        </div>
      </div>
    );
  }

  // AI ASSISTANT MESSAGE: Left-Aligned, clean developer format
  return (
    <div className="py-3 px-4 md:px-6 flex gap-2.5 bg-transparent">
      <div className="shrink-0 mt-0.5">
        <div className="w-6 h-6 rounded border border-indigo-700/50 bg-indigo-950/60 flex items-center justify-center text-indigo-300">
          <BookOpen className="w-3.5 h-3.5" />
        </div>
      </div>

      <div className="flex-1 min-w-0 space-y-2.5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5">
            <span className="text-xs font-medium text-zinc-100">AI Research Scientist</span>
            <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-indigo-950/40 text-indigo-300 border border-indigo-800/40">
              Literature Analyst
            </span>
          </div>
          {message.content && (
            <button
              onClick={handleCopy}
              className="text-zinc-500 hover:text-zinc-300 text-[11px] flex items-center gap-1 transition"
            >
              {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
              <span>{copied ? "Nusxalandi" : "Nusxa"}</span>
            </button>
          )}
        </div>

        {/* Live Research Activity Status Bar (Like Gemini / Perplexity) */}
        {message.progress && (
          <div className="flex items-center gap-2.5 px-3 py-2 rounded-lg bg-indigo-950/40 border border-indigo-700/50 text-xs text-indigo-200 shadow-sm backdrop-blur-xs">
            <span className="relative flex h-2 w-2 shrink-0">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-indigo-500"></span>
            </span>
            <span className="font-mono text-[11.5px] tracking-tight">{message.progress}</span>
          </div>
        )}

        {/* Live Thinking Stream Preview while streaming (before answer is finalized) */}
        {message.thinking && !message.content ? (
          <div className="rounded-lg border border-[#202738] bg-[#0c0f18] p-3 space-y-1.5 text-xs">
            <div className="flex items-center justify-between text-[11px] text-zinc-400 font-mono">
              <div className="flex items-center gap-1.5 text-indigo-300">
                <Brain className="w-3.5 h-3.5 animate-pulse text-indigo-400" />
                <span>Model fikrlash jarayoni (Thinking)...</span>
              </div>
              <span className="text-[10px] text-indigo-400/80 animate-pulse font-mono flex items-center gap-1">
                <Activity className="w-3 h-3 animate-spin" /> Fikr oqimi
              </span>
            </div>
            <div className="text-zinc-400 font-mono text-[11px] leading-relaxed max-h-48 overflow-y-auto whitespace-pre-wrap bg-[#080a10] p-2.5 rounded border border-[#1a1f2e]">
              {message.thinking}
            </div>
          </div>
        ) : message.thinking ? (
          /* Finished Thinking Accordion */
          <div className="rounded border border-[#202738] bg-[#0f131c] overflow-hidden text-xs">
            <div
              onClick={() => setShowThinking(!showThinking)}
              className="px-2.5 py-1.5 flex items-center justify-between cursor-pointer hover:bg-[#151a26] transition text-zinc-400 select-none"
            >
              <div className="flex items-center gap-1.5 text-[11px]">
                <Brain className="w-3.5 h-3.5 text-zinc-400" />
                <span>Model fikrlash jarayoni (Thinking)</span>
              </div>
              {showThinking ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
            </div>
            {showThinking && (
              <div className="p-3 border-t border-[#1e2434] bg-[#0a0d14] text-zinc-400 font-mono text-[11px] whitespace-pre-wrap leading-relaxed max-h-60 overflow-y-auto">
                {message.thinking}
              </div>
            )}
          </div>
        ) : null}

        {/* Tool Call Cards */}
        {message.toolCalls && message.toolCalls.length > 0 && (
          <div className="space-y-1.5 pt-1">
            {message.toolCalls.map((tc, idx) => (
              <ToolCallCard key={tc.id || idx} toolCall={tc} />
            ))}
          </div>
        )}

        {/* Message content */}
        {message.content ? (
          <MarkdownRenderer content={message.content} />
        ) : !message.thinking && (!message.toolCalls || message.toolCalls.length === 0) ? (
          <div className="flex items-center gap-2.5 py-2.5 px-3.5 rounded-lg bg-[#0e121d] border border-blue-900/40 text-xs text-blue-300 font-mono">
            <Loader2 className="w-3.5 h-3.5 animate-spin text-blue-400 shrink-0" />
            <span className="animate-pulse">Ilmiy tadqiqot boshlanmoqda (ma'lumotlar tahlili va qidiruv)...</span>
          </div>
        ) : null}
      </div>
    </div>
  );
};
