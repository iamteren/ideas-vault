#!/usr/bin/env python3
import sys, uuid, json, boto3

REGION     = "us-east-1"
MODEL_ID   = "amazon.nova-pro-v1:0"
LAMBDA_ARN = "arn:aws:lambda:us-east-1:552533871472:function:ideas-tools"

bedrock = boto3.client("bedrock-runtime", region_name=REGION)
lamb    = boto3.client("lambda", region_name=REGION)

BANNER = """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Ideas Vault Organizer  |  Powered by Bedrock Nova Pro
  Type your message. Type  exit  to quit.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

TOOLS = [
    {"toolSpec": {"name": "get_idea",        "description": "Retrieve a full idea row from ideas.md by idea number", "inputSchema": {"json": {"type": "object", "properties": {"idea_id": {"type": "string"}}, "required": ["idea_id"]}}}},
    {"toolSpec": {"name": "get_progress",    "description": "Get progress status and artifact list for an idea",     "inputSchema": {"json": {"type": "object", "properties": {"idea_id": {"type": "string"}}, "required": ["idea_id"]}}}},
    {"toolSpec": {"name": "update_progress", "description": "Update progress status and optionally add a note",       "inputSchema": {"json": {"type": "object", "properties": {"idea_id": {"type": "string"}, "status": {"type": "string"}, "note": {"type": "string"}}, "required": ["idea_id", "status"]}}}},
    {"toolSpec": {"name": "save_artifact",   "description": "Save a drafted artifact to S3",                         "inputSchema": {"json": {"type": "object", "properties": {"idea_id": {"type": "string"}, "artifact_type": {"type": "string"}, "content": {"type": "string"}}, "required": ["idea_id", "artifact_type", "content"]}}}},
    {"toolSpec": {"name": "list_artifacts",  "description": "List all artifacts saved for an idea",                  "inputSchema": {"json": {"type": "object", "properties": {"idea_id": {"type": "string"}}, "required": ["idea_id"]}}}},
    {"toolSpec": {"name": "get_artifact",    "description": "Retrieve content of a saved artifact",                  "inputSchema": {"json": {"type": "object", "properties": {"idea_id": {"type": "string"}, "artifact_type": {"type": "string"}}, "required": ["idea_id", "artifact_type"]}}}}
]

def load_prompt():
    with open("/home/cloudshell-user/ideas-vault/idea_organizer_prompt.txt") as f:
        return f.read().strip()

def call_tool(name, tool_input):
    payload = {
        "actionGroup": "ideas-tools",
        "function": name,
        "parameters": [{"name": k, "type": "string", "value": str(v)} for k, v in tool_input.items()]
    }
    resp = lamb.invoke(FunctionName=LAMBDA_ARN, Payload=json.dumps(payload).encode())
    result = json.loads(resp["Payload"].read())
    return result.get("response", {}).get("functionResponse", {}).get("responseBody", {}).get("TEXT", {}).get("body", "{}")

def invoke(messages):
    system = [{"text": load_prompt()}]
    while True:
        resp = bedrock.converse(
            modelId=MODEL_ID,
            system=system,
            messages=messages,
            toolConfig={"tools": TOOLS}
        )
        msg    = resp["output"]["message"]
        reason = resp["stopReason"]
        messages.append(msg)

        if reason == "end_turn":
            # Extract text from response
            for block in msg.get("content", []):
                if "text" in block:
                    return block["text"], messages
            return "", messages

        if reason == "tool_use":
            tool_results = []
            for block in msg.get("content", []):
                if "toolUse" in block:
                    tu      = block["toolUse"]
                    result  = call_tool(tu["name"], tu["input"])
                    tool_results.append({
                        "toolResult": {
                            "toolUseId": tu["toolUseId"],
                            "content": [{"text": result}]
                        }
                    })
            messages.append({"role": "user", "content": tool_results})

def main():
    print(BANNER)
    messages = []

    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        opening = f"I want to work on idea #{sys.argv[1]}"
        print(f"You: {opening}\n")
        messages.append({"role": "user", "content": [{"text": opening}]})
    else:
        opening = "Show me a summary of my ideas and ask which one I want to work on."
        messages.append({"role": "user", "content": [{"text": opening}]})

    reply, messages = invoke(messages)
    print(f"Agent: {reply}\n")

    while True:
        try:
            user = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break
        if user.lower() in ("exit", "quit", "bye"):
            print("Goodbye.")
            break
        if not user:
            continue
        messages.append({"role": "user", "content": [{"text": user}]})
        reply, messages = invoke(messages)
        print(f"\nAgent: {reply}\n")

if __name__ == "__main__":
    main()
