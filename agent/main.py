"""
CLI entry point for the Agentic Triage Assistant.
"""

import os
import sys

import click
import structlog
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt

from agent.config import get_settings
from agent.orchestrator import TriageAgent

console = Console()
settings = get_settings()

@click.group()
def cli():
    """Agentic Triage Assistant - Automated incident investigation."""
    pass

@cli.command()
@click.option("--demo", is_flag=True, help="Run in demo mode (no API keys required)")
def triage(demo: bool):
    """Start an interactive triage session."""
    if demo:
        os.environ["DEMO_MODE"] = "true"
        console.print("[yellow]Running in Demo Mode (Mock tools & LLM responses)[/yellow]")
    
    agent = TriageAgent()
    
    console.print(Panel.fit("[bold red]Agentic Triage Assistant[/bold red]\nType 'exit' to quit."))
    
    while True:
        try:
            query = Prompt.ask("\n[bold cyan]Describe Incident>[/bold cyan]")
            if query.lower() in ('exit', 'quit'):
                break
            if not query.strip():
                continue
                
            with console.status("[bold green]Agent investigating...[/bold green]"):
                result = agent.triage(query)
            
            # Print Observations
            console.print("\n[bold yellow]Agent Action Trace:[/bold yellow]")
            for obs in result["observations"]:
                console.print(f"[dim]{obs}[/dim]")
                
            # Print Safety Status
            safe_status = "[green]✓ Verified Grounded[/green]" if result["is_safe"] else "[red]⚠ Validation Warning[/red]"
            console.print(f"\n[bold]Output Safety:[/bold] {safe_status}")
            
            # Print Final Triage Result
            console.print("\n[bold magenta]Triage Report>[/bold magenta]")
            console.print(Markdown(result["triage_result"]))
                    
        except KeyboardInterrupt:
            break
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {e}")

if __name__ == "__main__":
    cli()
