import json
import boto3
from datetime import datetime, timezone

S3_BUCKET    = "iamteren-ideas-vault"
S3_KEY       = "ideas.md"
DYNAMO_TABLE = "ideas-progress"
REGION       = "us-east-1"

s3     = boto3.client("s3", region_name=REGION)
dynamo = boto3.resource("dynamodb", region_name=REGION)

def ts():
    return datetime.now(timezone.utc).isoformat()

def get_ideas_md():
    obj = s3.get_object(Bucket=S3_BUCKET, Key=S3_KEY)
    return obj["Body"].read().decode("utf-8")

def parse_idea_row(md, idea_id):
    for line in md.splitlines():
        if not line.strip().startswith("|"):
            continue
        cols = [c.strip() for c in line.split("|")[1:-1]]
        if len(cols) == 7 and cols[0] == str(idea_id):
            return {"id": cols[0], "concept": cols[1], "principle": cols[2],
                    "offer": cols[3], "poc": cols[4], "moat": cols[5], "prompt": cols[6]}
    return None

def get_table():
    return dynamo.Table(DYNAMO_TABLE)

def get_idea(params):
    idea = parse_idea_row(get_ideas_md(), params["idea_id"])
    return idea if idea else {"error": f"Idea #{params['idea_id']} not found"}

def get_progress(params):
    resp = get_table().get_item(Key={"idea_id": str(params["idea_id"])})
    item = resp.get("Item")
    return item if item else {"idea_id": str(params["idea_id"]), "status": "not_started", "notes": [], "artifacts": []}

def update_progress(params):
    table = get_table()
    expr  = "SET #s = :s, updated_at = :u"
    names = {"#s": "status"}
    vals  = {":s": params["status"], ":u": ts()}
    if params.get("note"):
        expr += ", notes = list_append(if_not_exists(notes, :empty), :n)"
        vals[":n"]     = [{"ts": ts(), "text": params["note"]}]
        vals[":empty"] = []
    table.update_item(Key={"idea_id": str(params["idea_id"])},
                      UpdateExpression=expr,
                      ExpressionAttributeNames=names,
                      ExpressionAttributeValues=vals)
    return {"idea_id": str(params["idea_id"]), "status": params["status"], "updated": True}

def save_artifact(params):
    key = f"artifacts/idea-{params['idea_id']}/{params['artifact_type']}.md"
    s3.put_object(Bucket=S3_BUCKET, Key=key,
                  Body=params["content"].encode("utf-8"), ContentType="text/markdown")
    get_table().update_item(
        Key={"idea_id": str(params["idea_id"])},
        UpdateExpression="SET artifacts = list_append(if_not_exists(artifacts, :empty), :a)",
        ExpressionAttributeValues={
            ":a":     [{"type": params["artifact_type"], "s3_key": key, "created_at": ts()}],
            ":empty": []
        }
    )
    return {"saved": True, "s3_key": key}

def list_artifacts(params):
    progress = get_progress(params)
    return {"idea_id": str(params["idea_id"]), "artifacts": progress.get("artifacts", [])}

def get_artifact(params):
    key = f"artifacts/idea-{params['idea_id']}/{params['artifact_type']}.md"
    try:
        obj = s3.get_object(Bucket=S3_BUCKET, Key=key)
        return {"content": obj["Body"].read().decode("utf-8")}
    except Exception:
        return {"error": "Artifact not found"}

ACTION_MAP = {
    "get_idea":        get_idea,
    "get_progress":    get_progress,
    "update_progress": update_progress,
    "save_artifact":   save_artifact,
    "list_artifacts":  list_artifacts,
    "get_artifact":    get_artifact,
}

def lambda_handler(event, context):
    print("EVENT:", json.dumps(event))
    action     = event.get("actionGroup", "")
    func       = event.get("function", "")
    params_raw = event.get("parameters", [])
    params     = {p["name"]: p["value"] for p in params_raw}
    handler    = ACTION_MAP.get(func)
    if not handler:
        result = {"error": f"Unknown function: {func}"}
    else:
        try:
            result = handler(params)
        except Exception as e:
            result = {"error": str(e)}
    return {
        "messageVersion": "1.0",
        "response": {
            "actionGroup": action,
            "function":    func,
            "functionResponse": {
                "responseBody": {"TEXT": {"body": json.dumps(result)}}
            }
        }
    }
