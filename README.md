# Ideas Vault CLI

A personal CLI idea repository backed by AWS S3.

## Setup
1. Create an S3 bucket and set `IDEAS_BUCKET` in your `~/.bashrc`
2. Copy `view_table.py` to `~/view_table.py`
3. Add the shell functions from `bashrc_snippet.sh` to your `~/.bashrc`

## Commands
| Command | Description |
|---|---|
| `show-ideas` | Pull from S3 and render the full table |
| `show-prompt <#>` | Show the full 30-Day Launch Prompt for an idea |
| `pull-ideas` | Sync S3 → local ideas.md |
| `push-ideas` | Sync local ideas.md → S3 |
| `bulk-add-ideas` | Process bulk.txt and push to S3 |
