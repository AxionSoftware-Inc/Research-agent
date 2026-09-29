# Autonomous AI Research Agent & Deep Research Lab

An autonomous, local AI research scientist, literature review, and manuscript preparation system. Designed to search academic preprints (arXiv) and the open web, download research papers, decompose PDFs into modular LaTeX sections, translate academic prose into Uzbek while preserving 100% of mathematical equations and citations, reassemble master manuscripts, audit syntax and citation keys, and compile publication-ready PDFs with Tectonic.

Equipped with an **autonomous self-healing auto-fixer** and **small model resilience engine** (optimized for 7B/8B/14B local models like `gemma4-26b`, `llama3.1-8b`, `qwen2.5-7b`).

---

## 🔬 Core Capabilities

1. **Academic Discovery & Downloader:**
   - **`search_arxiv`**: Queries arXiv for preprints, titles, abstracts, dates, and direct PDF links.
   - **`search_web`**: Live web search across Google Scholar, Nature, Science, and technical articles via DuckDuckGo.
   - **`download_paper`**: Downloads papers directly via arXiv ID (`2301.12345`), DOI, or PDF URL to `outputs/papers/`.
   - **`fetch_web_page`**: Extracts clean, readable Markdown from any technical article or URL.

2. **PDF to LaTeX Decomposition:**
   - **`decompose_paper_to_latex`**: Parses PDF papers using PyMuPDF and breaks them into modular files:
     - `sections/00_abstract.tex`
     - `sections/01_introduction.tex`
     - `sections/02_methodology.tex`
     - `sections/03_results.tex`
     - `sections/04_conclusion.tex`
     - `main.tex` & `references.bib`

3. **Academic Translation with Math & Citation Protection:**
   - **`translate_academic_latex`**: Safely masks all mathematical formulas (`$...$`, `$$...$$`, `\begin{equation}`), citations (`\cite{...}`), and references (`\ref{...}`) before translating prose into Uzbek. After translation, restores all math and tags with 100% precision.

4. **Document Reassembly:**
   - **`reassemble_latex_document`**: Assembles multiple section files into a clean, complete master LaTeX document with a publication-grade preamble and bibliography links.

5. **Auditing & Self-Healing Auto-Fixer:**
   - **`audit_and_verify_latex`**: Checks math mode balance (unmatched `$`), environment closures, unescaped characters, and missing BibTeX keys.
   - **`auto_fix_latex_errors`**: Parses Tectonic compilation logs and automatically injects missing packages (`amsmath`, `amssymb`, `hyperref`, `booktabs`), escapes prose characters (`%`, `_`), repairs syntax, and recompiles.

6. **Small Model Self-Correction Engine:**
   - **Fallback Tool-Call Extractor**: Automatically captures tool calls if smaller models output JSON in text/markdown instead of the native API format.
   - **Targeted Self-Correction Guidance**: When a tool produces an error, the engine provides diagnostic hints so smaller models self-correct instead of getting stuck in loops.

7. **BibTeX Citation Ledger & Tectonic Compiler:**
   - **`manage_bibtex`**: Maintains and searches `references.bib`.
   - **`compile_latex`**: Fast local PDF compilation using `tools/tectonic.exe`.

---

## 🚀 Quick Start

### 1. Launch Research CLI (Terminal)

```powershell
Set-Location D:\Researcher
.\agent.ps1
```

### 2. Launch Modern Web GUI (Next.js 16 + FastAPI)

```powershell
Set-Location D:\Researcher
.\start_gui.ps1
```

- **Backend:** FastAPI on `http://127.0.0.1:8765` with real-time SSE streaming.
- **Frontend:** Next.js dark-mode UI on `http://localhost:3000`.

### 3. Run 11-Step Automated Verification Suite

```powershell
.\.venv\Scripts\python.exe test_research_agent.py
```

---

## 🛠️ Complete Research Tools Reference

| Tool Name | Category | Purpose | Example Input |
| :--- | :--- | :--- | :--- |
| `search_arxiv` | Discovery | Search arXiv for preprints & abstracts | `query: "quantum computing error correction"` |
| `search_web` | Discovery | Live web search via DuckDuckGo | `query: "DeepSeek-R1 technical architecture"` |
| `fetch_web_page` | Extraction | Fetch webpage and convert to Markdown | `url: "https://example.com/article"` |
| `download_paper` | Ingestion | Direct paper download to `outputs/papers/` | `identifier_or_url: "2301.12345"` |
| `download_and_extract_paper` | Extraction | Download & extract pages/TOC outline | `pdf_url_or_path: "paper.pdf"` |
| `decompose_paper_to_latex` | Decomposition | Split PDF into modular `sections/*.tex` | `pdf_path: "outputs/papers/sample.pdf"` |
| `translate_academic_latex` | Translation | Translate to Uzbek preserving math & citations | `content_or_file: "sections/01_intro.tex"` |
| `reassemble_latex_document` | Assembly | Merge modular sections into `main.tex` | `sections_dir: "sections", title: "..."` |
| `audit_and_verify_latex` | Auditing | Audit math balance, brackets & citations | `tex_file: "main.tex"` |
| `auto_fix_latex_errors` | Self-Healing | Auto-repair missing packages/syntax | `tex_file: "main.tex"` |
| `manage_bibtex` | Bibliography | Add, list, or search BibTeX citations | `action: "add", bibtex_entry: "@article{...}"` |
| `compile_latex` | Publishing | Compile LaTeX `.tex` to PDF via Tectonic | `tex_file: "main.tex"` |
| `extract_pdf_page` | Inspection | Extract text, tables & blocks from page | `pdf_file: "paper.pdf", page_number: 1` |
| `run_shell_command` | Data Analysis | Run Python / shell scripts & calculations | `command: "python plot_results.py"` |
| `update_plan` | Planning | Track milestones in multi-step research | `steps: [...], current_step: 1` |

---

## 🖥️ Desktop Application (Tauri 2.0)

Inside `frontend/`:
```powershell
npm run build
npx @tauri-apps/cli dev
```
To build a standalone `.exe` installer:
```powershell
npx @tauri-apps/cli build
```
