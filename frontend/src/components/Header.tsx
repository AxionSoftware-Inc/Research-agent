"use client";

import React from "react";
import { ServerStatus } from "@/types";
import {
  Bot,
  RotateCcw,
  Trash2,
  Sliders,
  Square,
  AlertCircle,
  Gauge,
  Coins,
  HardDrive,
} from "lucide-react";


interface HeaderProps {
  status: ServerStatus | null;
  onUndo: () => void;
  onClear: () => void;
  onOpenSettings: () => void;
  onCancelTask: () => void;
  onUnloadVram?: () => void;
  isStreaming: boolean;
  activeMode?: string;
}

export const Header: React.FC<HeaderProps> = ({
  status,
  onUndo,
  onClear,
  onOpenSettings,
  onCancelTask,
  onUnloadVram,
  isStreaming,
  activeMode,
}) => {
  const tokenUsed = status?.token_estimate || 0;
  const tokenMax = status?.token_max || 262144;
  const percent = status?.token_percent || Math.round((tokenUsed / tokenMax) * 100);

  const meterColor =
    percent > 80
      ? "bg-red-500 text-red-400"
      : percent > 50
      ? "bg-amber-400 text-amber-300"
      : "bg-blue-500 text-blue-400";

  return (
    <header className="h-13 border-b border-[#1e2434] bg-[#0c0e14] px-4 flex items-center justify-between sticky top-0 z-30 select-none text-xs">
      {/* Brand & Connection */}
      <div className="flex items-center gap-2.5">
        <div className="w-7 h-7 rounded border border-[#263148] bg-[#141a26] flex items-center justify-center text-blue-400">
          <Bot className="w-4 h-4" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span className="font-semibold text-xs text-zinc-100">AI Researcher</span>
            <span className="text-[10px] uppercase font-mono px-1.5 py-0.2 rounded bg-indigo-950/60 text-indigo-300 border border-indigo-700/40">
              Deep Research Lab
            </span>
            {activeMode && (
              <span className="hidden sm:inline-flex items-center gap-1 text-[10px] font-mono px-2 py-0.2 rounded bg-cyan-950/60 text-cyan-300 border border-cyan-700/50">
                <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse"></span>
                {activeMode}
              </span>
            )}
          </div>
          <div className="flex items-center gap-1.5 text-[11px] text-zinc-400">
            {status?.status === "online" ? (
              <span className="flex items-center gap-1 text-emerald-400">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                Online
              </span>
            ) : (
              <span className="flex items-center gap-1 text-amber-400">
                <AlertCircle className="w-3 h-3" />
                Connecting...
              </span>
            )}
            <span className="text-zinc-600">•</span>
            <span className="text-zinc-400 truncate max-w-[220px]" title={status?.workspace}>
              {status?.workspace ? status.workspace.split("\\").pop() : "Workspace"}
            </span>
          </div>
        </div>
      </div>

      {/* Real-time Context Window Meter */}
      <div className="hidden md:flex items-center gap-2 px-3 py-1 rounded border border-[#1e2434] bg-[#10141d]">
        <Gauge className="w-3.5 h-3.5 text-zinc-400" />
        <div className="flex flex-col gap-0.5 w-32">
          <div className="flex items-center justify-between text-[10px] font-mono">
            <span className="text-zinc-400">Kontekst:</span>
            <span className={`font-semibold ${meterColor.split(" ")[1]}`}>{percent}%</span>
          </div>
          <div className="w-full bg-[#1b212f] h-1 rounded overflow-hidden">
            <div
              className={`h-full transition-all duration-300 ${meterColor.split(" ")[0]}`}
              style={{ width: `${Math.min(100, Math.max(2, percent))}%` }}
            ></div>
          </div>
        </div>
        <span className="text-[10px] font-mono text-zinc-400">
          {tokenUsed.toLocaleString()} / {(tokenMax / 1000).toFixed(0)}k
        </span>
      </div>

      {/* Real-time Financial Cost Tracker */}
      <div className="hidden lg:flex items-center gap-2 px-2.5 py-1 rounded border border-[#1e2434] bg-[#10141d] text-[11px]">
        <Coins className="w-3.5 h-3.5 text-blue-400" />
        <div className="flex items-center gap-1.5 font-mono">
          {status?.model_pricing?.is_local ? (
            <span className="text-emerald-400 font-medium">Local ($0.00)</span>
          ) : (
            <div className="flex items-center gap-1">
              <span className="text-zinc-400">Xarajat:</span>
              <span className="text-zinc-100 font-semibold">
                ${status?.total_cost_usd !== undefined ? status.total_cost_usd.toFixed(4) : "0.0000"}
              </span>
            </div>
          )}
          {status?.model_pricing && !status.model_pricing.is_local && (
            <span className="text-[10px] text-zinc-500">
              (${status.model_pricing.input_cost_per_1m}/${status.model_pricing.output_cost_per_1m} 1M)
            </span>
          )}
        </div>
      </div>

      {/* Real-time VRAM Live Monitor & Quick Purge */}
      {status?.vram && status.vram.online && (
        <div className="hidden xl:flex items-center gap-2 px-2.5 py-1 rounded border border-[#1e2434] bg-[#10141d] text-[11px]">
          <HardDrive className="w-3.5 h-3.5 text-indigo-400" />
          <div className="flex items-center gap-1.5 font-mono">
            <span className="text-zinc-400">VRAM:</span>
            {status.vram.count > 0 ? (
              <span
                className="text-emerald-400 font-medium flex items-center gap-1"
                title={status.vram.models.map((m) => `${m.name}: ${m.size_vram_gb} GB`).join(", ")}
              >
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                {status.vram.total_vram_gb} GB ({status.vram.models[0]?.name?.split(":")[0]})
              </span>
            ) : (
              <span className="text-zinc-500 font-medium flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-zinc-600"></span>
                0 GB (Bo'sh)
              </span>
            )}
          </div>
          {status.vram.count > 0 && onUnloadVram && (
            <button
              onClick={onUnloadVram}
              title="VRAMni butunlay bo'shatish (Purge VRAM)"
              className="text-[10px] text-zinc-400 hover:text-amber-300 ml-1 px-1 py-0.2 rounded hover:bg-[#1a2232] transition border border-transparent hover:border-[#2a344c]"
            >
              Bo'shatish
            </button>
          )}
        </div>
      )}

      {/* Actions & Controls */}
      <div className="flex items-center gap-1.5">
        {/* Stop Task Button */}
        {isStreaming && (
          <button
            onClick={onCancelTask}
            title="Vazifani to'xtatish"
            className="flex items-center gap-1 px-2.5 py-1 text-xs rounded border border-red-500/40 bg-red-500/10 hover:bg-red-500/20 text-red-300 transition"
          >
            <Square className="w-3 h-3 fill-current" />
            <span>To'xtatish</span>
          </button>
        )}

        {/* Quick Undo button */}
        <button
          onClick={onUndo}
          disabled={isStreaming || (status?.checkpoints_count || 0) === 0}
          title="Oxirgi fayl o'zgarishini bekor qilish (Undo)"
          className="flex items-center gap-1 px-2 py-1 text-xs rounded border border-[#2a344a] bg-[#121622] hover:bg-[#1a2030] text-zinc-300 transition disabled:opacity-30 disabled:cursor-not-allowed"
        >
          <RotateCcw className="w-3.5 h-3.5 text-amber-400" />
          <span>Undo ({status?.checkpoints_count || 0})</span>
        </button>

        {/* Clear chat */}
        <button
          onClick={onClear}
          title="Chatni tozalash"
          className="p-1.5 text-zinc-400 hover:text-zinc-100 rounded hover:bg-[#161a26] border border-transparent hover:border-[#222838] transition"
        >
          <Trash2 className="w-3.5 h-3.5" />
        </button>

        {/* Settings button */}
        <button
          onClick={onOpenSettings}
          title="Tizim sozlamalari"
          className="flex items-center gap-1 px-2.5 py-1 text-xs rounded border border-[#2a344a] bg-[#141824] hover:bg-[#1d2334] text-zinc-200 transition"
        >
          <Sliders className="w-3.5 h-3.5 text-blue-400" />
          <span>Sozlamalar</span>
        </button>
      </div>
    </header>
  );
};
