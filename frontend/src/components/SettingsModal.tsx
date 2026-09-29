"use client";

import React, { useEffect, useState } from "react";
import { AppSettings, ModelItem } from "@/types";
import { X, Check, Search, Plus, Trash2, Cpu, Globe, Server, CheckCircle2 } from "lucide-react";

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSaved: () => void;
  backendUrl: string;
}

export const SettingsModal: React.FC<SettingsModalProps> = ({
  isOpen,
  onClose,
  onSaved,
  backendUrl,
}) => {
  const [activeTab, setActiveTab] = useState<"models" | "agent" | "workspace" | "prompt">("models");
  const [settings, setSettings] = useState<AppSettings>({
    ollama_url: "http://127.0.0.1:11434",
    default_model: "gemma4-26b:latest",
    temperature: 0.2,
    max_iterations: 30,
    system_prompt: "",
    workspace_dir: "",
    plan_mode_auto: true,
    critic_enabled: true,
    auto_flush_context: true,
    context_window_size: 262144,
    top_p: 0.95,
  });

  const [models, setModels] = useState<ModelItem[]>([]);
  const [isScanning, setIsScanning] = useState(false);
  const [scanMessage, setScanMessage] = useState("");
  const [isAddingModel, setIsAddingModel] = useState(false);

  // New Custom Model Form State
  const [newModelName, setNewModelName] = useState("");
  const [newProvider, setNewProvider] = useState<"openai_compatible" | "ollama">("openai_compatible");
  const [newBaseUrl, setNewBaseUrl] = useState("https://api.deepseek.com/v1");
  const [newApiKey, setNewApiKey] = useState("");
  const [newModelId, setNewModelId] = useState("deepseek-chat");
  const [newInputCost, setNewInputCost] = useState("0.14");
  const [newOutputCost, setNewOutputCost] = useState("0.28");

  const [loading, setLoading] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);

  const fetchModels = () => {
    fetch(`${backendUrl}/api/models`)
      .then((r) => r.json())
      .then((data) => {
        if (data.models) setModels(data.models);
      })
      .catch(console.error);
  };

  useEffect(() => {
    if (isOpen) {
      fetch(`${backendUrl}/api/settings`)
        .then((r) => r.json())
        .then((data) => {
          setSettings((prev) => ({
            ...prev,
            ...data,
          }));
        })
        .catch(console.error);

      fetchModels();
    }
  }, [isOpen, backendUrl]);

  if (!isOpen) return null;

  // Auto-scan local servers (Ollama, LM Studio, vLLM)
  const handleScanLocal = async () => {
    setIsScanning(true);
    setScanMessage("");
    try {
      const res = await fetch(`${backendUrl}/api/models/scan`, { method: "POST" });
      const data = await res.json();
      if (data.status === "success") {
        setScanMessage(`Tayyor! ${data.added_count} ta yangi lokal model topildi.`);
        fetchModels();
      }
    } catch (e: any) {
      setScanMessage(`Skanerlashda xatolik: ${e.message}`);
    } finally {
      setIsScanning(false);
    }
  };

  // Add custom API model with pricing
  const handleAddCustomModel = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newModelName.trim() || !newBaseUrl.trim() || !newModelId.trim()) return;

    try {
      const res = await fetch(`${backendUrl}/api/models`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: newModelName.trim(),
          provider: newProvider,
          base_url: newBaseUrl.trim(),
          model_name: newModelId.trim(),
          api_key: newApiKey.trim() || null,
          input_cost_per_1m: parseFloat(newInputCost) || 0.0,
          output_cost_per_1m: parseFloat(newOutputCost) || 0.0,
        }),
      });
      const data = await res.json();
      if (data.status === "success") {
        setIsAddingModel(false);
        setNewModelName("");
        setNewApiKey("");
        fetchModels();
      }
    } catch (e: any) {
      alert(`Model qo'shishda xatolik: ${e.message}`);
    }
  };

  const handleDeleteModel = async (id: string) => {
    try {
      await fetch(`${backendUrl}/api/models/${id}`, { method: "DELETE" });
      fetchModels();
    } catch (e: any) {
      console.error(e);
    }
  };

  const handleSelectDefaultModel = (modelName: string) => {
    setSettings({ ...settings, default_model: modelName });
  };

  const handleSave = async () => {
    setLoading(true);
    try {
      await fetch(`${backendUrl}/api/settings`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(settings),
      });

      if (settings.workspace_dir) {
        await fetch(`${backendUrl}/api/workspace`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ path: settings.workspace_dir }),
        });
      }

      setSavedSuccess(true);
      setTimeout(() => {
        setSavedSuccess(false);
        onSaved();
        onClose();
      }, 700);
    } catch (e: any) {
      alert(`Xatolik: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  const resetSystemPrompt = () => {
    const defaultPrompt = `You are an autonomous AI software engineer, terminal assistant, and researcher (similar to Claude Code and Codex), powered by local intelligence.

Your goals:
1. Act methodically: understand the problem, inspect the relevant files, formulate a clear plan, and execute changes.
2. Use tools directly to inspect the environment, read files, write code, run shell commands, and verify results.
3. When writing or modifying files, make minimal, surgical changes. Always verify your changes (run tests, check syntax, or compile).
4. Be concise and direct in your communication. Avoid unnecessary flattery or lengthy disclaimers. Focus on actions, results, and precise explanations.
5. If a command or tool returns an error, carefully inspect the error message and self-correct instead of giving up.
6. When editing code, ensure you do not break existing functionality.
7. For conversational greetings, conceptual explanations, and general knowledge questions, respond directly and concisely WITHOUT calling any tools. Only invoke tools when the task requires inspecting files, running commands, editing code, compiling, or querying the environment.`;
    setSettings({ ...settings, system_prompt: defaultPrompt });
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="w-full max-w-3xl bg-[#0f1218] border border-[#222838] rounded-lg shadow-xl overflow-hidden flex flex-col h-[78vh]">
        {/* Header */}
        <div className="px-5 py-3 border-b border-[#202636] flex items-center justify-between bg-[#11141c]">
          <div>
            <h2 className="font-semibold text-xs text-zinc-100 uppercase tracking-wider">
              Tizim Sozlamalari
            </h2>
            <p className="text-[11px] text-zinc-400">
              Ollama, LM Studio, tashqi API ulash, narx hisoblash va ReAct avtonomiyasi
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-1 text-zinc-400 hover:text-zinc-100 rounded hover:bg-[#1a202e] transition"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Body */}
        <div className="flex flex-1 overflow-hidden">
          {/* Side tabs */}
          <div className="w-48 border-r border-[#202636] bg-[#0c0e14] p-2 space-y-0.5 shrink-0">
            <button
              onClick={() => setActiveTab("models")}
              className={`w-full text-left px-3 py-2 rounded text-xs font-medium transition ${
                activeTab === "models"
                  ? "bg-[#181e2b] text-blue-400 border border-[#263148]"
                  : "text-zinc-400 hover:text-zinc-200 hover:bg-[#121622]"
              }`}
            >
              Modellar & API Provayderlar
            </button>
            <button
              onClick={() => setActiveTab("agent")}
              className={`w-full text-left px-3 py-2 rounded text-xs font-medium transition ${
                activeTab === "agent"
                  ? "bg-[#181e2b] text-blue-400 border border-[#263148]"
                  : "text-zinc-400 hover:text-zinc-200 hover:bg-[#121622]"
              }`}
            >
              ReAct & Avtonomiya
            </button>
            <button
              onClick={() => setActiveTab("workspace")}
              className={`w-full text-left px-3 py-2 rounded text-xs font-medium transition ${
                activeTab === "workspace"
                  ? "bg-[#181e2b] text-blue-400 border border-[#263148]"
                  : "text-zinc-400 hover:text-zinc-200 hover:bg-[#121622]"
              }`}
            >
              Ishchi Katalog
            </button>
            <button
              onClick={() => setActiveTab("prompt")}
              className={`w-full text-left px-3 py-2 rounded text-xs font-medium transition ${
                activeTab === "prompt"
                  ? "bg-[#181e2b] text-blue-400 border border-[#263148]"
                  : "text-zinc-400 hover:text-zinc-200 hover:bg-[#121622]"
              }`}
            >
              Tizim Instruksiyasi
            </button>
          </div>

          {/* Form Content */}
          <div className="flex-1 overflow-y-auto p-5 text-xs text-zinc-300 space-y-5 bg-[#0f1218]">
            {/* TAB: MODELS & API PROVIDERS */}
            {activeTab === "models" && (
              <div className="space-y-4">
                {/* Actions: Auto-Scan & Add API */}
                <div className="flex items-center justify-between gap-2 p-3 rounded border border-[#202738] bg-[#121622]">
                  <div>
                    <div className="font-medium text-zinc-200">Lokal & Tashqi Modellar</div>
                    <div className="text-[11px] text-zinc-400">
                      Ollama (11434), LM Studio (1234), vLLM (8000) ni avtomatik aniqlang yoki yangi API ulang.
                    </div>
                  </div>
                  <div className="flex items-center gap-1.5 shrink-0">
                    <button
                      type="button"
                      onClick={handleScanLocal}
                      disabled={isScanning}
                      className="px-2.5 py-1 rounded bg-[#181e2b] hover:bg-[#20283a] text-blue-300 border border-[#28354f] flex items-center gap-1 text-xs transition disabled:opacity-50"
                    >
                      <Search className="w-3.5 h-3.5" />
                      <span>{isScanning ? "Qidirilmoqda..." : "Lokalni Topish"}</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => setIsAddingModel(!isAddingModel)}
                      className="px-2.5 py-1 rounded bg-blue-600 hover:bg-blue-500 text-white flex items-center gap-1 text-xs transition"
                    >
                      <Plus className="w-3.5 h-3.5" />
                      <span>API Ulash</span>
                    </button>
                  </div>
                </div>

                {scanMessage && (
                  <div className="p-2 rounded bg-blue-950/40 border border-blue-500/30 text-blue-200 text-[11px]">
                    {scanMessage}
                  </div>
                )}

                {/* Form to Add Custom Model / API */}
                {isAddingModel && (
                  <form
                    onSubmit={handleAddCustomModel}
                    className="p-3.5 rounded border border-[#263148] bg-[#131724] space-y-3"
                  >
                    <div className="font-semibold text-zinc-100 flex items-center justify-between text-xs">
                      <span>Yangi Model / Tashqi API Qo'shish</span>
                      <button
                        type="button"
                        onClick={() => setIsAddingModel(false)}
                        className="text-zinc-500 hover:text-zinc-300"
                      >
                        <X className="w-3.5 h-3.5" />
                      </button>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
                      <div className="space-y-1">
                        <label className="text-[11px] text-zinc-400">Ko'rinadigan Nomi:</label>
                        <input
                          type="text"
                          placeholder="masalan: DeepSeek V3 (API)"
                          value={newModelName}
                          onChange={(e) => setNewModelName(e.target.value)}
                          className="w-full px-2 py-1.5 rounded bg-[#0b0e14] border border-[#232a3d] text-zinc-100 text-xs focus:outline-none focus:border-blue-500"
                          required
                        />
                      </div>

                      <div className="space-y-1">
                        <label className="text-[11px] text-zinc-400">Provayder Turi:</label>
                        <select
                          value={newProvider}
                          onChange={(e: any) => setNewProvider(e.target.value)}
                          className="w-full px-2 py-1.5 rounded bg-[#0b0e14] border border-[#232a3d] text-zinc-200 text-xs focus:outline-none focus:border-blue-500"
                        >
                          <option value="openai_compatible">OpenAI-Compatible (OpenRouter / DeepSeek / LM Studio)</option>
                          <option value="ollama">Ollama Native</option>
                        </select>
                      </div>

                      <div className="space-y-1">
                        <label className="text-[11px] text-zinc-400">Base URL (Endpoint):</label>
                        <input
                          type="text"
                          placeholder="https://api.deepseek.com/v1 yoki http://127.0.0.1:1234/v1"
                          value={newBaseUrl}
                          onChange={(e) => setNewBaseUrl(e.target.value)}
                          className="w-full px-2 py-1.5 rounded bg-[#0b0e14] border border-[#232a3d] text-zinc-100 font-mono text-[11px] focus:outline-none focus:border-blue-500"
                          required
                        />
                      </div>

                      <div className="space-y-1">
                        <label className="text-[11px] text-zinc-400">API Key (Agar kerak bo'lsa):</label>
                        <input
                          type="password"
                          placeholder="sk-..."
                          value={newApiKey}
                          onChange={(e) => setNewApiKey(e.target.value)}
                          className="w-full px-2 py-1.5 rounded bg-[#0b0e14] border border-[#232a3d] text-zinc-100 font-mono text-[11px] focus:outline-none focus:border-blue-500"
                        />
                      </div>

                      <div className="space-y-1 md:col-span-2">
                        <label className="text-[11px] text-zinc-400">Model ID / Nomi:</label>
                        <input
                          type="text"
                          placeholder="deepseek-chat yoki anthropic/claude-3.7-sonnet"
                          value={newModelId}
                          onChange={(e) => setNewModelId(e.target.value)}
                          className="w-full px-2 py-1.5 rounded bg-[#0b0e14] border border-[#232a3d] text-zinc-100 font-mono text-xs focus:outline-none focus:border-blue-500"
                          required
                        />
                      </div>

                      {/* Pricing Fields */}
                      <div className="space-y-1">
                        <label className="text-[11px] text-zinc-400">
                          Input Narxi ($ per 1 Million token):
                        </label>
                        <input
                          type="number"
                          step="0.01"
                          placeholder="0.14"
                          value={newInputCost}
                          onChange={(e) => setNewInputCost(e.target.value)}
                          className="w-full px-2 py-1.5 rounded bg-[#0b0e14] border border-[#232a3d] text-zinc-100 font-mono text-xs focus:outline-none focus:border-blue-500"
                        />
                      </div>

                      <div className="space-y-1">
                        <label className="text-[11px] text-zinc-400">
                          Output Narxi ($ per 1 Million token):
                        </label>
                        <input
                          type="number"
                          step="0.01"
                          placeholder="0.28"
                          value={newOutputCost}
                          onChange={(e) => setNewOutputCost(e.target.value)}
                          className="w-full px-2 py-1.5 rounded bg-[#0b0e14] border border-[#232a3d] text-zinc-100 font-mono text-xs focus:outline-none focus:border-blue-500"
                        />
                      </div>
                    </div>

                    <div className="flex justify-end gap-2 pt-1 border-t border-[#1e2434]">
                      <button
                        type="button"
                        onClick={() => setIsAddingModel(false)}
                        className="px-2.5 py-1 rounded text-zinc-400 hover:text-zinc-200"
                      >
                        Bekor
                      </button>
                      <button
                        type="submit"
                        className="px-3 py-1 rounded bg-blue-600 hover:bg-blue-500 text-white font-medium"
                      >
                        Modelni Saqlash
                      </button>
                    </div>
                  </form>
                )}

                {/* Models List */}
                <div className="space-y-1.5">
                  <div className="text-[10px] font-semibold text-zinc-400 uppercase tracking-wider px-1">
                    Ro'yxatdagi Modellar ({models.length})
                  </div>

                  <div className="space-y-1.5">
                    {models.map((m, idx) => {
                      const isDefault = settings.default_model === m.model_name || settings.default_model === m.id;
                      return (
                        <div
                          key={`${m.id}_${idx}`}
                          className={`p-2.5 rounded border flex items-center justify-between transition ${
                            isDefault
                              ? "bg-[#182030] border-blue-500/40 text-zinc-100"
                              : "bg-[#111520] border-[#1e2434] text-zinc-300"
                          }`}
                        >
                          <div className="flex items-center gap-2 min-w-0">
                            {m.is_local ? (
                              <Server className="w-4 h-4 text-emerald-400 shrink-0" />
                            ) : (
                              <Globe className="w-4 h-4 text-blue-400 shrink-0" />
                            )}
                            <div className="min-w-0">
                              <div className="font-medium text-xs truncate flex items-center gap-1.5">
                                <span>{m.name || m.model_name}</span>
                                {isDefault && (
                                  <span className="text-[9px] px-1 py-0.2 rounded bg-blue-950 text-blue-300 border border-blue-800/40">
                                    Standart
                                  </span>
                                )}
                              </div>
                              <div className="text-[10px] font-mono text-zinc-400 flex items-center gap-2">
                                <span>{m.provider}</span>
                                <span>•</span>
                                {m.is_local ? (
                                  <span className="text-emerald-400 font-medium">Lokal (Bepul)</span>
                                ) : (
                                  <span className="text-zinc-300">
                                    In: ${m.input_cost_per_1m}/1M • Out: ${m.output_cost_per_1m}/1M
                                  </span>
                                )}
                              </div>
                            </div>
                          </div>

                          <div className="flex items-center gap-1.5 shrink-0">
                            {!isDefault && (
                              <button
                                type="button"
                                onClick={() => handleSelectDefaultModel(m.model_name)}
                                className="px-2 py-0.5 rounded text-[11px] bg-[#1a2130] hover:bg-[#232c40] text-zinc-300 border border-[#2a354c] transition"
                              >
                                Standart qilish
                              </button>
                            )}
                            {m.id !== "gemma4-26b:latest" && (
                              <button
                                type="button"
                                onClick={() => handleDeleteModel(m.id)}
                                title="Modelni o'chirish"
                                className="p-1 text-zinc-500 hover:text-red-400 rounded transition"
                              >
                                <Trash2 className="w-3.5 h-3.5" />
                              </button>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Sampling Temperature */}
                <div className="p-3 rounded border border-[#202738] bg-[#121622] space-y-2 mt-2">
                  <div className="flex justify-between items-center">
                    <span className="text-zinc-200 font-medium">Sampling Temperature</span>
                    <span className="font-mono text-zinc-100 font-semibold">{settings.temperature}</span>
                  </div>
                  <input
                    type="range"
                    min="0.0"
                    max="1.0"
                    step="0.05"
                    value={settings.temperature}
                    onChange={(e) =>
                      setSettings({ ...settings, temperature: parseFloat(e.target.value) })
                    }
                    className="w-full accent-blue-500 cursor-pointer h-1.5 bg-[#1b2232] rounded"
                  />
                  <div className="text-[10px] text-zinc-400">
                    Dasturlash va buyruqlar uchun 0.1 - 0.2 qat'iy aniqlik beradi.
                  </div>
                </div>
              </div>
            )}

            {/* TAB: AGENT & AUTONOMY */}
            {activeTab === "agent" && (
              <div className="space-y-4">
                <div className="p-3.5 rounded border border-[#202738] bg-[#121622] space-y-2.5">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="font-medium text-zinc-200 text-xs">
                        Maksimal qadamlar soni (Max Iterations)
                      </div>
                      <div className="text-[11px] text-zinc-400">
                        Bitta vazifa uchun to'xtamasdan bajariladigan qadamlar limiti.
                      </div>
                    </div>
                    <span className="font-mono text-zinc-100 font-semibold px-2 py-0.5 rounded bg-[#1a2130] border border-[#2a344d]">
                      {settings.max_iterations} qadam
                    </span>
                  </div>
                  <input
                    type="range"
                    min="5"
                    max="200"
                    step="5"
                    value={settings.max_iterations}
                    onChange={(e) =>
                      setSettings({ ...settings, max_iterations: parseInt(e.target.value) })
                    }
                    className="w-full accent-blue-500 cursor-pointer h-1.5 bg-[#1b2232] rounded"
                  />
                  <div className="flex justify-between text-[10px] font-mono text-zinc-400">
                    <span>5</span>
                    <span>30 (standart)</span>
                    <span>100</span>
                    <span>200</span>
                  </div>
                </div>

                <div className="p-3.5 rounded border border-[#202738] bg-[#121622] flex items-center justify-between">
                  <div className="pr-4">
                    <div className="font-medium text-zinc-200 text-xs">Plan Mode (Auto-Blueprint)</div>
                    <div className="text-[11px] text-zinc-400">
                      Ulkan vazifalarda avval reja tuzib, o'zini bosqichma-bosqich uyg'otish.
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() =>
                      setSettings({ ...settings, plan_mode_auto: !settings.plan_mode_auto })
                    }
                    className={`px-3 py-1 rounded text-xs font-medium border transition ${
                      settings.plan_mode_auto
                        ? "bg-blue-600/20 text-blue-300 border-blue-500/40"
                        : "bg-[#181e2b] text-zinc-400 border-[#263148]"
                    }`}
                  >
                    {settings.plan_mode_auto ? "Yoqilgan" : "O'chiq"}
                  </button>
                </div>

                <div className="p-3.5 rounded border border-[#202738] bg-[#121622] flex items-center justify-between">
                  <div className="pr-4">
                    <div className="font-medium text-zinc-200 text-xs">
                      LLM Self-Critic & Drift Tekshiruvi
                    </div>
                    <div className="text-[11px] text-zinc-400">
                      Har bir vazifa yakunida modelning maqsaddan og'ish darajasini (0-100%) tekshirish.
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() =>
                      setSettings({ ...settings, critic_enabled: !settings.critic_enabled })
                    }
                    className={`px-3 py-1 rounded text-xs font-medium border transition ${
                      settings.critic_enabled
                        ? "bg-blue-600/20 text-blue-300 border-blue-500/40"
                        : "bg-[#181e2b] text-zinc-400 border-[#263148]"
                    }`}
                  >
                    {settings.critic_enabled ? "Yoqilgan" : "O'chiq"}
                  </button>
                </div>

                <div className="p-3.5 rounded border border-[#202738] bg-[#121622] flex items-center justify-between">
                  <div className="pr-4">
                    <div className="font-medium text-zinc-200 text-xs">
                      Auto Context Flush (Dense Memory)
                    </div>
                    <div className="text-[11px] text-zinc-400">
                      Vazifa tugagach ortiqcha xom toollar natijalarini tozalash va xulosani .agent_memory.json da saqlash.
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() =>
                      setSettings({ ...settings, auto_flush_context: !settings.auto_flush_context })
                    }
                    className={`px-3 py-1 rounded text-xs font-medium border transition ${
                      settings.auto_flush_context
                        ? "bg-blue-600/20 text-blue-300 border-blue-500/40"
                        : "bg-[#181e2b] text-zinc-400 border-[#263148]"
                    }`}
                  >
                    {settings.auto_flush_context ? "Yoqilgan" : "O'chiq"}
                  </button>
                </div>
              </div>
            )}

            {/* TAB: WORKSPACE */}
            {activeTab === "workspace" && (
              <div className="space-y-4">
                <div className="space-y-1">
                  <label className="text-zinc-300 font-medium">
                    Ishchi Katalog Yo'li (Project Workspace)
                  </label>
                  <input
                    type="text"
                    value={settings.workspace_dir}
                    onChange={(e) => setSettings({ ...settings, workspace_dir: e.target.value })}
                    className="w-full px-2.5 py-2 rounded bg-[#121622] border border-[#23293a] text-zinc-100 font-mono text-xs focus:outline-none focus:border-blue-500"
                  />
                  <p className="text-[11px] text-zinc-400">
                    Terminal buyruqlari va fayllar tahriri shu papka ichida bajariladi.
                  </p>
                </div>

                <div className="p-3 rounded border border-[#202738] bg-[#121622] space-y-1">
                  <div className="font-medium text-zinc-200">Avtomatik Checkpointlar va Rollback</div>
                  <p className="text-[11px] text-zinc-400 leading-relaxed">
                    Har bir fayl o'zgarishidan oldin .agent_checkpoints/ papkasiga avtomatik nusxa olinadi. Undo tugmasi bilan istalgan o'zgarishni bekor qilishingiz mumkin.
                  </p>
                </div>
              </div>
            )}

            {/* TAB: SYSTEM PROMPT */}
            {activeTab === "prompt" && (
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <label className="text-zinc-300 font-medium">Tizim Qoidalari (System Prompt)</label>
                  <button
                    type="button"
                    onClick={resetSystemPrompt}
                    className="text-[11px] text-zinc-400 hover:text-zinc-200 px-2 py-0.5 rounded hover:bg-[#181e2b] border border-[#222838]"
                  >
                    Standartga qaytarish
                  </button>
                </div>
                <textarea
                  rows={10}
                  value={settings.system_prompt}
                  onChange={(e) => setSettings({ ...settings, system_prompt: e.target.value })}
                  className="w-full px-3 py-2 rounded bg-[#121622] border border-[#23293a] text-zinc-200 font-mono text-xs focus:outline-none focus:border-blue-500 leading-relaxed"
                />
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="px-5 py-3 border-t border-[#202636] bg-[#11141c] flex items-center justify-between">
          <span className="text-[11px] text-zinc-400">
            O'zgarishlar darhol joriy qilinadi
          </span>
          <div className="flex items-center gap-2">
            <button
              onClick={onClose}
              className="px-3 py-1.5 rounded text-xs text-zinc-300 hover:text-white hover:bg-[#1a202e] border border-[#222838] transition"
            >
              Bekor qilish
            </button>
            <button
              onClick={handleSave}
              disabled={loading}
              className="px-4 py-1.5 rounded text-xs font-medium bg-blue-600 hover:bg-blue-500 text-white transition flex items-center gap-1.5 shadow-xs"
            >
              {savedSuccess ? (
                <>
                  <Check className="w-3.5 h-3.5" />
                  <span>Saqlandi</span>
                </>
              ) : (
                <span>Saqlash</span>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
