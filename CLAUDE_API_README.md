# Using CLAUDE.md with the Claude API (example)

Quick steps:

1. Set environment variables:

```bash
export CLAUDE_API_KEY="your_api_key"
export CLAUDE_API_URL="https://api.your-claude-provider.example/v1/chat"
# optional: export CLAUDE_MODEL="claude-v1"
```

2. Run the example script (from project root):

```bash
python scripts/claude_api_example.py "ช่วยอธิบาย login_view ใน store/views.py ว่าทำงานอย่างไร"
```

3. If your provider uses a different request/response shape (e.g., Anthropic), adapt `scripts/claude_api_example.py`:

- replace `build_payload()` to form the expected JSON body
- parse the provider's response structure (e.g., `completion` or `completion.content`)

Security note:
- เก็บคีย์ใน environment variables หรือ secret manager; อย่า commit ลงใน repo
