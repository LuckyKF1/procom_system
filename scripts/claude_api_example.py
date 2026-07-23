#!/usr/bin/env python3
"""
Example: send CLAUDE.md as a `system` message before asking a question.

Usage:
  export CLAUDE_API_KEY=your_key_here
  export CLAUDE_API_URL=https://api.your-claude-provider.example/v1/chat
  python scripts/claude_api_example.py "ช่วยอธิบาย login_view ใน store/views.py"

Notes:
- Adapt `CLAUDE_API_URL` and payload shape to the Claude provider you use (Anthropic/Cloud vendor).
"""
import os
import sys
import json
import requests


def load_claude_md():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(root, "CLAUDE.md")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def build_payload(system_text: str, user_prompt: str):
    # Generic chat-style payload (OpenAI-like). Replace if your Claude API expects a different shape.
    return {
        "model": os.environ.get("CLAUDE_MODEL", "claude-v1"),
        "messages": [
            {"role": "system", "content": system_text},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.2,
    }


def main():
    api_key = os.environ.get("CLAUDE_API_KEY")
    api_url = os.environ.get("CLAUDE_API_URL")
    if not api_key or not api_url:
        print("Set CLAUDE_API_KEY and CLAUDE_API_URL environment variables.")
        sys.exit(1)

    if len(sys.argv) < 2:
        print("Usage: python scripts/claude_api_example.py \"your question\"")
        sys.exit(1)

    user_prompt = sys.argv[1]
    system_text = load_claude_md()

    payload = build_payload(system_text, user_prompt)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    resp = requests.post(api_url, headers=headers, json=payload, timeout=60)
    try:
        data = resp.json()
    except Exception:
        print("Non-JSON response:", resp.text)
        resp.raise_for_status()

    # Print result in a provider-agnostic way. Adjust based on your provider's response format.
    if isinstance(data, dict):
        # Common places where chat responses appear
        # Try popular keys: 'choices' (OpenAI-like), 'output' or 'completion'
        if "choices" in data and data["choices"]:
            print(data["choices"][0].get("message", {}).get("content") or data["choices"][0].get("text"))
        elif "completion" in data:
            print(data["completion"])
        elif "output" in data:
            print(data["output"])
        else:
            print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(data)


if __name__ == "__main__":
    main()
