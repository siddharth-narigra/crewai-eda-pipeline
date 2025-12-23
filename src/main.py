"""
CLI Entry Point for the Explainable Multi-Agent EDA System
"""

import argparse
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from src.utils.file_handler import load_dataset, validate_file, ensure_output_dirs
from src.crew.eda_crew import EDACrew


console = Console()


def print_banner():
    """Print the application banner."""
    banner = """
    ╔═══════════════════════════════════════════════════════════════╗
    ║     🔍 Explainable Multi-Agent EDA System                     ║
    ║     Automated Data Analysis with AI-Powered Insights          ║
    ╚═══════════════════════════════════════════════════════════════╝
    """
    console.print(Panel(banner, style="bold blue"))


def print_summary(result: dict):
    """Print the analysis summary."""
    console.print("\n")
    console.print(Panel("✅ Analysis Complete!", style="bold green"))
    
    # Output files table
    table = Table(title="Generated Files", show_header=True, header_style="bold cyan")
    table.add_column("File Type", style="dim")
    table.add_column("Path")
    
    output_dir = result.get("output_dir", "output")
    
    table.add_row("Cleaned Data", f"{output_dir}/cleaned_data.csv")
    table.add_row("Markdown Report", f"{output_dir}/report.md")
    table.add_row("HTML Report", f"{output_dir}/report.html")
    table.add_row("Visualizations", f"{output_dir}/charts/")
    
    console.print(table)
    
    # Changelog
    changelog = result.get("changelog", [])
    if changelog:
        console.print("\n[bold]Data Transformations Applied:[/bold]")
        for i, change in enumerate(changelog, 1):
            console.print(f"  {i}. {change}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Explainable Multi-Agent EDA System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python src/main.py data.csv
  python src/main.py data.xlsx --output results
        """
    )
    
    parser.add_argument(
        "file",
        type=str,
        help="Path to the CSV or Excel file to analyze"
    )
    
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="output",
        help="Output directory for reports and charts (default: output)"
    )
    
    args = parser.parse_args()
    
    # Print banner
    print_banner()
    
    # Validate file
    console.print(f"\n📁 Loading: [cyan]{args.file}[/cyan]")
    
    is_valid, message = validate_file(args.file)
    if not is_valid:
        console.print(f"[red]Error:[/red] {message}")
        sys.exit(1)
    
    # Load dataset
    df = load_dataset(args.file)
    if df is None:
        console.print("[red]Failed to load dataset. Exiting.[/red]")
        sys.exit(1)
    
    # Create output directories
    ensure_output_dirs(args.output)
    
    # Run EDA
    console.print("\n🤖 Starting Multi-Agent Analysis...\n")
    console.print("[dim]This may take a few minutes depending on dataset size.[/dim]\n")
    
    try:
        crew = EDACrew(output_dir=args.output)
        result = crew.run(df)
        
        # Print summary
        print_summary(result)
        
        console.print("\n[bold green]Analysis complete![/bold green]")
        console.print(f"Open [cyan]{args.output}/report.html[/cyan] in your browser to view the full report.\n")
        
    except ValueError as e:
        console.print(f"\n[red]Configuration Error:[/red] {str(e)}")
        console.print("[dim]Please make sure you have set up your .env file with OPENROUTER_API_KEY[/dim]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]Error during analysis:[/red] {str(e)}")
        console.print("[dim]Check your API key and network connection.[/dim]")
        raise


if __name__ == "__main__":
    main()
