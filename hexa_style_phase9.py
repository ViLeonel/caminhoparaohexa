"""Ajustes visuais das seções sazonais da ficha individual."""

from __future__ import annotations

__all__ = ["PHASE9_CSS"]

PHASE9_CSS = """
<style>
    [data-testid="stTabs"] {
        margin-top: .5rem;
    }

    [data-testid="stTabs"] [role="tablist"] {
        gap: .35rem;
        overflow-x: auto;
        padding-bottom: .25rem;
        scrollbar-width: thin;
    }

    [data-testid="stTabs"] button[role="tab"] {
        min-height: 44px;
        border-radius: .65rem;
        padding-inline: .85rem;
        white-space: nowrap;
    }

    [data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
        background: rgba(234, 179, 8, .12);
        color: var(--white);
    }

    [data-testid="stTabs"] [role="tabpanel"] {
        padding-top: .65rem;
    }

    @media (max-width: 768px) {
        [data-testid="stTabs"] [role="tablist"] {
            margin-inline: -.25rem;
            padding-inline: .25rem;
        }

        [data-testid="stTabs"] button[role="tab"] {
            font-size: .875rem;
        }
    }

    @media (prefers-reduced-motion: reduce) {
        [data-testid="stTabs"] button[role="tab"] {
            transition: none !important;
        }
    }
</style>
"""
