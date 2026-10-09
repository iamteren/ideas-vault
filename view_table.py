import sys
from rich.table import Table
from rich.console import Console
from rich import box

def parse_table(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = [l.strip() for l in f.readlines() if l.strip()]
    except FileNotFoundError:
        print(f"Error: File {file_path} not found.")
        return None, None

    table_lines = [l for l in lines if l.startswith('|')]
    if len(table_lines) < 2:
        print("No valid markdown table found.")
        return None, None

    headers = [c.strip() for c in table_lines[0].split('|')[1:-1]]
    rows = []
    for row in table_lines[2:]:
        rows.append([c.strip() for c in row.split('|')[1:-1]])

    return headers, rows

def show_table(file_path):
    headers, rows = parse_table(file_path)
    if not headers:
        return
    if not rows:
        print("The idea vault is currently empty.")
        return

    # Show all columns EXCEPT the last one (30-Day Launch Prompt)
    display_headers = headers[:-1]
    display_rows = [r[:-1] for r in rows]

    table = Table(
        box=box.SIMPLE_HEAVY,
        show_header=True,
        header_style="bold cyan",
        border_style="bright_blue",
        row_styles=["", "dim"],
        show_lines=True,
        expand=False,
        padding=(0, 1)
    )

    col_config = [
        {"style": "bold white",  "min_width": 3,  "max_width": 3,  "no_wrap": True},
        {"style": "bold green",  "min_width": 26, "max_width": 26, "no_wrap": False},
        {"style": "cyan",        "min_width": 26, "max_width": 26, "no_wrap": False},
        {"style": "white",       "min_width": 26, "max_width": 26, "no_wrap": False},
        {"style": "white",       "min_width": 26, "max_width": 26, "no_wrap": False},
        {"style": "magenta",     "min_width": 26, "max_width": 26, "no_wrap": False},
    ]

    for idx, header in enumerate(display_headers):
        cfg = col_config[idx] if idx < len(col_config) else {"style": "white", "min_width": 20, "max_width": 20, "no_wrap": False}
        table.add_column(
            header,
            style=cfg["style"],
            min_width=cfg["min_width"],
            max_width=cfg["max_width"],
            no_wrap=cfg["no_wrap"]
        )

    for row in display_rows:
        while len(row) < len(display_headers):
            row.append("")
        table.add_row(*row)

    console = Console()
    console.print(table)
    console.print("[dim]Tip: run [bold]show-prompt <#>[/bold] to see the full 30-Day Launch Prompt for any idea.[/dim]")

def show_prompt(file_path, idea_num):
    headers, rows = parse_table(file_path)
    if not headers:
        return

    for row in rows:
        if row and row[0].strip() == str(idea_num):
            console = Console()
            console.print(f"\n[bold cyan]Idea #{idea_num} — {row[1]}[/bold cyan]")
            console.print(f"[dim]Behavioral Principle:[/dim] [cyan]{row[2]}[/cyan]\n")
            console.print(f"[bold yellow]30-Day Launch Prompt:[/bold yellow]")
            console.print(f"[white]{row[6] if len(row) > 6 else 'No prompt found.'}[/white]\n")
            return

    print(f"No idea found with # {idea_num}")

if __name__ == "__main__":
    file = sys.argv[1] if len(sys.argv) > 1 else "ideas.md"
    mode = sys.argv[2] if len(sys.argv) > 2 else "table"
    num  = sys.argv[3] if len(sys.argv) > 3 else None

    if mode == "prompt" and num:
        show_prompt(file, num)
    else:
        show_table(file)
