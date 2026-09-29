"use client";

import React from "react";
import { ChatSession } from "@/types";
import { Plus, X, MessageSquare } from "lucide-react";

interface ChatTabsProps {
  sessions: ChatSession[];
  activeSessionId: string;
  onSelectSession: (id: string) => void;
  onCreateSession: () => void;
  onDeleteSession: (id: string) => void;
}

export const ChatTabs: React.FC<ChatTabsProps> = ({
  sessions,
  activeSessionId,
  onSelectSession,
  onCreateSession,
  onDeleteSession,
}) => {
  return (
    <div className="h-9 border-b border-[#1e2434] bg-[#0b0d13] px-3 flex items-center gap-1 overflow-x-auto select-none scrollbar-none text-xs">
      {sessions.map((s) => {
        const isActive = s.id === activeSessionId;
        return (
          <div
            key={s.id}
            onClick={() => onSelectSession(s.id)}
            className={`h-7 px-2.5 rounded text-xs font-medium flex items-center gap-1.5 cursor-pointer transition shrink-0 group border ${
              isActive
                ? "bg-[#161c28] border-[#2b364e] text-zinc-100"
                : "bg-transparent border-transparent text-zinc-400 hover:bg-[#121622] hover:text-zinc-200"
            }`}
          >
            {s.is_running ? (
              <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse"></span>
            ) : (
              <MessageSquare
                className={`w-3 h-3 ${isActive ? "text-blue-400" : "text-zinc-500"}`}
              />
            )}

            <span className="max-w-[140px] truncate">{s.name}</span>

            {s.id !== "default" && (
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  onDeleteSession(s.id);
                }}
                className="opacity-0 group-hover:opacity-100 hover:text-red-400 p-0.5 rounded transition ml-0.5"
              >
                <X className="w-3 h-3" />
              </button>
            )}
          </div>
        );
      })}

      {/* New Chat Button */}
      <button
        type="button"
        onClick={onCreateSession}
        title="Yangi parallel chat"
        className="h-7 px-2 rounded text-zinc-400 hover:text-zinc-200 hover:bg-[#141824] border border-transparent hover:border-[#222838] flex items-center gap-1 text-xs transition shrink-0 ml-1"
      >
        <Plus className="w-3 h-3" />
        <span>Chat</span>
      </button>
    </div>
  );
};
