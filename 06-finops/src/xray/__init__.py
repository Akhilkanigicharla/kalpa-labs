"""LLM Bill X-ray generator (F-06, roadmap A30): usage export -> 2-page HTML (and PDF)."""
from .report import build
from .render import render

__all__ = ["build", "render"]
