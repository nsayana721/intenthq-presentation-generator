"""Prompts for LLM agents."""

from pathlib import Path

PROMPTS_DIR = Path(__file__).parent

def load_prompt(filename: str) -> str:
    """Load prompt from file."""
    filepath = PROMPTS_DIR / filename
    if not filepath.exists():
        raise FileNotFoundError(f"Prompt file not found: {filename}")
    return filepath.read_text(encoding='utf-8')

__all__ = ["load_prompt", "PROMPTS_DIR"]