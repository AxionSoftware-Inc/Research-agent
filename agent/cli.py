"""
Interactive Claude Code / Codex Style Terminal Interface
"""
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from agent.config import DEFAULT_MODEL, OLLAMA_URL, WORKSPACE_DIR
from agent.context import ContextManager
from agent.engine import Agent
from agent.llm import OllamaClient
from agent.tools import create_default_registry


def print_banner(console: Console, model_name: str):
    header = (
        f"[bold cyan]⚡ LOCAL AUTONOMOUS CODING AGENT[/bold cyan] [dim](Claude Code & Codex Style)[/dim]\n"
        f"[dim]Model:[/] [bold yellow]{model_name}[/] [dim]| Workspace:[/] [bold green]{WORKSPACE_DIR}[/]\n"
        f"[dim]Commands:[/] [cyan]/help[/cyan], [cyan]/tools[/cyan], [cyan]/model[/cyan], [cyan]/context[/cyan], [cyan]/clear[/cyan], [cyan]/exit[/cyan]"
    )
    console.print(Panel(header, border_style="cyan", padding=(1, 2)))


def main():
    console = Console()
    llm = OllamaClient(base_url=OLLAMA_URL, model=DEFAULT_MODEL)
    registry = create_default_registry()
    context = ContextManager()
    agent = Agent(llm=llm, tools=registry, context=context)

    print_banner(console, llm.model)

    while True:
        try:
            console.print()
            user_input = console.input("[bold green]assistant> [/bold green]").strip()

            if not user_input:
                continue

            # Command Handling
            if user_input.startswith("/"):
                cmd_parts = user_input.split(maxsplit=1)
                cmd = cmd_parts[0].lower()
                arg = cmd_parts[1] if len(cmd_parts) > 1 else ""

                if cmd in ("/exit", "/quit"):
                    console.print("[dim]Goodbye![/dim]")
                    break

                elif cmd in ("/clear", "/reset"):
                    context.reset()
                    console.print("[yellow]✓ Conversation context cleared.[/yellow]")
                    continue

                elif cmd == "/context":
                    token_est = context.get_token_estimate()
                    msg_count = len(context.messages)
                    console.print(f"[cyan]Active messages:[/] {msg_count} | [cyan]Estimated tokens:[/] ~{token_est}")
                    continue

                elif cmd == "/tools":
                    table = Table(title="Available Tools", border_style="cyan")
                    table.add_column("Tool Name", style="bold green")
                    table.add_column("Description", style="dim")
                    for t in registry.list_tools():
                        table.add_row(t["name"], t["description"])
                    console.print(table)
                    continue

                elif cmd == "/model":
                    if arg:
                        llm.set_model(arg.strip())
                        console.print(f"[bold yellow]✓ Model switched to:[/] {llm.model}")
                    else:
                        models = llm.list_models()
                        console.print(f"[cyan]Current model:[/] [bold yellow]{llm.model}[/bold yellow]")
                        console.print(f"[cyan]Available models in Ollama:[/] {', '.join(models)}")
                        console.print("[dim]Usage: /model <model_name>[/dim]")
                    continue

                elif cmd == "/undo":
                    from agent.checkpoint import checkpoint_manager
                    res = checkpoint_manager.undo()
                    console.print(Panel(res, title="⏪ Rollback (Undo)", border_style="yellow"))
                    continue

                elif cmd == "/checkpoints":
                    from agent.checkpoint import checkpoint_manager
                    chks = checkpoint_manager.list_checkpoints()
                    if not chks:
                        console.print("[dim]No checkpoints recorded yet.[/dim]")
                    else:
                        table = Table(title="Recorded Checkpoints (Stack)", border_style="yellow")
                        table.add_column("ID", style="cyan")
                        table.add_column("Time", style="dim")
                        table.add_column("Description", style="bold green")
                        table.add_column("Touched Files", style="white")
                        for c in chks:
                            table.add_row(c["id"], c["time"], c["description"], ", ".join(c["files"]))
                        console.print(table)
                    continue

                elif cmd == "/plan":
                    from agent.tools.plan_tools import plan_tracker
                    console.print(Panel(plan_tracker.get_summary(), title="📋 Execution Plan", border_style="cyan"))
                    continue

                elif cmd == "/help":
                    help_text = (
                        "[bold cyan]Available Commands:[/bold cyan]\n"
                        "  [yellow]/undo[/yellow]             - Revert the latest file modification (Rollback)\n"
                        "  [yellow]/checkpoints[/yellow]      - List all snapshot checkpoints in history\n"
                        "  [yellow]/plan[/yellow]             - View active sub-goal execution plan\n"
                        "  [yellow]/tools[/yellow]            - List registered tools and capabilities\n"
                        "  [yellow]/model <name>[/yellow]     - Switch active model (e.g. /model gemma4-26b:latest)\n"
                        "  [yellow]/context[/yellow]          - Show context token estimation and memory status\n"
                        "  [yellow]/clear[/yellow]            - Reset conversation context\n"
                        "  [yellow]/exit[/yellow]             - Exit interactive session\n"
                    )
                    console.print(Panel(help_text, title="Help", border_style="yellow"))
                    continue

                else:
                    console.print(f"[red]Unknown command '{cmd}'. Type /help for available commands.[/red]")
                    continue

            # Run Agent
            def on_thinking(th: str):
                cleaned = th.strip()
                if cleaned:
                    console.print(Panel(Text(cleaned, style="italic dim white"), title="🤔 Reasoning", border_style="dim blue", padding=(0, 1)))

            def on_tool_call(name: str, args: dict):
                args_summary = ", ".join(f"{k}={repr(v)}" for k, v in args.items())
                if len(args_summary) > 120:
                    args_summary = args_summary[:117] + "..."
                console.print(f"[bold cyan]⚙ Calling Tool:[/] [bold green]{name}[/bold green]({args_summary})")

            def on_tool_result(name: str, result: str):
                summary = result.strip()
                lines = summary.splitlines()
                if len(lines) > 6:
                    preview = "\n".join(lines[:3]) + f"\n... [+{len(lines) - 5} more lines] ...\n" + lines[-1]
                else:
                    preview = summary
                console.print(Panel(Text(preview, style="dim white"), title=f"✓ Result: {name}", border_style="dim green", padding=(0, 1)))

            def on_message(final_text: str):
                console.print()
                console.print(Markdown(final_text))

            # Run ReAct Loop
            with console.status("[bold green]Agent thinking & executing...[/bold green]", spinner="dots"):
                agent.run(
                    user_prompt=user_input,
                    on_thinking=on_thinking,
                    on_tool_call=on_tool_call,
                    on_tool_result=on_tool_result,
                    on_message=on_message,
                )

        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted. Type /exit to quit.[/yellow]")
            continue
        except Exception as err:
            console.print(f"[bold red]Error:[/] {err}")


if __name__ == "__main__":
    main()
