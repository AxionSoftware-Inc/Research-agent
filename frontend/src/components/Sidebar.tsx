"use client";

import React, { useEffect, useState } from "react";
import { ChatSession, CheckpointItem, PlanData, Project } from "@/types";
import {
  FolderKanban,
  RotateCcw,
  CheckCircle,
  Circle,
  ListOrdered,
  History,
  Brain,
  Plus,
  MessageSquare,
  X,
  Folder,
  FolderOpen,
  ChevronRight,
  ChevronDown,
  Trash2,
  Check,
  BookOpen,
  FileText,
  Bookmark,
  Download,
  Sparkles,
  RefreshCw,
} from "lucide-react";

interface SidebarProps {
  projects: Project[];
  activeProjectId: string;
  onSelectProject: (projectId: string) => void;
  onCreateProject: (name: string, path?: string) => Promise<void>;
  onDeleteProject?: (projectId: string) => Promise<void>;
  sessions: ChatSession[];
  activeSessionId: string;
  onSelectSession: (id: string) => void;
  onCreateSession: (projectId?: string) => void;
  onDeleteSession: (id: string) => void;
  checkpoints: CheckpointItem[];
  plan: PlanData | null;
  onUndo: () => void;
  onRefreshData: () => void;
  onSelectFile?: (filePath: string) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  projects,
  activeProjectId,
  onSelectProject,
  onCreateProject,
  onDeleteProject,
  sessions,
  activeSessionId,
  onSelectSession,
  onCreateSession,
  onDeleteSession,
  checkpoints,
  plan,
  onUndo,
  onRefreshData,
  onSelectFile,
}) => {
  const [activeTab, setActiveTab] = useState<"projects" | "plan" | "literature" | "checkpoints">("projects");
  const [expandedProjects, setExpandedProjects] = useState<Record<string, boolean>>({});
  const [isCreatingProject, setIsCreatingProject] = useState(false);
  const [newProjectName, setNewProjectName] = useState("");
  const [newProjectPath, setNewProjectPath] = useState("");
  const [literatureData, setLiteratureData] = useState<{ papers: any[]; references: any[]; latex_drafts: any[] }>({
    papers: [],
    references: [],
    latex_drafts: [],
  });
  const [copiedCitation, setCopiedCitation] = useState<string | null>(null);

  // Auto-expand active project
  useEffect(() => {
    if (activeProjectId) {
      setExpandedProjects((prev) => ({
        ...prev,
        [activeProjectId]: true,
      }));
    }
  }, [activeProjectId]);

  const toggleProjectExpand = (projId: string) => {
    setExpandedProjects((prev) => ({
      ...prev,
      [projId]: !prev[projId],
    }));
  };

  const handleCreateProjectSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newProjectName.trim()) return;
    await onCreateProject(newProjectName.trim(), newProjectPath.trim() || undefined);
    setNewProjectName("");
    setNewProjectPath("");
    setIsCreatingProject(false);
  };

  const fetchLiterature = () => {
    fetch("http://127.0.0.1:8765/api/literature")
      .then((r) => r.json())
      .then((d) => setLiteratureData(d))
      .catch(console.error);
  };

  useEffect(() => {
    if (activeTab === "literature") {
      fetchLiterature();
    }
  }, [activeTab]);

  return (
    <aside className="w-68 border-r border-[#1e2434] bg-[#0e1118] flex flex-col h-[calc(100vh-3.25rem)] shrink-0 select-none text-xs">
      {/* Top Tabs Navigation */}
      <div className="flex border-b border-[#1e2434] bg-[#0c0e14]">
        <button
          onClick={() => setActiveTab("projects")}
          className={`flex-1 py-2 font-medium flex items-center justify-center gap-1 transition text-[11px] ${
            activeTab === "projects"
              ? "text-indigo-400 border-b-2 border-indigo-500 bg-[#131722]"
              : "text-zinc-400 hover:text-zinc-200"
          }`}
          title="Tadqiqot loyihalari va chat sessiyalari"
        >
          <FolderKanban className="w-3.5 h-3.5" />
          <span>Tadqiqot</span>
        </button>
        <button
          onClick={() => setActiveTab("plan")}
          className={`flex-1 py-2 font-medium flex items-center justify-center gap-1 transition text-[11px] ${
            activeTab === "plan"
              ? "text-indigo-400 border-b-2 border-indigo-500 bg-[#131722]"
              : "text-zinc-400 hover:text-zinc-200"
          }`}
          title="Ilmiy protokol va milestone qadamlari"
        >
          <ListOrdered className="w-3.5 h-3.5" />
          <span>Protokol</span>
        </button>
        <button
          onClick={() => setActiveTab("literature")}
          className={`flex-1 py-2 font-medium flex items-center justify-center gap-1 transition text-[11px] ${
            activeTab === "literature"
              ? "text-indigo-400 border-b-2 border-indigo-500 bg-[#131722]"
              : "text-zinc-400 hover:text-zinc-200"
          }`}
          title="Yuklangan maqolalar, BibTeX iqtiboslar va LaTeX qoralamalar"
        >
          <BookOpen className="w-3.5 h-3.5" />
          <span>Adabiyot</span>
        </button>
        <button
          onClick={() => setActiveTab("checkpoints")}
          className={`flex-1 py-2 font-medium flex items-center justify-center gap-1 transition text-[11px] ${
            activeTab === "checkpoints"
              ? "text-indigo-400 border-b-2 border-indigo-500 bg-[#131722]"
              : "text-zinc-400 hover:text-zinc-200"
          }`}
          title="O'zgarishlar tarixi va qaytarish (Undo)"
        >
          <History className="w-3.5 h-3.5" />
          <span>Tarix</span>
        </button>
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-y-auto p-2">
        {/* PROJECTS TAB */}
        {activeTab === "projects" && (
          <div className="space-y-2">
            {/* Header: Action Bar */}
            <div className="flex items-center justify-between px-1.5 py-1 text-zinc-400">
              <span className="text-[10px] font-semibold tracking-wider uppercase text-zinc-400">
                Workspaces ({projects.length})
              </span>
              <div className="flex items-center gap-1">
                <button
                  onClick={() => setIsCreatingProject(!isCreatingProject)}
                  title="New Project"
                  className="p-1 hover:text-zinc-100 hover:bg-[#1b2130] rounded transition flex items-center gap-1 text-[11px] text-zinc-400"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>Project</span>
                </button>
              </div>
            </div>

            {/* Inline New Project Form */}
            {isCreatingProject && (
              <form
                onSubmit={handleCreateProjectSubmit}
                className="p-2.5 rounded border border-[#252d40] bg-[#121622] space-y-2 mb-2"
              >
                <div className="text-[11px] font-medium text-zinc-200">Yangi Loyiha Ochish</div>
                <input
                  type="text"
                  placeholder="Loyiha nomi (masalan: My-App)"
                  value={newProjectName}
                  onChange={(e) => setNewProjectName(e.target.value)}
                  className="w-full px-2 py-1 rounded bg-[#0b0e14] border border-[#232a3d] text-zinc-100 text-xs focus:outline-none focus:border-blue-500"
                  autoFocus
                />
                <input
                  type="text"
                  placeholder="Papka yo'li (ixtiyoriy)"
                  value={newProjectPath}
                  onChange={(e) => setNewProjectPath(e.target.value)}
                  className="w-full px-2 py-1 rounded bg-[#0b0e14] border border-[#232a3d] text-zinc-300 font-mono text-[11px] focus:outline-none focus:border-blue-500"
                />
                <div className="flex items-center justify-end gap-1.5 pt-1">
                  <button
                    type="button"
                    onClick={() => setIsCreatingProject(false)}
                    className="px-2 py-1 text-[11px] rounded text-zinc-400 hover:text-zinc-200 hover:bg-[#1a2030]"
                  >
                    Bekor
                  </button>
                  <button
                    type="submit"
                    disabled={!newProjectName.trim()}
                    className="px-2.5 py-1 text-[11px] font-medium rounded bg-blue-600 hover:bg-blue-500 text-white disabled:opacity-40 transition"
                  >
                    Yaratish
                  </button>
                </div>
              </form>
            )}

            {/* Projects & Chats Tree */}
            <div className="space-y-1">
              {projects.map((proj) => {
                const isActiveProj = proj.id === activeProjectId;
                const isExpanded = !!expandedProjects[proj.id];
                const projSessions = sessions.filter(
                  (s) => (s.project_id || "proj_default") === proj.id
                );

                return (
                  <div key={proj.id} className="rounded border border-transparent transition">
                    {/* Project Row */}
                    <div
                      className={`group flex items-center justify-between px-2 py-1.5 rounded cursor-pointer transition ${
                        isActiveProj
                          ? "bg-[#181e2b] text-blue-300 border border-[#263148]"
                          : "text-zinc-300 hover:bg-[#141824] hover:text-zinc-100"
                      }`}
                      onClick={() => {
                        onSelectProject(proj.id);
                        toggleProjectExpand(proj.id);
                      }}
                    >
                      <div className="flex items-center gap-1.5 min-w-0">
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            toggleProjectExpand(proj.id);
                          }}
                          className="text-zinc-400 hover:text-zinc-200"
                        >
                          {isExpanded ? (
                            <ChevronDown className="w-3.5 h-3.5" />
                          ) : (
                            <ChevronRight className="w-3.5 h-3.5" />
                          )}
                        </button>

                        {isActiveProj ? (
                          <FolderOpen className="w-3.5 h-3.5 text-blue-400 shrink-0" />
                        ) : (
                          <Folder className="w-3.5 h-3.5 text-zinc-400 shrink-0" />
                        )}

                        <span className="font-medium text-xs truncate" title={proj.path}>
                          {proj.name}
                        </span>

                        {isActiveProj && (
                          <span className="text-[9px] px-1 py-0.2 rounded bg-blue-950 text-blue-400 border border-blue-800/40">
                            active
                          </span>
                        )}
                      </div>

                      {/* Right action on hover */}
                      <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition">
                        <button
                          type="button"
                          title="New Chat in this project"
                          onClick={(e) => {
                            e.stopPropagation();
                            onSelectProject(proj.id);
                            onCreateSession(proj.id);
                          }}
                          className="p-0.5 hover:text-blue-300 rounded"
                        >
                          <Plus className="w-3.5 h-3.5" />
                        </button>
                        {proj.id !== "proj_default" && onDeleteProject && (
                          <button
                            type="button"
                            title="Delete project"
                            onClick={(e) => {
                              e.stopPropagation();
                              if (confirm(`"${proj.name}" loyihasini o'chirasizmi?`)) {
                                onDeleteProject(proj.id);
                              }
                            }}
                            className="p-0.5 hover:text-red-400 rounded"
                          >
                            <Trash2 className="w-3 h-3" />
                          </button>
                        )}
                      </div>
                    </div>

                    {/* Scoped Chat Sessions list for this project */}
                    {isExpanded && (
                      <div className="pl-4 pr-1 py-0.5 space-y-0.5 border-l border-[#1d2334] ml-3.5 mt-0.5">
                        {projSessions.length === 0 ? (
                          <div className="py-1 px-2 text-[11px] text-zinc-400 italic">
                            Chatlar yo'q
                          </div>
                        ) : (
                          projSessions.map((sess) => {
                            const isChatActive = sess.id === activeSessionId;
                            return (
                              <div
                                key={sess.id}
                                onClick={() => {
                                  onSelectProject(proj.id);
                                  onSelectSession(sess.id);
                                }}
                                className={`group flex items-center justify-between px-2 py-1 rounded cursor-pointer transition text-xs ${
                                  isChatActive
                                    ? "bg-[#1f2738] text-zinc-100 font-medium border border-[#2d3852]"
                                    : "text-zinc-400 hover:text-zinc-200 hover:bg-[#141824]"
                                }`}
                              >
                                <div className="flex items-center gap-1.5 min-w-0">
                                  <MessageSquare
                                    className={`w-3 h-3 shrink-0 ${
                                      isChatActive ? "text-blue-400" : "text-zinc-400"
                                    }`}
                                  />
                                  <span className="truncate">{sess.name}</span>
                                </div>

                                <div className="flex items-center gap-1">
                                  {sess.tokens > 0 && (
                                    <span className="text-[10px] font-mono text-zinc-400">
                                      {sess.tokens}t
                                    </span>
                                  )}
                                  {sess.id !== "default" && (
                                    <button
                                      type="button"
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        onDeleteSession(sess.id);
                                      }}
                                      className="opacity-0 group-hover:opacity-100 hover:text-red-400 p-0.5 transition"
                                    >
                                      <X className="w-3 h-3" />
                                    </button>
                                  )}
                                </div>
                              </div>
                            );
                          })
                        )}

                        {/* Add Chat inside this project */}
                        <button
                          type="button"
                          onClick={() => {
                            onSelectProject(proj.id);
                            onCreateSession(proj.id);
                          }}
                          className="w-full flex items-center gap-1.5 px-2 py-1 text-[11px] text-zinc-400 hover:text-blue-300 rounded hover:bg-[#141824] transition mt-1"
                        >
                          <Plus className="w-3 h-3" />
                          <span>Yangi chat</span>
                        </button>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* PLAN TAB */}
        {activeTab === "plan" && (
          <div className="space-y-3 p-1">
            <div className="text-[10px] font-semibold text-zinc-400 uppercase tracking-wider">
              Autonomous Plan Tracker
            </div>
            {plan && plan.steps && plan.steps.length > 0 ? (
              <div className="space-y-2">
                <div className="p-2 rounded border border-[#222838] bg-[#121622] space-y-1">
                  <div className="text-[11px] font-semibold text-zinc-200">Reja Xulosasi:</div>
                  <div className="text-[11px] text-zinc-400 leading-relaxed">{plan.summary}</div>
                </div>

                <div className="space-y-1 mt-2">
                  {plan.steps.map((step, idx) => {
                    const isDone = idx < plan.current_step;
                    const isCurrent = idx === plan.current_step;
                    return (
                      <div
                        key={idx}
                        className={`p-2 rounded border text-xs flex items-start gap-2 ${
                          isCurrent
                            ? "bg-blue-950/40 border-blue-500/50 text-blue-200"
                            : isDone
                            ? "bg-[#111520] border-[#1e2434] text-zinc-400 line-through"
                            : "bg-[#0f121a] border-[#1a2030] text-zinc-400"
                        }`}
                      >
                        {isDone ? (
                          <CheckCircle className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
                        ) : isCurrent ? (
                          <div className="w-3.5 h-3.5 rounded-full border-2 border-blue-400 shrink-0 mt-0.5 animate-pulse" />
                        ) : (
                          <Circle className="w-3.5 h-3.5 text-zinc-600 shrink-0 mt-0.5" />
                        )}
                        <span className="leading-snug">{step}</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            ) : (
              <div className="p-4 rounded border border-dashed border-[#222838] text-center text-zinc-400 text-xs">
                Faol reja mavjud emas. Katta vazifa berilganda agent avtomatik reja tuzadi.
              </div>
            )}
          </div>
        )}

        {/* LITERATURE & PAPERS TAB */}
        {activeTab === "literature" && (
          <div className="space-y-3 p-1">
            <div className="flex items-center justify-between pb-1 border-b border-[#1c2233]">
              <span className="text-[10px] font-semibold text-zinc-400 uppercase tracking-wider">
                Adabiyotlar & Maqolalar
              </span>
              <button
                onClick={fetchLiterature}
                className="p-1 hover:text-zinc-100 hover:bg-[#1b2130] rounded text-[11px] text-zinc-400 transition"
                title="Yangilash"
              >
                <RefreshCw className="w-3 h-3" />
              </button>
            </div>

            {/* Sub-section 1: Downloaded PDF Papers */}
            <div className="space-y-1.5">
              <div className="flex items-center gap-1.5 text-[11px] font-medium text-indigo-300">
                <Download className="w-3.5 h-3.5" />
                <span>Yuklangan Maqolalar ({literatureData.papers.length})</span>
              </div>
              {literatureData.papers.length === 0 ? (
                <div className="p-2.5 rounded border border-dashed border-[#202738] text-center text-zinc-500 text-[10px]">
                  outputs/papers/ papkasida PDF maqolalar yo'q. 'download_paper' orqali yuklang.
                </div>
              ) : (
                literatureData.papers.map((p) => (
                  <div
                    key={p.path}
                    onClick={() => onSelectFile && onSelectFile(p.path)}
                    className="p-2 rounded bg-[#121622] hover:bg-[#181e2e] border border-[#202738] flex items-center justify-between cursor-pointer transition group"
                  >
                    <div className="flex items-center gap-1.5 min-w-0">
                      <FileText className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
                      <span className="text-[11px] text-zinc-200 truncate group-hover:text-indigo-300 font-mono">
                        {p.name}
                      </span>
                    </div>
                    <span className="text-[10px] text-zinc-500 font-mono shrink-0 ml-1">
                      {(p.size / 1024).toFixed(0)} KB
                    </span>
                  </div>
                ))
              )}
            </div>

            {/* Sub-section 2: BibTeX References */}
            <div className="space-y-1.5 pt-1">
              <div className="flex items-center gap-1.5 text-[11px] font-medium text-emerald-300">
                <Bookmark className="w-3.5 h-3.5" />
                <span>BibTeX Iqtiboslar ({literatureData.references.length})</span>
              </div>
              {literatureData.references.length === 0 ? (
                <div className="p-2.5 rounded border border-dashed border-[#202738] text-center text-zinc-500 text-[10px]">
                  references.bib da iqtiboslar yo'q. 'manage_bibtex' orqali qo'shiladi.
                </div>
              ) : (
                literatureData.references.map((ref) => (
                  <div
                    key={ref.key}
                    className="p-2 rounded bg-[#121622] border border-[#202738] space-y-1 text-[11px]"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-emerald-400 font-semibold text-[10px]">
                        @{ref.key}
                      </span>
                      <button
                        onClick={() => {
                          navigator.clipboard.writeText(`\\cite{${ref.key}}`);
                          setCopiedCitation(ref.key);
                          setTimeout(() => setCopiedCitation(null), 2000);
                        }}
                        className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-950/60 border border-emerald-800/40 text-emerald-300 hover:bg-emerald-900/60 transition"
                      >
                        {copiedCitation === ref.key ? "✓ Nusxalandi" : "\\cite"}
                      </button>
                    </div>
                    <div className="text-zinc-300 text-[10px] line-clamp-2 leading-snug">
                      {ref.title}
                    </div>
                    {ref.year && (
                      <span className="text-[9px] text-zinc-500 font-mono">
                        Yil: {ref.year}
                      </span>
                    )}
                  </div>
                ))
              )}
            </div>

            {/* Sub-section 3: LaTeX Drafts */}
            <div className="space-y-1.5 pt-1">
              <div className="flex items-center gap-1.5 text-[11px] font-medium text-purple-300">
                <Sparkles className="w-3.5 h-3.5" />
                <span>LaTeX Qoralamalar ({literatureData.latex_drafts.length})</span>
              </div>
              {literatureData.latex_drafts.length === 0 ? (
                <div className="p-2.5 rounded border border-dashed border-[#202738] text-center text-zinc-500 text-[10px]">
                  Hozircha .tex fayllar topilmadi.
                </div>
              ) : (
                literatureData.latex_drafts.slice(0, 8).map((d) => (
                  <div
                    key={d.path}
                    onClick={() => onSelectFile && onSelectFile(d.path)}
                    className="p-1.5 rounded bg-[#121622] hover:bg-[#181e2e] border border-[#202738] flex items-center justify-between cursor-pointer transition group"
                  >
                    <span className="text-[11px] text-zinc-200 truncate font-mono group-hover:text-purple-300">
                      {d.name}
                    </span>
                    <span className="text-[10px] text-zinc-500 font-mono">
                      {(d.size / 1024).toFixed(1)} KB
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {/* CHECKPOINTS TAB */}
        {activeTab === "checkpoints" && (
          <div className="space-y-3 p-1">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-semibold text-zinc-400 uppercase tracking-wider">
                Git Snapshots ({checkpoints.length})
              </span>
              <button
                onClick={onUndo}
                disabled={checkpoints.length === 0}
                className="px-2 py-0.5 rounded bg-amber-500/10 hover:bg-amber-500/20 text-amber-300 border border-amber-500/30 flex items-center gap-1 text-[11px] disabled:opacity-40 transition"
              >
                <RotateCcw className="w-3 h-3" />
                <span>Undo</span>
              </button>
            </div>

            <div className="space-y-1.5">
              {checkpoints.length === 0 ? (
                <div className="p-4 rounded border border-dashed border-[#222838] text-center text-zinc-400 text-xs">
                  Hozircha saqlangan snapshotlar yo'q.
                </div>
              ) : (
                checkpoints.map((cp) => (
                  <div
                    key={cp.id}
                    className="p-2 rounded border border-[#202738] bg-[#121622] space-y-1"
                  >
                    <div className="flex items-center justify-between text-[11px] font-medium text-zinc-200">
                      <span className="truncate max-w-[160px]">{cp.description}</span>
                      <span className="text-[10px] font-mono text-zinc-400">{cp.time}</span>
                    </div>
                    <div className="text-[10px] text-zinc-400 truncate">
                      {cp.files.join(", ")}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}
      </div>
    </aside>
  );
};
