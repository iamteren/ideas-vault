#!/usr/bin/env python3
"""
expand_idea.py  —  Reads a PENDING row from ideas.md, calls Bedrock Nova Micro
                   using the prompt in idea_agent_prompt.txt, and replaces the
                   row with the fully expanded version.

Usage:
    python3 ~/ideas-vault/expand_idea.py <idea_number> [path/to/ideas.md]
"""

import sys
import json

try:
    import boto3
except ImportError:
    print("ERROR: boto3 not available. Run this in AWS CloudShell.")
    sys.exit(1)

SCRIPT_DIR  = __file__.rsplit("/", 1)[0]
PROMPT_FILE = SCRIPT_DIR + "/idea_agent_prompt.txt"
MODEL_ID    = "amazon.nova-micro-v1:0"
REGION      = "us-east-1"

def load_system_prompt():
    try:
        with open(PROMPT_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"ERROR: Agent prompt file not found at {PROMPT_FILE}")
        sys.exit(1)

def load_ideas(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.readlines()
    except FileNotFoundError:
        print(f"ERROR: ideas.md not found at {path}")
        sys.exit(1)

def find_row(lines, idea_num):
    for i, line in enumerate(lines):
        if not line.strip().startswith("|"):
            continue
        cols = [c.strip() for c in line.split("|")[1:-1]]
        if len(cols) >= 2 and cols[0] == str(idea_num):
            return i, cols
    return None, None

def validate_output(raw):
    cleaned = raw.strip().strip("`").strip()
    if not cleaned.startswith("|") or not cleaned.endswith("|"):
        raise ValueError(f"Output is not a table row: {cleaned[:120]}")
    cols = [c.strip() for c in cleaned.split("|")[1:-1]]
    if len(cols) != 7:
        raise ValueError(f"Expected 7 fields, got {len(cols)}")
    return cols

def call_nova(system_prompt, seed_text):
    client = boto3.client("bedrock-runtime", region_name=REGION)
    body = {
        "system": [{"text": system_prompt}],
        "messages": [{"role": "user", "content": [{"text": seed_text}]}],
        "inferenceConfig": {
            "maxTokens": 1024,
            "temperature": 0.2,
            "topP": 0.9
        }
    }
    response = client.invoke_model(
        modelId=MODEL_ID,
        body=json.dumps(body),
        contentType="application/json",
        accept="application/json"
    )
    result = json.loads(response["body"].read())
    return result["output"]["message"]["content"][0]["text"].strip()

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 expand_idea.py <idea_number> [ideas.md path]")
        sys.exit(1)

    idea_num   = sys.argv[1]
    ideas_path = sys.argv[2] if len(sys.argv) > 2 else "./ideas.md"

    print(f"Loading agent prompt...")
    system_prompt = load_system_prompt()

    print(f"Reading {ideas_path}...")
    lines = load_ideas(ideas_path)

    idx, cols = find_row(lines, idea_num)
    if idx is None:
        print(f"ERROR: No row found with idea number {idea_num}")
        sys.exit(1)

    name      = cols[1] if len(cols) > 1 else ""
    principle = cols[2] if len(cols) > 2 else ""

    seed = f"{name} — {principle}" if principle and principle.upper() != "PENDING" else name

    print(f"Seed: {seed}")
    print(f"Calling Nova Micro...")

    raw = call_nova(system_prompt, seed)
    print(f"\nModel output:\n{raw}\n")

    try:
        expanded_cols = validate_output(raw)
    except ValueError as e:
        print(f"ERROR: Validation failed — {e}")
        print("ideas.md was NOT modified.")
        sys.exit(1)

    expanded_cols[0] = idea_num
    lines[idx] = "| " + " | ".join(expanded_cols) + " |\n"

    with open(ideas_path, "w", encoding="utf-8") as f:
        f.writelines(lines)

    print(f"Idea #{idea_num} expanded and saved.")

if __name__ == "__main__":
    main()
