"""
Core Autonomous Agent Engine (ReAct Execution Loop) with Stagnation Guard, Checkpoint Commit & Live Token Streaming
"""
import json
import re
from typing import Any, Callable, Dict, List, Optional, Tuple

from agent.checkpoint import checkpoint_manager
from agent.config import MAX_ITERATIONS
from agent.context import ContextManager
from agent.llm import OllamaClient
from agent.tools.registry import ToolRegistry


def extract_fallback_tool_calls(text: str) -> Optional[List[Dict[str, Any]]]:
    """
    Recovers tool calls written by smaller local models directly into text/markdown
    when native API tool-calling wasn't formatted properly.
    """
    if not text:
        return None

    # Check for markdown code blocks containing JSON
    json_blocks = re.findall(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", text)
    if not json_blocks:
        # Check for raw JSON object with name/arguments
        raw_match = re.search(r"(\{\s*\"(?:name|function)\"\s*:[\s\S]*?\})", text)
        if raw_match:
            json_blocks = [raw_match.group(1)]

    extracted = []
    for block in json_blocks:
        try:
            data = json.loads(block)
            if "name" in data and ("arguments" in data or "parameters" in data):
                extracted.append({
                    "id": f"fallback_{data['name']}",
                    "function": {
                        "name": data["name"],
                        "arguments": data.get("arguments") or data.get("parameters", {}),
                    }
                })
            elif "function" in data and isinstance(data["function"], dict):
                fn = data["function"]
                if "name" in fn:
                    extracted.append({
                        "id": f"fallback_{fn['name']}",
                        "function": {
                            "name": fn["name"],
                            "arguments": fn.get("arguments", {}),
                        }
                    })
        except Exception:
            # Tolerant cleanup for trailing commas and single quotes
            try:
                repaired = re.sub(r",\s*\}", "}", block)
                repaired = re.sub(r",\s*\]", "]", repaired)
                repaired = repaired.replace("'", '"')
                data = json.loads(repaired)
                if "name" in data:
                    extracted.append({
                        "id": f"fallback_{data['name']}",
                        "function": {
                            "name": data["name"],
                            "arguments": data.get("arguments", {}),
                        }
                    })
            except Exception:
                continue

    return extracted if extracted else None


class Agent:
    def __init__(
        self,
        llm: OllamaClient,
        tools: ToolRegistry,
        context: Optional[ContextManager] = None,
        max_iterations: int = MAX_ITERATIONS,
    ):
        self.llm = llm
        self.tools = tools
        self.context = context or ContextManager()
        self.max_iterations = max_iterations

    def run(
        self,
        user_prompt: str,
        on_thinking: Optional[Callable[[str], None]] = None,
        on_thinking_chunk: Optional[Callable[[str], None]] = None,
        on_content_chunk: Optional[Callable[[str], None]] = None,
        on_tool_call: Optional[Callable[[str, Dict[str, Any]], None]] = None,
        on_tool_result: Optional[Callable[[str, str], None]] = None,
        on_message: Optional[Callable[[str], None]] = None,
        on_cost_update: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_progress: Optional[Callable[[str], None]] = None,
        cancel_event: Optional[Any] = None,
    ) -> str:
        """
        Runs the autonomous ReAct agent loop until task completion, max_iterations, or user cancellation.
        Streams thinking chunks and content chunks live to the client in real-time.
        """
        self.context.add_user_message(user_prompt)

        iteration = 0
        final_answer = ""
        tools_used: List[str] = []

        friendly_tool_labels = {
            "search_arxiv": "🔬 arXiv ilmiy bazasidan maqolalar qidirilmoqda...",
            "search_crossref": "🌐 CrossRef xalqaro jurnallaridan iqtiboslar bilan qidirilmoqda...",
            "search_europepmc": "🧬 Europe PMC / PubMed tibbiyot bazasidan qidirilmoqda...",
            "search_web": "🌐 Internetdan ilmiy ma'lumotlar qidirilmoqda...",
            "fetch_web_page": "📖 Veb maqola matni yuklab olinmoqda...",
            "download_paper": "📥 Ilmiy PDF maqola yuklab olinmoqda...",
            "download_and_extract_paper": "📑 Maqola yuklab olinib, matni tahlil qilinmoqda...",
            "decompose_paper_to_latex": "✂️ Maqola mustaqil LaTeX modullariga (sections/) ajratilmoqda...",
            "translate_academic_latex": "🔤 Formulalarni saqlagan holda o'zbek tiliga akademik tarjima qilinmoqda...",
            "reassemble_latex_document": "📐 Bo'limlar yagona LaTeX master hujjatiga yig'ilmoqda...",
            "audit_and_verify_latex": "🔍 LaTeX formulalari va sintaksisi tekshirilmoqda...",
            "auto_fix_latex_errors": "🛠 LaTeX xatoliklari avtomatik tuzatilmoqda...",
            "manage_bibtex": "📚 BibTeX iqtiboslar bazasi yangilanmoqda...",
            "compile_latex": "⚡ Tectonic orqali nashrga tayyor PDF kompilatsiya qilinmoqda...",
            "export_latex_to_docx": "📝 Microsoft Word (.docx) formatiga eksport qilinmoqda...",
            "verify_claims_against_sources": "🛡 Da'volar asl manba PDF bilan kross-tekshirilmoqda...",
            "run_deep_research": "🚀 Avtonom Deep Research: adabiyotlar tahlili va maqola yaratilmoqda...",
            "write_file": "✍ Loyihaga fayl yozilmoqda...",
            "edit_file": "⚡ Fayl tahrirlanmoqda...",
            "read_file": "📄 Fayl o'qilmoqda...",
            "list_directory": "📂 Fayllar ro'yxati ko'rilmoqda...",
        }

        if on_progress:
            on_progress("🧠 Model so'rovni tahlil qilmoqda va ilmiy fikrlashni boshlamoqda...")

        # Stagnation tracking: (tool_name, args_hash, is_error)
        tool_call_history: List[Tuple[str, str, bool]] = []
        consecutive_stagnation_count = 0

        while iteration < self.max_iterations:
            if cancel_event and cancel_event.is_set():
                final_answer = "⏹️ Task was stopped by the user."
                if on_message:
                    on_message(final_answer)
                break

            iteration += 1

            if on_progress and iteration > 1:
                on_progress(f"🤔 Fikr yuritilmoqda (Qadam {iteration}/{self.max_iterations})...")

            # Prepare schemas and messages
            tool_schemas = self.tools.get_schemas()
            messages = self.context.get_messages_for_llm()

            # Query LLM with real-time streaming
            response = self.llm.chat_stream(
                messages=messages,
                tools=tool_schemas,
                on_thinking_chunk=on_thinking_chunk,
                on_content_chunk=on_content_chunk,
            )

            # Fire token & cost callback
            if on_cost_update:
                on_cost_update({
                    "prompt_tokens": response.get("prompt_tokens", 0),
                    "completion_tokens": response.get("completion_tokens", 0),
                    "total_tokens": response.get("total_tokens", 0),
                    "cost_usd": response.get("cost_usd", 0.0),
                })


            content = response.get("content", "")
            thinking = response.get("thinking", None)
            tool_calls = response.get("tool_calls", None)

            # Fallback tool call extraction for smaller local models (7B/8B/14B)
            # that output JSON directly into text instead of standard API tool_calls
            if not tool_calls and content:
                extracted = extract_fallback_tool_calls(content)
                if extracted:
                    tool_calls = extracted

            # Fire complete thinking callback if needed
            if thinking and on_thinking:
                on_thinking(thinking)

            # Check if tools were requested
            if tool_calls:
                # Add assistant message with tool calls to context
                self.context.add_assistant_message(
                    content=content,
                    thinking=thinking,
                    tool_calls=tool_calls
                )

                # Execute requested tools
                for tc in tool_calls:
                    if cancel_event and cancel_event.is_set():
                        final_answer = "⏹️ Task was stopped by the user."
                        if on_message:
                            on_message(final_answer)
                        break

                    fn_data = tc.get("function", {})
                    tool_name = fn_data.get("name", "")
                    tool_args = fn_data.get("arguments", {})
                    tool_call_id = tc.get("id")

                    tools_used.append(tool_name)

                    if on_progress:
                        status_msg = friendly_tool_labels.get(tool_name, f"⚙️ '{tool_name}' vositasi bajarilmoqda...")
                        on_progress(status_msg)

                    if on_tool_call:
                        on_tool_call(tool_name, tool_args)

                    # Checkpoint session for file tracking
                    checkpoint_desc = f"Action: {tool_name}({list(tool_args.keys())})"
                    checkpoint_manager.begin_checkpoint(checkpoint_desc)

                    # Execute tool
                    tool_output = self.tools.execute(tool_name, tool_args)

                    # Commit checkpoint if any file was changed
                    checkpoint_manager.commit_checkpoint()

                    if on_tool_result:
                        on_tool_result(tool_name, tool_output)

                    if on_progress:
                        on_progress(f"✓ '{tool_name}' natijasi olindi. Ma'lumotlar tahlil qilinmoqda...")

                    # Check if output is an error
                    is_err = tool_output.lower().startswith("error")

                    # Self-Correction Guidance for Small Local Models
                    if is_err:
                        tool_output += (
                            f"\n\n[💡 MODEL SELF-CORRECTION GUIDANCE: "
                            f"Tool '{tool_name}' returned an error. "
                            f"Do NOT repeat the exact same call with identical arguments. "
                            f"If LaTeX compilation failed, use 'auto_fix_latex_errors' or 'audit_and_verify_latex'. "
                            f"If a file was not found, inspect available files with 'list_directory'. "
                            f"Carefully adjust your parameters and self-correct.]"
                        )

                    # Add tool result to context
                    self.context.add_tool_result(
                        tool_name=tool_name,
                        result=tool_output,
                        tool_call_id=tool_call_id,
                    )

                    # Stagnation & Loop Guard
                    args_sig = json.dumps(tool_args, sort_keys=True)
                    if tool_call_history and tool_call_history[-1][:2] == (tool_name, args_sig):
                        consecutive_stagnation_count += 1
                    else:
                        consecutive_stagnation_count = 0

                    tool_call_history.append((tool_name, args_sig, is_err))

                    # If model repeats exact same call 2 times with error
                    if consecutive_stagnation_count >= 1 and is_err:
                        intervention = {
                            "role": "system",
                            "content": (
                                f"[⚠️ STAGNATION WARNING: You repeated '{tool_name}' with the exact same arguments and received an error. "
                                "Do NOT repeat this identical call. Stop, analyze why it failed, inspect surrounding context, "
                                "or use an alternative tool/approach.]"
                            )
                        }
                        self.context.messages.append(intervention)

                    # If model loops 3 times regardless of error
                    elif consecutive_stagnation_count >= 2:
                        intervention = {
                            "role": "system",
                            "content": (
                                f"[⚠️ INFINITE LOOP PREVENTED: You called '{tool_name}' 3 consecutive times without progress. "
                                "Proceed to the next step of your plan or provide your final response to the user.]"
                            )
                        }
                        self.context.messages.append(intervention)

                # Continue next iteration of ReAct loop
                continue

            else:
                # Final response reached (no tool calls)
                final_answer = content
                self.context.add_assistant_message(
                    content=final_answer,
                    thinking=thinking,
                    tool_calls=None
                )
                if on_message:
                    on_message(final_answer)

                # Auto-flush bloated context after task and preserve memory in ledger!
                self.context.finalize_task_and_flush(user_prompt, final_answer, tools_used)
                break

        if iteration >= self.max_iterations and not final_answer:
            final_answer = f"Agent reached maximum iteration limit ({self.max_iterations}) without final answer."
            if on_message:
                on_message(final_answer)
            self.context.finalize_task_and_flush(user_prompt, final_answer, tools_used)

        return final_answer
