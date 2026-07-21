"""Estilos adicionais do modo de alto contraste."""

from __future__ import annotations

__all__ = ["HIGH_CONTRAST_CSS"]

HIGH_CONTRAST_CSS = '\n<style>\n    :root {\n        --navy-950: #000000;\n        --navy-900: #000000;\n        --navy-800: #111111;\n        --slate-500: #E5E7EB;\n        --slate-400: #F3F4F6;\n        --slate-300: #FFFFFF;\n        --white: #FFFFFF;\n        --gold: #FFF200;\n        --green: #7CFF6B;\n        --orange: #FFD166;\n        --red: #FF7B7B;\n        --blue: #7DD3FC;\n        --color-focus: #00E5FF;\n    }\n    .stApp { background: #000000 !important; color: #FFFFFF !important; }\n    .player-card-pitch, .bench-card, .tactical-list-item,\n    .summary-card, .profile-card, .market-card, .legend-box,\n    .evaluation-meta-card, .kpi-card, .contract-item {\n        background: #000000 !important;\n        border-width: 3px !important;\n    }\n    .project-subtitle, .project-hero-subtitle, .profile-secondary,\n    .market-label, .bench-club, .tactical-list-slot, .kpi-context,\n    .contract-term, .section-subtitle {\n        color: #FFFFFF !important;\n    }\n    .project-trophy, .section-eyebrow { color: #FFF200 !important; }\n    .world-cup-trophy .trophy-detail { stroke: #000000 !important; }\n    a { text-decoration: underline !important; text-decoration-thickness: 2px !important; }\n</style>\n'
