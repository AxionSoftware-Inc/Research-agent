"use client";

import React, { useEffect, useState } from "react";
import {
  X,
  Copy,
  Check,
  FileCode,
  ExternalLink,
  Save,
  Play,
  Download,
  Maximize2,
  Minimize2,
  FileText,
  AlertCircle,
  Loader2,
} from "lucide-react";

interface FileViewerDrawerProps {
  filePath: string | null;
  onClose: () => void;
  onSelectFile?: (path: string) => void;
}

export const FileViewerDrawer: React.FC<FileViewerDrawerProps> = ({
  filePath,
  onClose,
  onSelectFile,
}) => {
  const [content, setContent] = useState<string>("");
  const [isEditing, setIsEditing] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(false);
  const [copied, setCopied] = useState<boolean>(false);
  const [saving, setSaving] = useState<boolean>(false);
  const [savedSuccess, setSavedSuccess] = useState<boolean>(false);
  const [compiling, setCompiling] = useState<boolean>(false);
  const [compileStatus, setCompileStatus] = useState<string | null>(null);
  const [isWide, setIsWide] = useState<boolean>(false);

  const isPdf = filePath?.toLowerCase().endsWith(".pdf");
  const isTex = filePath?.toLowerCase().endsWith(".tex");

  const rawUrl = filePath
    ? `http://127.0.0.1:8765/api/file/raw?path=${encodeURIComponent(filePath)}`
    : "";

  useEffect(() => {
    if (!filePath || isPdf) return;
    setLoading(true);
    setCompileStatus(null);
    fetch(`http://127.0.0.1:8765/api/file/content?path=${encodeURIComponent(filePath)}`)
      .then((res) => res.json())
      .then((data) => {
        setContent(data.content || "");
        setLoading(false);
      })
      .catch((err) => {
        setContent(`Error loading file: ${err.message}`);
        setLoading(false);
      });
  }, [filePath, isPdf]);

  if (!filePath) return null;

  const handleCopy = () => {
    navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const res = await fetch("http://127.0.0.1:8765/api/file/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ path: filePath, content }),
      });
      if (res.ok) {
        setSavedSuccess(true);
        setTimeout(() => setSavedSuccess(false), 2500);
      }
    } catch (e) {
      console.error("Save error:", e);
    } finally {
      setSaving(false);
    }
  };

  const handleCompile = async () => {
    if (!isTex) return;
    setCompiling(true);
    setCompileStatus("Kompilatsiya qilinmoqda...");
    try {
      // First save current content
      await fetch("http://127.0.0.1:8765/api/file/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ path: filePath, content }),
      });

      const res = await fetch("http://127.0.0.1:8765/api/latex/compile", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tex_path: filePath }),
      });
      const data = await res.json();
      if (data.status === "success") {
        setCompileStatus("Kompilatsiya muvaffaqiyatli!");
        if (data.pdf_path && onSelectFile) {
          setTimeout(() => {
            onSelectFile(data.pdf_path);
          }, 1000);
        }
      } else {
        setCompileStatus(`Xatolik: ${data.message || data.error || "Noma'lum"}`);
      }
    } catch (e: any) {
      setCompileStatus(`Xatolik: ${e.message}`);
    } finally {
      setCompiling(false);
    }
  };

  return (
    <div
      className={`fixed inset-y-0 right-0 ${
        isWide ? "w-4/5" : "w-1/2 min-w-[500px]"
      } bg-[#0b0e14] border-l border-[#262c3f] shadow-2xl z-40 flex flex-col transition-all duration-200`}
    >
      {/* Header */}
      <div className="h-14 border-b border-[#232838] bg-[#10141f] px-4 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-2 font-mono text-xs text-zinc-200 truncate max-w-[55%]">
          {isPdf ? (
            <FileText className="w-4 h-4 text-rose-400 shrink-0" />
          ) : (
            <FileCode className="w-4 h-4 text-cyan-400 shrink-0" />
          )}
          <span className="truncate">{filePath}</span>
        </div>

        <div className="flex items-center gap-1.5">
          {isTex && (
            <button
              onClick={handleCompile}
              disabled={compiling}
              title="PDF ga kompilatsiya qilish"
              className="flex items-center gap-1 px-2.5 py-1 text-xs rounded bg-indigo-600/30 hover:bg-indigo-600/50 text-indigo-200 border border-indigo-500/40 transition"
            >
              {compiling ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <Play className="w-3 h-3 text-indigo-400" />
              )}
              <span>Kompilatsiya</span>
            </button>
          )}

          {!isPdf && (
            <>
              <button
                onClick={() => setIsEditing(!isEditing)}
                className={`px-2 py-1 text-xs rounded transition border ${
                  isEditing
                    ? "bg-amber-500/20 text-amber-300 border-amber-500/40"
                    : "bg-[#171d2b] text-zinc-400 border-zinc-700/60 hover:text-zinc-200"
                }`}
              >
                {isEditing ? "Ko'rish rejimi" : "Tahrirlash"}
              </button>

              <button
                onClick={handleSave}
                disabled={saving}
                title="Faylni saqlash"
                className="flex items-center gap-1 px-2 py-1 text-xs rounded bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-300 border border-emerald-500/40 transition"
              >
                {savedSuccess ? (
                  <Check className="w-3.5 h-3.5 text-emerald-400" />
                ) : (
                  <Save className="w-3.5 h-3.5" />
                )}
                <span>{savedSuccess ? "Saqlandi" : "Saqlash"}</span>
              </button>

              <button
                onClick={handleCopy}
                title="Nusxalash"
                className="p-1.5 hover:bg-[#1d2232] rounded text-zinc-400 hover:text-white transition"
              >
                {copied ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
              </button>
            </>
          )}

          {isPdf && (
            <>
              <a
                href={rawUrl}
                download
                title="PDF yuklab olish"
                className="p-1.5 hover:bg-[#1d2232] rounded text-zinc-400 hover:text-white transition flex items-center"
              >
                <Download className="w-4 h-4 text-zinc-300" />
              </a>
              <a
                href={rawUrl}
                target="_blank"
                rel="noreferrer"
                title="Alohida oynada ochish"
                className="p-1.5 hover:bg-[#1d2232] rounded text-zinc-400 hover:text-white transition flex items-center"
              >
                <ExternalLink className="w-4 h-4 text-zinc-300" />
              </a>
            </>
          )}

          <button
            onClick={() => setIsWide(!isWide)}
            title={isWide ? "Kichraytirish" : "Kengaytirish"}
            className="p-1.5 hover:bg-[#1d2232] rounded text-zinc-400 hover:text-white transition"
          >
            {isWide ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
          </button>

          <button
            onClick={onClose}
            className="p-1.5 hover:bg-[#1d2232] rounded text-zinc-400 hover:text-white transition"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Compile notification bar if active */}
      {compileStatus && (
        <div
          className={`px-4 py-1.5 text-xs flex items-center gap-2 border-b ${
            compileStatus.includes("muvaffaqiyatli")
              ? "bg-emerald-950/40 text-emerald-300 border-emerald-800/40"
              : compileStatus.includes("Xatolik")
              ? "bg-rose-950/40 text-rose-300 border-rose-800/40"
              : "bg-indigo-950/40 text-indigo-300 border-indigo-800/40"
          }`}
        >
          {compileStatus.includes("Xatolik") ? (
            <AlertCircle className="w-3.5 h-3.5 text-rose-400 shrink-0" />
          ) : compileStatus.includes("muvaffaqiyatli") ? (
            <Check className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
          ) : (
            <Loader2 className="w-3.5 h-3.5 animate-spin text-indigo-400 shrink-0" />
          )}
          <span className="truncate">{compileStatus}</span>
        </div>
      )}

      {/* Main Body */}
      <div className="flex-1 overflow-hidden bg-[#090b10] flex flex-col">
        {isPdf ? (
          <div className="w-full h-full bg-[#181a20]">
            <iframe
              src={rawUrl}
              title={filePath}
              className="w-full h-full border-0"
            />
          </div>
        ) : loading ? (
          <div className="flex items-center justify-center h-full text-zinc-500 text-xs">
            <Loader2 className="w-5 h-5 animate-spin mr-2" />
            Fayl yuklanmoqda...
          </div>
        ) : isEditing ? (
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            className="w-full h-full p-4 font-mono text-xs leading-relaxed text-zinc-200 bg-[#090b10] resize-none outline-none focus:ring-1 focus:ring-indigo-500/50"
            spellCheck={false}
          />
        ) : (
          <div className="flex-1 overflow-auto p-4 font-mono text-xs text-zinc-300 bg-[#090b10]">
            <pre className="whitespace-pre overflow-x-auto leading-relaxed">
              {content.split("\n").map((line, i) => (
                <div key={i} className="table-row">
                  <span className="table-cell pr-4 text-right select-none text-zinc-600 w-10">
                    {i + 1}
                  </span>
                  <span className="table-cell">{line}</span>
                </div>
              ))}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
};
