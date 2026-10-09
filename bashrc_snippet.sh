# --- PERSONAL CLI IDEA ENGINE CONFIG ---
export IDEAS_BUCKET="yourname-ideas-vault-2026"

function pull-ideas() {
    aws s3 cp s3://$IDEAS_BUCKET/ideas.md ./ideas.md > /dev/null 2>&1
}

function push-ideas() {
    aws s3 cp ./ideas.md s3://$IDEAS_BUCKET/ideas.md > /dev/null 2>&1
    echo "S3 Cloud Database Updated Successfully!"
}

function show-ideas() {
    pull-ideas
    python3 ~/view_table.py ./ideas.md
}

function show-prompt() {
    if [ -z "$1" ]; then
        echo "Usage: show-prompt <idea number>"
        return 1
    fi
    pull-ideas
    python3 ~/view_table.py ./ideas.md prompt $1
}

function bulk-add-ideas() {
    if [ ! -f "bulk.txt" ]; then
        echo "Error: Create a bulk.txt file containing your raw data first."
        return 1
    fi
    pull-ideas
    while IFS=$'\t' read -r num concept principle offer poc moat prompt || [ -n "$num" ]; do
        if [[ "$num" == "#"* ]] || [[ -z "$concept" ]]; then continue; fi
        concept=$(echo "$concept" | tr '|' '-')
        principle=$(echo "$principle" | tr '|' '-')
        offer=$(echo "$offer" | tr '|' '-')
        poc=$(echo "$poc" | tr '|' '-')
        moat=$(echo "$moat" | tr '|' '-')
        prompt=$(echo "$prompt" | tr '|' '-' | sed 's/"//g')
        echo "| $num | $concept | $principle | $offer | $poc | $moat | $prompt |" >> ideas.md
    done < bulk.txt
    rm bulk.txt
    push-ideas
    echo "Bulk Import Completed!"
}
