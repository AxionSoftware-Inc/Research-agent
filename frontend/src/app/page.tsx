"use client";

import React, { useEffect, useRef, useState } from "react";
import { Header } from "@/components/Header";
import { Sidebar } from "@/components/Sidebar";
import { MessageItem } from "@/components/MessageItem";
import { FileViewerDrawer } from "@/components/FileViewerDrawer";
import { ChatTabs } from "@/components/ChatTabs";
import { SettingsModal } from "@/components/SettingsModal";
import {
  Attachment,
  ChatSession,
  CheckpointItem,
  FileNode,
  Message,
  PlanData,
  Project,
  ServerStatus,
  ToolCall,
} from "@/types";

import {
  Send,
  Sparkles,
  Terminal,
  RotateCcw,
  Paperclip,
  Image as ImageIcon,
  FileText,
  X,
  Cpu,
  Square,
  Bot,
  HardDrive,
  Globe,
  BookOpen,
  Bookmark,
} from "lucide-react";

const BACKEND_URL = "http://127.0.0.1:8765";

export default function Home() {
  // Projects state
  const [projects, setProjects] = useState<Project[]>([
    {
      id: "proj_default",
      name: "Researcher",
      path: "D:\\Researcher",
      created_at: Date.now(),
      is_active: true,
      chat_count: 1,
    },
  ]);
  const [activeProjectId, setActiveProjectId] = useState<string>("proj_default");

  // Sessions & Tabs state
  const [sessions, setSessions] = useState<ChatSession[]>([
    {
      id: "default",
      name: "General Task",
      model: "gemma4-26b:latest",
      project_id: "proj_default",
      is_running: false,
      tokens: 0,
      created_at: Date.now(),
    },
  ]);
  const [activeSessionId, setActiveSessionId] = useState<string>("default");

  // Per-session message storage mapping: session_id -> Message[]
  const [sessionMessages, setSessionMessages] = useState<Record<string, Message[]>>({
    default: [],
  });


  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [attachments, setAttachments] = useState<Attachment[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [status, setStatus] = useState<ServerStatus | null>(null);
  const [files, setFiles] = useState<FileNode[]>([]);
  const [checkpoints, setCheckpoints] = useState<CheckpointItem[]>([]);
  const [plan, setPlan] = useState<PlanData | null>(null);
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [vramNotice, setVramNotice] = useState<string | null>(null);
  const [activeMode, setActiveMode] = useState<string>("Avtonom Tadqiqotchi");

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const activeMessages = sessionMessages[activeSessionId] || [];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [activeMessages]);

  // Fetch status, sessions, files, checkpoints, plan, and projects
  const refreshData = async () => {
    try {
      const [resStatus, resSessions, resFiles, resCheckpoints, resPlan, resProjects] = await Promise.all([
        fetch(`${BACKEND_URL}/api/status?session_id=${activeSessionId}`).then((r) => r.json()),
        fetch(`${BACKEND_URL}/api/sessions`).then((r) => r.json()),
        fetch(`${BACKEND_URL}/api/files`).then((r) => r.json()),
        fetch(`${BACKEND_URL}/api/checkpoints`).then((r) => r.json()),
        fetch(`${BACKEND_URL}/api/plan?session_id=${activeSessionId}`).then((r) => r.json()),
        fetch(`${BACKEND_URL}/api/projects`).then((r) => r.json()).catch(() => ({ projects: [] })),
      ]);

      setStatus(resStatus);
      if (resSessions.sessions && resSessions.sessions.length > 0) {
        setSessions(resSessions.sessions);
      }
      setFiles(resFiles.files || []);
      setCheckpoints(resCheckpoints.checkpoints || []);
      setPlan(resPlan || null);

      if (resProjects?.projects && resProjects.projects.length > 0) {
        setProjects(resProjects.projects);
        if (resProjects.active_project_id) {
          setActiveProjectId(resProjects.active_project_id);
        }
      }
    } catch {
      // Backend starting up
    }
  };

  useEffect(() => {
    refreshData();
    const interval = setInterval(refreshData, 4000);
    return () => clearInterval(interval);
  }, [activeSessionId]);

  // Project Handlers
  const handleSelectProject = async (projId: string) => {
    setActiveProjectId(projId);
    try {
      await fetch(`${BACKEND_URL}/api/projects/${projId}/activate`, { method: "POST" });
      refreshData();
    } catch (e) {
      console.error(e);
    }
  };

  const handleCreateProject = async (name: string, path?: string) => {
    try {
      const res = await fetch(`${BACKEND_URL}/api/projects`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, path }),
      });
      const data = await res.json();
      if (data.status === "success") {
        setActiveProjectId(data.project.id);
        if (data.initial_session) {
          setActiveSessionId(data.initial_session.id);
          setSessionMessages((prev) => ({
            ...prev,
            [data.initial_session.id]: [],
          }));
        }
        refreshData();
      }
    } catch (e: any) {
      alert(`Loyiha yaratishda xatolik: ${e.message}`);
    }
  };

  const handleDeleteProject = async (projId: string) => {
    try {
      await fetch(`${BACKEND_URL}/api/projects/${projId}`, { method: "DELETE" });
      refreshData();
    } catch (e) {
      console.error(e);
    }
  };

  // Session Handlers
  const handleCreateSession = async (projectId?: string) => {
    const targetProjId = projectId || activeProjectId;
    const projectSessions = sessions.filter(
      (s) => (s.project_id || "proj_default") === targetProjId
    );
    const chatNumber = projectSessions.length + 1;
    const name = `Chat #${chatNumber}`;
    try {
      const res = await fetch(`${BACKEND_URL}/api/sessions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, project_id: targetProjId }),
      });
      const data = await res.json();
      const newSession = data.session;

      setSessions((prev) => [...prev, newSession]);
      setSessionMessages((prev) => ({
        ...prev,
        [newSession.id]: [],
      }));
      setActiveSessionId(newSession.id);

      setActiveProjectId(targetProjId);
      refreshData();
    } catch (e: any) {
      alert(`Chat sessiyasi yaratishda xatolik: ${e.message}`);
    }
  };


  const handleDeleteSession = async (id: string) => {
    if (id === "default") return;
    try {
      await fetch(`${BACKEND_URL}/api/sessions/${id}`, { method: "DELETE" });
      setSessions((prev) => prev.filter((s) => s.id !== id));
      setSessionMessages((prev) => {
        const copy = { ...prev };
        delete copy[id];
        return copy;
      });
      if (activeSessionId === id) {
        setActiveSessionId("default");
      }
      refreshData();
    } catch (e: any) {
      alert(`Failed to delete session: ${e.message}`);
    }
  };

  const handleSelectModel = async (model: string) => {
    try {
      setVramNotice(`VRAM almashtirilmoqda: '${model}' xotiraga yuklanmoqda...`);
      const formData = new FormData();
      formData.append("model", model);
      formData.append("session_id", activeSessionId);
      await fetch(`${BACKEND_URL}/api/model/select`, {
        method: "POST",
        body: formData,
      });
      setSessions((prev) =>
        prev.map((s) => (s.id === activeSessionId ? { ...s, model } : s))
      );
      setStatus((prev) => (prev ? { ...prev, current_model: model } : prev));
      setTimeout(() => {
        setVramNotice(null);
        refreshData();
      }, 1500);
    } catch (e) {
      console.error(e);
      setVramNotice(null);
    }
  };

  const handleUnloadVram = async () => {
    try {
      setVramNotice("VRAM tozalanmoqda: Barcha modellar xotiradan chiqarilmoqda...");
      await fetch(`${BACKEND_URL}/api/vram/unload`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });
      setTimeout(() => {
        setVramNotice(null);
        refreshData();
      }, 1200);
    } catch (e) {
      console.error("VRAM unload error:", e);
      setVramNotice(null);
    }
  };

  // Stop / Cancel running task
  const handleCancelTask = async () => {
    try {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      await fetch(`${BACKEND_URL}/api/sessions/${activeSessionId}/cancel`, {
        method: "POST",
      });
      setIsStreaming(false);
      refreshData();
    } catch (e: any) {
      console.error("Cancel failed:", e);
    }
  };

  // File & Image Upload
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    setIsUploading(true);
    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      const formData = new FormData();
      formData.append("file", file);

      try {
        const res = await fetch(`${BACKEND_URL}/api/upload`, {
          method: "POST",
          body: formData,
        });
        const data = await res.json();
        if (data.status === "success") {
          setAttachments((prev) => [
            ...prev,
            {
              file_name: data.file_name,
              path: data.path,
              is_image: data.is_image,
              size: data.size,
              preview_text: data.preview_text,
            },
          ]);
        }
      } catch (err: any) {
        alert(`Upload failed for ${file.name}: ${err.message}`);
      }
    }
    setIsUploading(false);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const handleRemoveAttachment = (path: string) => {
    setAttachments((prev) => prev.filter((a) => a.path !== path));
  };

  // Drag and Drop
  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    const droppedFiles = e.dataTransfer.files;
    if (!droppedFiles || droppedFiles.length === 0) return;

    setIsUploading(true);
    for (let i = 0; i < droppedFiles.length; i++) {
      const file = droppedFiles[i];
      const formData = new FormData();
      formData.append("file", file);

      try {
        const res = await fetch(`${BACKEND_URL}/api/upload`, {
          method: "POST",
          body: formData,
        });
        const data = await res.json();
        if (data.status === "success") {
          setAttachments((prev) => [
            ...prev,
            {
              file_name: data.file_name,
              path: data.path,
              is_image: data.is_image,
              size: data.size,
              preview_text: data.preview_text,
            },
          ]);
        }
      } catch (err: any) {
        console.error(err);
      }
    }
    setIsUploading(false);
  };

  const handleUndo = async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/api/undo`, { method: "POST" });
      const data = await res.json();
      setSessionMessages((prev) => ({
        ...prev,
        [activeSessionId]: [
          ...(prev[activeSessionId] || []),
          {
            id: `undo_${Date.now()}`,
            role: "assistant",
            content: `⏪ **Rollback Natijasi:**\n${data.message}`,
            timestamp: Date.now(),
          },
        ],
      }));
      refreshData();
    } catch (e: any) {
      alert(`Undo failed: ${e.message}`);
    }
  };

  const handleClear = async () => {
    try {
      await fetch(`${BACKEND_URL}/api/clear?session_id=${activeSessionId}`, { method: "POST" });
      setSessionMessages((prev) => ({
        ...prev,
        [activeSessionId]: [
          {
            id: `reset_${Date.now()}`,
            role: "assistant",
            content: "✓ Kontekst va suhbat xotirasi tozalandi. Yangi vazifani boshlashimiz mumkin!",
            timestamp: Date.now(),
          },
        ],
      }));
      refreshData();
    } catch (e: any) {
      console.error(e);
    }
  };

  const handleSubmit = async (overridePrompt?: string) => {
    const promptToSend = (overridePrompt || input).trim();
    if ((!promptToSend && attachments.length === 0) || isStreaming) return;

    if (promptToSend === "/undo") {
      setInput("");
      handleUndo();
      return;
    }
    if (promptToSend === "/clear") {
      setInput("");
      handleClear();
      return;
    }

    const currentAttachments = [...attachments];
    setAttachments([]);

    const activeSession = sessions.find((s) => s.id === activeSessionId);
    const targetModel = activeSession?.model || status?.current_model || "gemma4-26b:latest";

    const userMsg: Message = {
      id: `usr_${Date.now()}`,
      role: "user",
      content: promptToSend,
      attachments: currentAttachments,
      timestamp: Date.now(),
    };

    const assistantMsgId = `asst_${Date.now()}`;
    const assistantMsg: Message = {
      id: assistantMsgId,
      role: "assistant",
      content: "",
      toolCalls: [],
      timestamp: Date.now(),
    };

    setSessionMessages((prev) => ({
      ...prev,
      [activeSessionId]: [...(prev[activeSessionId] || []), userMsg, assistantMsg],
    }));

    setInput("");
    setIsStreaming(true);

    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    try {
      const response = await fetch(`${BACKEND_URL}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: activeSessionId,
          prompt: promptToSend,
          model: targetModel,
          attachments: currentAttachments.map((a) => a.path),
        }),
        signal: abortController.signal,
      });

      if (!response.body) throw new Error("No response body from server");

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n\n");
        buffer = lines.pop() || "";

        for (const block of lines) {
          const match = block.match(/data: (.*)/);
          if (!match) continue;

          try {
            const eventData = JSON.parse(match[1]);
            const eventType = eventData.type;

            if (eventType === "vram_status") {
              setVramNotice(eventData.text);
              continue;
            }

            if (eventType === "vram_ready") {
              setVramNotice(null);
              refreshData();
              continue;
            }

            if (eventType === "mode_status") {
              setActiveMode(eventData.mode || "Avtonom Tadqiqotchi");
              continue;
            }

            // Once content or thinking arrives, clear vram notice
            if (eventType === "thinking_chunk" || eventType === "content_chunk") {
              setVramNotice(null);
            }

            setSessionMessages((prev) => {
              const currentList = prev[activeSessionId] || [];
              const updatedList = currentList.map((msg) => {
                if (msg.id !== assistantMsgId) return msg;

                if (eventType === "progress") {
                  return {
                    ...msg,
                    progress: eventData.text,
                  };
                }

                if (eventType === "thinking_chunk" || eventType === "thinking") {
                  return {
                    ...msg,
                    thinking: (msg.thinking || "") + eventData.data,
                    progress: msg.progress || "🧠 Model ilmiy mulohaza yuritmoqda (Thinking)...",
                  };
                }

                if (eventType === "content_chunk") {
                  return {
                    ...msg,
                    content: (msg.content || "") + eventData.data,
                    progress: undefined,
                  };
                }

                if (eventType === "tool_call") {
                  const existing = msg.toolCalls || [];
                  const newToolCall: ToolCall = {
                    name: eventData.name,
                    args: eventData.args,
                    status: "running",
                  };
                  return {
                    ...msg,
                    progress: `⚙️ '${eventData.name}' bajarilmoqda...`,
                    toolCalls: [...existing, newToolCall],
                  };
                }

                if (eventType === "tool_result") {
                  const existing = [...(msg.toolCalls || [])];
                  const last = existing.find(
                    (t) => t.name === eventData.name && t.status === "running"
                  );
                  if (last) {
                    last.status = "done";
                    last.result = eventData.result;
                  }
                  return {
                    ...msg,
                    progress: `✓ '${eventData.name}' yakunlandi. Natijalar qayta ishlanmoqda...`,
                    toolCalls: existing,
                  };
                }

                if (eventType === "message" || eventType === "done") {
                  return {
                    ...msg,
                    content: eventType === "message" ? eventData.data : msg.content,
                    progress: undefined,
                  };
                }

                return msg;
              });

              return { ...prev, [activeSessionId]: updatedList };
            });

            if (eventType === "cost_update") {
              const cData = eventData.data || eventData;
              setStatus((prev) =>
                prev
                  ? {
                      ...prev,
                      total_cost_usd: cData.total_cost_usd,
                      total_input_tokens: cData.total_input_tokens,
                      total_output_tokens: cData.total_output_tokens,
                    }
                  : prev
              );
            }
          } catch {
            // Chunk parse ignore
          }

        }
      }
    } catch (err: any) {
      if (err.name !== "AbortError") {
        setSessionMessages((prev) => ({
          ...prev,
          [activeSessionId]: (prev[activeSessionId] || []).map((m) =>
            m.id === assistantMsgId
              ? { ...m, content: `⚠️ Error executing request: ${err.message}` }
              : m
          ),
        }));
      }
    } finally {
      setIsStreaming(false);
      setVramNotice(null);
      refreshData();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="flex h-screen flex-col bg-[#080a0f] text-zinc-100 font-sans overflow-hidden">
      {/* Top Header */}
      <Header
        status={status}
        onUndo={handleUndo}
        onClear={handleClear}
        onOpenSettings={() => setIsSettingsOpen(true)}
        onCancelTask={handleCancelTask}
        onUnloadVram={handleUnloadVram}
        isStreaming={isStreaming}
        activeMode={activeMode}
      />

      {/* Main Body */}
      <div className="flex flex-1 overflow-hidden relative">
        {/* Left Sidebar */}
        <Sidebar
          projects={projects}
          activeProjectId={activeProjectId}
          onSelectProject={handleSelectProject}
          onCreateProject={handleCreateProject}
          onDeleteProject={handleDeleteProject}
          sessions={sessions}
          activeSessionId={activeSessionId}
          onSelectSession={(id) => setActiveSessionId(id)}
          onCreateSession={(projId) => handleCreateSession(projId)}
          onDeleteSession={handleDeleteSession}
          checkpoints={checkpoints}
          plan={plan}
          onUndo={handleUndo}
          onRefreshData={refreshData}
          onSelectFile={(f) => setSelectedFile(f)}
        />


        {/* Center Chat View */}
        <main className="flex-1 flex flex-col h-full bg-[#080a0f] overflow-hidden">
          {/* Multi-Chat Session Tabs */}
          <ChatTabs
            sessions={sessions}
            activeSessionId={activeSessionId}
            onSelectSession={(id) => setActiveSessionId(id)}
            onCreateSession={handleCreateSession}
            onDeleteSession={handleDeleteSession}
          />

          {/* Messages Scroll Area (Visible when chat has messages) */}
          {activeMessages.length > 0 && (
            <div className="flex-1 overflow-y-auto divide-y divide-[#171b26]/60">
              {activeMessages.map((msg) => (
                <MessageItem key={msg.id} message={msg} />
              ))}
              <div ref={messagesEndRef} />
            </div>
          )}

          {/* Quick Action Chips & Input Area (Centered when empty, docked when active) */}
          <div
            onDragOver={(e) => e.preventDefault()}
            onDrop={handleDrop}
            className={`transition-all duration-300 ease-out flex flex-col justify-center ${
              activeMessages.length === 0
                ? "flex-1 items-center px-4 pb-12"
                : "p-3 border-t border-[#1e2434] bg-[#0c0e14]"
            }`}
          >
            <div
              className={`w-full transition-all duration-300 ease-out space-y-2.5 ${
                activeMessages.length === 0 ? "max-w-2xl mx-auto" : "max-w-4xl mx-auto"
              }`}
            >
              {/* Real-time VRAM Swapping / Loading Banner */}
              {vramNotice && (
                <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-blue-950/70 border border-blue-500/40 text-xs text-blue-200 shadow-md backdrop-blur-xs animate-pulse">
                  <HardDrive className="w-3.5 h-3.5 text-blue-400 shrink-0" />
                  <span className="font-mono text-[11px]">{vramNotice}</span>
                </div>
              )}

              {/* Hero Banner when chat is empty */}
              {activeMessages.length === 0 && (
                <div className="text-center space-y-1.5 mb-5 select-none">
                  <div className="w-10 h-10 rounded-lg border border-indigo-700/40 bg-indigo-950/40 flex items-center justify-center text-indigo-400 mx-auto mb-2.5 shadow-xs">
                    <BookOpen className="w-5 h-5" />
                  </div>
                  <h1 className="text-base font-semibold text-zinc-100 tracking-tight">
                    Qanday ilmiy tadqiqot olib boramiz?
                  </h1>
                  <p className="text-xs text-zinc-400 max-w-md mx-auto">
                    arXiv va internet qidiruvi, ilmiy maqolalar tahlili, adabiyotlar sharhi (Literature Review) yoki LaTeX maqola tayyorlash.
                  </p>
                </div>
              )}

              {/* Attachment preview pills */}
              {attachments.length > 0 && (
                <div className="flex flex-wrap gap-1.5 pb-1">
                  {attachments.map((att) => (
                    <div
                      key={att.path}
                      className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-[#141926] border border-[#243048] text-xs text-zinc-200"
                    >
                      {att.is_image ? (
                        <ImageIcon className="w-3 h-3 text-blue-400" />
                      ) : (
                        <FileText className="w-3 h-3 text-amber-400" />
                      )}
                      <span className="truncate max-w-[150px]">{att.file_name}</span>
                      <button
                        onClick={() => handleRemoveAttachment(att.path)}
                        className="hover:text-red-400 ml-1 transition"
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </div>
                  ))}
                </div>
              )}

              {/* Action Chips */}
              <div className="flex items-center gap-1.5 overflow-x-auto pb-0.5 text-xs text-zinc-400 select-none">
                <span className="text-[10px] text-zinc-500 uppercase tracking-wider font-medium mr-1">
                  Tezkor:
                </span>
                <button
                  onClick={() =>
                    handleSubmit("run_deep_research vositasi orqali 'Multimodal Foundation Models in Healthcare' mavzusida to'liq ilmiy adabiyotlar tahlili o'tkaz, LaTeX va Word maqola yarat")
                  }
                  className="px-2 py-0.5 rounded bg-fuchsia-950/40 hover:bg-fuchsia-900/50 text-fuchsia-300 border border-fuchsia-700/50 flex items-center gap-1 transition"
                >
                  <Sparkles className="w-3 h-3 text-fuchsia-400" />
                  <span>🚀 Deep Research (Avtonom)</span>
                </button>
                <button
                  onClick={() =>
                    handleSubmit("search_crossref va search_arxiv vositalari orqali 'Self-Healing AI Agents' bo'yicha eng nufuzli maqolalarni qidir")
                  }
                  className="px-2 py-0.5 rounded bg-[#131722] hover:bg-[#1a2030] text-zinc-300 border border-[#202738] flex items-center gap-1 transition"
                >
                  <Globe className="w-3 h-3 text-orange-400" />
                  <span>CrossRef & arXiv</span>
                </button>
                <button
                  onClick={() =>
                    handleSubmit("search_europepmc vositasi orqali 'Cancer Immunotherapy AI' bo'yicha PubMed tibbiy maqolalarini qidir")
                  }
                  className="px-2 py-0.5 rounded bg-[#131722] hover:bg-[#1a2030] text-zinc-300 border border-[#202738] flex items-center gap-1 transition"
                >
                  <BookOpen className="w-3 h-3 text-teal-400" />
                  <span>PubMed (Tibbiyot)</span>
                </button>
                <button
                  onClick={() =>
                    handleSubmit("references.bib faylidagi barcha iqtiboslar ro'yxatini ko'rsat")
                  }
                  className="px-2 py-0.5 rounded bg-[#131722] hover:bg-[#1a2030] text-zinc-300 border border-[#202738] flex items-center gap-1 transition"
                >
                  <Bookmark className="w-3 h-3 text-emerald-400" />
                  <span>BibTeX</span>
                </button>
                <button
                  onClick={() =>
                    handleSubmit("research_paper.tex faylini Tectonic orqali tekshir va PDF ga kompilyatsiya qil")
                  }
                  className="px-2 py-0.5 rounded bg-[#131722] hover:bg-[#1a2030] text-zinc-300 border border-[#202738] flex items-center gap-1 transition"
                >
                  <Sparkles className="w-3 h-3 text-purple-400" />
                  <span>LaTeX PDF</span>
                </button>
                <button
                  onClick={handleUndo}
                  className="px-2 py-0.5 rounded bg-amber-500/10 hover:bg-amber-500/20 text-amber-300 border border-amber-500/30 flex items-center gap-1 transition"
                >
                  <RotateCcw className="w-3 h-3" />
                  <span>Undo</span>
                </button>
              </div>

              {/* Text Input Box */}
              <div className="relative rounded-lg border border-[#23293a] bg-[#10141d] focus-within:border-indigo-500 transition">
                <textarea
                  ref={textareaRef}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Tadqiqot mavzusi, ilmiy savolni kiriting yoki PDF maqola yuklang..."
                  rows={2}
                  disabled={isStreaming}
                  className="w-full bg-transparent px-3 py-2 text-xs text-zinc-200 placeholder-zinc-500 focus:outline-none resize-none font-sans"
                />

                {/* Bottom Bar inside input */}
                <div className="flex items-center justify-between px-2.5 pb-2 pt-1 border-t border-[#1b2130] text-[11px] text-zinc-400">
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => fileInputRef.current?.click()}
                      disabled={isStreaming || isUploading}
                      title="Fayl yoki rasm biriktirish"
                      className="p-1 rounded hover:bg-[#181e2b] text-zinc-400 hover:text-zinc-200 transition flex items-center gap-1"
                    >
                      <Paperclip className="w-3.5 h-3.5" />
                      <span className="hidden sm:inline text-xs">Biriktirish</span>
                    </button>
                    <input
                      ref={fileInputRef}
                      type="file"
                      multiple
                      className="hidden"
                      onChange={handleFileUpload}
                    />

                    {/* Model selector directly under chat */}
                    <div className="flex items-center gap-1 px-2 py-0.5 rounded bg-[#141824] border border-[#222838] text-zinc-300">
                      <Cpu className="w-3 h-3 text-blue-400" />
                      <select
                        value={sessions.find((s) => s.id === activeSessionId)?.model || status?.current_model || "gemma4-26b:latest"}
                        onChange={(e) => handleSelectModel(e.target.value)}
                        disabled={isStreaming}
                        className="bg-transparent border-none outline-none text-zinc-300 cursor-pointer text-[11px] font-mono"
                      >
                        {status?.models_detailed && status.models_detailed.length > 0 ? (
                          status.models_detailed.map((m, idx) => (
                            <option key={`${m.id}_${idx}`} value={m.model_name} className="bg-[#141824] text-white">
                              {m.name || m.model_name} {m.is_local ? "(Local)" : `($${m.input_cost_per_1m}/$${m.output_cost_per_1m})`}
                            </option>
                          ))
                        ) : status?.available_models && status.available_models.length > 0 ? (
                          status.available_models.map((m, idx) => (
                            <option key={`${m}_${idx}`} value={m} className="bg-[#141824] text-white">
                              {m}
                            </option>
                          ))
                        ) : (
                          <option value="gemma4-26b:latest" className="bg-[#141824] text-white">
                            gemma4-26b:latest
                          </option>
                        )}
                      </select>
                    </div>


                    {isUploading && (
                      <span className="text-blue-400 animate-pulse text-[10px]">Yuklanmoqda...</span>
                    )}
                  </div>

                  {/* Right: Send or Stop Task */}
                  <div className="flex items-center gap-2">
                    {isStreaming ? (
                      <button
                        onClick={handleCancelTask}
                        className="px-2.5 py-1 rounded bg-red-600 hover:bg-red-500 text-white font-medium flex items-center gap-1 text-xs transition"
                      >
                        <Square className="w-3 h-3 fill-current" />
                        <span>To'xtatish</span>
                      </button>
                    ) : (
                      <button
                        onClick={() => handleSubmit()}
                        disabled={!input.trim() && attachments.length === 0}
                        className="px-3 py-1 rounded bg-blue-600 hover:bg-blue-500 text-white font-medium flex items-center gap-1 text-xs transition disabled:opacity-30 disabled:cursor-not-allowed"
                      >
                        <span>Yuborish</span>
                        <Send className="w-3 h-3" />
                      </button>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </main>


        {/* Right Drawer: File Viewer */}
        <FileViewerDrawer
          filePath={selectedFile}
          onClose={() => setSelectedFile(null)}
          onSelectFile={(path) => setSelectedFile(path)}
        />
      </div>

      {/* Settings & Project Switcher Modal */}
      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        onSaved={refreshData}
        backendUrl={BACKEND_URL}
      />
    </div>
  );
}
