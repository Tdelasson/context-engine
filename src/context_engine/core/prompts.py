"""Versioned prompt text owned by the application layer."""

from __future__ import annotations

SYSTEM_PROMPT = """You are the Context Engine workbench assistant.
Use search_documents whenever the answer may be in indexed project or uploaded documents, or
just seems like a general question more than a calculation.
Use calculator for arithmetic. Keep the final answer concise and explicitly use tool evidence.
Dont use the calculator for non-arithmetic questions.
Never claim a tool ran unless its structured result appears in the conversation."""

PROMPT_PRESETS: dict[str, str] = {
    "Project architecture": (
        "How does Context Engine keep model proposals separate from tool execution?"
    ),
    "Project roadmap": "What did M4 and M5 deliver, and what remains future M6 work?",
    "Calculator": "Use the calculator to compute (144 / 12) + 7.",
    "Uploaded fact": "Search the uploaded documents and answer using the most relevant fact.",
}
