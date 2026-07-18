"""Design system compartilhado do aplicativo."""

from __future__ import annotations

import streamlit as st

from hexa_config import PAGE_CONFIG

CSS = """
<style>
    :root {
        --navy-950: #020617;
        --navy-900: #0F172A;
        --navy-800: #1E293B;
        --slate-500: #64748B;
        --slate-400: #94A3B8;
        --slate-300: #CBD5E1;
        --white: #F8FAFC;
        --gold: #EAB308;
        --green: #22C55E;
        --orange: #F97316;
        --red: #EF4444;
        --blue: #3B82F6;
    }

    .stApp {
        background-color: var(--navy-900);
        color: var(--white);
        font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }

    .block-container {
        max-width: 1500px;
        padding-top: 1.5rem;
        padding-bottom: 3rem;
    }

    .app-title {
        text-align: center;
        font-size: clamp(2rem, 5vw, 3.2rem);
        font-weight: 800;
        line-height: 1.1;
        background: linear-gradient(135deg, var(--gold) 0%, var(--white) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0 0 .35rem;
    }

    .project-subtitle {
        color: var(--slate-400);
        font-size: clamp(.95rem, 2vw, 1.15rem);
        text-align: center;
        margin: 0 auto 1.75rem;
        max-width: 880px;
        line-height: 1.6;
    }

    .pitch-container {
        background-color: #14532D;
        background-image: linear-gradient(to bottom, #14532D 0%, #166534 100%);
        border: 4px solid var(--gold);
        border-radius: 20px;
        position: relative;
        width: 100%;
        height: 680px;
        overflow: hidden;
        box-shadow: 0 15px 35px rgba(0, 0, 0, .55);
        margin-bottom: 25px;
    }

    .pitch-line-center {
        position: absolute;
        top: 50%;
        left: 0;
        width: 100%;
        height: 2px;
        background-color: rgba(248, 250, 252, .35);
    }

    .pitch-circle {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 150px;
        height: 150px;
        border: 2px solid rgba(248, 250, 252, .35);
        border-radius: 50%;
    }

    .pitch-penalty-top,
    .pitch-penalty-bottom {
        position: absolute;
        left: 50%;
        transform: translateX(-50%);
        width: 280px;
        height: 100px;
        border-left: 2px solid rgba(248, 250, 252, .35);
        border-right: 2px solid rgba(248, 250, 252, .35);
    }

    .pitch-penalty-top {
        top: 0;
        border-bottom: 2px solid rgba(248, 250, 252, .35);
    }

    .pitch-penalty-bottom {
        bottom: 0;
        border-top: 2px solid rgba(248, 250, 252, .35);
    }

    .player-node {
        position: absolute;
        transform: translate(-50%, -50%);
        width: 135px;
        text-align: center;
        z-index: 10;
    }

    .player-card-pitch {
        background: rgba(2, 6, 23, .95);
        border: 2px solid var(--gold);
        border-radius: 9px;
        padding: 6px;
        box-shadow: 0 4px 10px rgba(0, 0, 0, .5);
    }

    .player-card-empty {
        border-color: var(--slate-500) !important;
        background: rgba(15, 23, 42, .82);
    }

    .player-pos-tag {
        color: var(--gold);
        font-size: .66rem;
        font-weight: 800;
        text-transform: uppercase;
    }

    .player-name-tag {
        color: var(--white);
        font-size: .78rem;
        font-weight: 700;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .player-rating-tag,
    .player-empty-tag {
        display: inline-block;
        font-size: .64rem;
        font-weight: 800;
        border-radius: 4px;
        padding: 2px 5px;
        margin-top: 3px;
    }

    .player-rating-tag {
        background-color: var(--gold);
        color: var(--navy-950);
    }

    .player-empty-tag {
        color: var(--slate-300);
        border: 1px solid var(--slate-500);
    }

    .legend-box,
    .summary-box,
    .profile-card,
    .market-card,
    .stat-box,
    .bench-box,
    .rating-box {
        background-color: var(--navy-950);
        border-radius: 14px;
        box-shadow: 0 4px 10px rgba(0, 0, 0, .3);
    }

    .legend-box {
        display: flex;
        justify-content: center;
        flex-wrap: wrap;
        gap: 16px;
        padding: 12px;
        margin: -10px 0 25px;
        border: 1px solid var(--navy-800);
    }

    .legend-item {
        display: flex;
        align-items: center;
        gap: 7px;
        color: var(--white);
        font-size: .82rem;
    }

    .legend-dot {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        flex: 0 0 auto;
    }

    .bench-box {
        border: 1px solid var(--navy-800);
        padding: 14px;
        margin-bottom: 22px;
    }

    .bench-grid {
        display: grid;
        grid-template-columns: repeat(5, minmax(125px, 1fr));
        gap: 10px;
    }

    .bench-card {
        border: 1px solid var(--navy-800);
        border-radius: 10px;
        padding: 10px;
        min-width: 0;
    }

    .bench-number {
        color: var(--gold);
        font-size: .68rem;
        font-weight: 800;
    }

    .bench-name {
        color: var(--white);
        font-size: .82rem;
        font-weight: 800;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .bench-club {
        color: var(--slate-400);
        font-size: .7rem;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .summary-box {
        padding: 18px;
        border-top: 4px solid var(--gold);
        margin-bottom: 22px;
    }

    .summary-grid {
        display: grid;
        grid-template-columns: repeat(6, minmax(105px, 1fr));
        gap: 12px;
        text-align: center;
    }

    .summary-label {
        color: var(--slate-400);
        font-size: .66rem;
        text-transform: uppercase;
        font-weight: 800;
        letter-spacing: .03em;
    }

    .summary-value {
        color: var(--white);
        font-size: 1.05rem;
        font-weight: 800;
        margin-top: 3px;
    }

    .summary-footnote {
        color: var(--slate-400);
        font-size: .72rem;
        text-align: center;
        margin-top: 12px;
    }

    .profile-card {
        padding: 24px;
        border: 3px solid var(--gold);
        text-align: center;
    }

    .profile-card h2 {
        color: var(--white);
        margin: 0 0 5px;
        font-size: clamp(1.6rem, 4vw, 2.2rem);
    }

    .profile-details {
        margin-top: 18px;
        color: var(--slate-300);
        text-align: left;
        line-height: 1.85;
        font-size: .9rem;
    }

    .rating-box {
        padding: 16px;
        border: 1px solid var(--navy-800);
    }

    .rating-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 10px;
    }

    .rating-card {
        background: var(--navy-900);
        border: 1px solid var(--navy-800);
        border-radius: 10px;
        padding: 12px 8px;
        text-align: center;
    }

    .rating-label {
        color: var(--slate-400);
        font-size: .72rem;
        font-weight: 800;
        text-transform: uppercase;
    }

    .rating-value {
        color: var(--white);
        font-size: 1.25rem;
        font-weight: 800;
        margin-top: 3px;
    }

    .rating-gold { color: var(--gold); }

    .rating-note {
        color: var(--slate-400);
        font-size: .72rem;
        text-align: center;
        margin-top: 10px;
    }

    .market-card {
        padding: 18px;
        border-left: 5px solid var(--gold);
        margin-bottom: 22px;
    }

    .market-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(120px, 1fr));
        gap: 14px;
        margin-bottom: 14px;
    }

    .market-label {
        color: var(--slate-400);
        font-size: .7rem;
        text-transform: uppercase;
        font-weight: 800;
    }

    .market-value {
        color: var(--white);
        font-size: 1.15rem;
        font-weight: 800;
        margin-top: 4px;
    }

    .market-value.gold { color: var(--gold); }
    .market-value.green { color: var(--green); }

    .progress-track {
        width: 100%;
        height: 12px;
        border-radius: 999px;
        background: var(--navy-800);
        overflow: hidden;
        margin: 8px 0 5px;
    }

    .progress-fill {
        height: 100%;
        border-radius: 999px;
        background: linear-gradient(90deg, var(--orange), var(--gold), var(--green));
    }

    .market-dates {
        color: var(--slate-400);
        font-size: .72rem;
        display: flex;
        justify-content: space-between;
        gap: 10px;
        flex-wrap: wrap;
    }

    .stat-box {
        padding: 18px;
        border-left: 6px solid var(--gold);
        margin-bottom: 14px;
        color: var(--slate-300);
        line-height: 1.6;
    }

    .stat-box strong { color: var(--white); }

    .sidebar-title {
        color: var(--gold);
        margin-top: 15px;
        text-align: center;
    }

    section[data-testid="stSidebar"] {
        background-color: var(--navy-950) !important;
    }

    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] label {
        color: var(--white) !important;
    }

    header[data-testid="stHeader"],
    #MainMenu,
    footer,
    .stDeployButton {
        display: none !important;
    }

    @media (max-width: 1100px) {
        .summary-grid { grid-template-columns: repeat(3, minmax(120px, 1fr)); }
        .bench-grid { grid-template-columns: repeat(3, minmax(120px, 1fr)); }
    }

    @media (max-width: 900px) {
        .pitch-container { height: min(620px, 72vh); }
        .tactical-list-grid { grid-template-columns: 1fr; }
        .player-node { width: 112px; }
        .player-name-tag { font-size: .68rem; }
        .player-rating-tag, .player-empty-tag { font-size: .57rem; }
        .market-grid { grid-template-columns: 1fr; }
    }

    @media (max-width: 600px) {
        .block-container { padding-left: .75rem; padding-right: .75rem; }
        .pitch-container {
            height: 540px;
            border-width: 3px;
            border-radius: 14px;
        }
        .tactical-list-section { padding: 10px; }
        .tactical-list-item {
            flex-direction: column;
            align-items: stretch;
            min-height: 76px;
        }
        .tactical-list-meta {
            align-items: flex-start;
            padding-left: 52px;
            text-align: left;
        }
        .pitch-container { height: 560px; border-width: 3px; border-radius: 14px; }
        .pitch-circle { width: 105px; height: 105px; }
        .pitch-penalty-top, .pitch-penalty-bottom { width: 180px; height: 75px; }
        .player-node { width: 92px; }
        .player-card-pitch { padding: 4px; }
        .player-pos-tag { font-size: .52rem; }
        .player-name-tag { font-size: .58rem; }
        .player-rating-tag, .player-empty-tag { font-size: .5rem; padding: 1px 3px; }
        .legend-box { justify-content: flex-start; gap: 10px; }
        .legend-item { width: 100%; font-size: .75rem; }
        .summary-grid { grid-template-columns: 1fr 1fr; }
        .bench-grid { grid-template-columns: 1fr 1fr; }
        .rating-grid { grid-template-columns: 1fr; }
    }

    /* Estados semânticos: adaptabilidade e informação */
    .player-card-pitch.adapt-primary { border-color: var(--green); }
    .player-card-pitch.adapt-secondary { border-color: var(--gold); }
    .player-card-pitch.adapt-tertiary { border-color: var(--orange); }
    .player-card-pitch.adapt-incompatible { border-color: var(--red); }

    .player-adaptability-tag {
        display: block;
        margin-top: 4px;
        color: var(--slate-300);
        font-size: .56rem;
        font-weight: 700;
        line-height: 1.2;
    }

    .legend-primary { background: var(--green); }
    .legend-secondary { background: var(--gold); }
    .legend-tertiary { background: var(--orange); }
    .legend-empty { background: var(--slate-500); }

    .summary-highlight,
    .profile-highlight { color: var(--gold); font-weight: 800; }
    .summary-positive { color: var(--green); }

    .market-card-info { border-left-color: var(--blue); }
    .market-details {
        color: var(--slate-300);
        line-height: 1.85;
        font-size: .88rem;
    }

    .stat-positive { border-left-color: var(--green); }
    .stat-negative { border-left-color: var(--red); }
    .stat-info { border-left-color: var(--blue); }

    .tactical-list {
        display: grid;
        gap: 18px;
        margin-bottom: 24px;
    }

    .tactical-list-section {
        background: var(--navy-950);
        border: 1px solid var(--navy-800);
        border-radius: 14px;
        padding: 14px;
    }

    .tactical-list-heading {
        color: var(--gold);
        font-size: 1rem;
        margin: 0 0 10px;
    }

    .tactical-list-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 10px;
        list-style: none;
        margin: 0;
        padding: 0;
    }

    .tactical-list-item {
        display: flex;
        justify-content: space-between;
        gap: 12px;
        min-height: 68px;
        padding: 10px 12px;
        border: 2px solid var(--slate-500);
        border-radius: 10px;
        background: var(--navy-900);
    }

    .tactical-list-main,
    .tactical-list-meta,
    .tactical-list-copy {
        display: flex;
    }

    .tactical-list-main {
        align-items: center;
        gap: 10px;
        min-width: 0;
    }

    .tactical-list-copy,
    .tactical-list-meta {
        flex-direction: column;
    }

    .tactical-list-copy {
        min-width: 0;
    }

    .tactical-list-meta {
        align-items: flex-end;
        justify-content: center;
        gap: 4px;
        text-align: right;
    }

    .tactical-list-tag {
        display: inline-grid;
        place-items: center;
        min-width: 42px;
        min-height: 42px;
        border-radius: 8px;
        background: var(--navy-800);
        color: var(--gold);
        font-size: .74rem;
        font-weight: 800;
    }

    .tactical-list-slot,
    .tactical-list-ratings {
        color: var(--slate-400);
        font-size: .75rem;
    }

    .tactical-list-name {
        color: var(--white);
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    .tactical-list-status {
        color: var(--slate-300);
        font-size: .72rem;
        font-weight: 700;
    }

    .tactical-list-item.adapt-primary { border-left-color: var(--green); }
    .tactical-list-item.adapt-secondary { border-left-color: var(--gold); }
    .tactical-list-item.adapt-tertiary { border-left-color: var(--orange); }
    .tactical-list-item.adapt-incompatible { border-left-color: var(--red); }
    .tactical-list-item.adapt-empty { border-left-color: var(--slate-500); }

    .feedback-link {
        display: block;
        min-height: 44px;
        padding: 11px 14px;
        border: 2px solid transparent;
        border-radius: 8px;
        background: var(--gold);
        color: var(--navy-950) !important;
        font-weight: 800;
        line-height: 1.35;
        text-align: center;
        text-decoration: none !important;
    }

    .feedback-link:hover {
        filter: brightness(1.08);
        text-decoration: underline !important;
    }

    .feedback-link:focus-visible,
    a:focus-visible,
    button:focus-visible,
    input:focus-visible,
    textarea:focus-visible,
    [role="radio"]:focus-visible,
    [role="option"]:focus-visible {
        outline: 3px solid var(--blue) !important;
        outline-offset: 3px;
    }

    @media (prefers-reduced-motion: reduce) {
        *, *::before, *::after {
            scroll-behavior: auto !important;
            transition-duration: .01ms !important;
            animation-duration: .01ms !important;
            animation-iteration-count: 1 !important;
        }
    }

    /* Posições do campo sem atributos style inline. */
    .pitch-pos-l15-b28 { left: 15%; bottom: 28%; }
    .pitch-pos-l20-b55 { left: 20%; bottom: 55%; }
    .pitch-pos-l20-b65 { left: 20%; bottom: 65%; }
    .pitch-pos-l20-b72 { left: 20%; bottom: 72%; }
    .pitch-pos-l25-b45 { left: 25%; bottom: 45%; }
    .pitch-pos-l30-b52 { left: 30%; bottom: 52%; }
    .pitch-pos-l35-b65 { left: 35%; bottom: 65%; }
    .pitch-pos-l37-b22 { left: 37%; bottom: 22%; }
    .pitch-pos-l38-b42 { left: 38%; bottom: 42%; }
    .pitch-pos-l38-b45 { left: 38%; bottom: 45%; }
    .pitch-pos-l38-b78 { left: 38%; bottom: 78%; }
    .pitch-pos-l40-b45 { left: 40%; bottom: 45%; }
    .pitch-pos-l50-b40 { left: 50%; bottom: 40%; }
    .pitch-pos-l50-b42 { left: 50%; bottom: 42%; }
    .pitch-pos-l50-b60 { left: 50%; bottom: 60%; }
    .pitch-pos-l50-b62 { left: 50%; bottom: 62%; }
    .pitch-pos-l50-b65 { left: 50%; bottom: 65%; }
    .pitch-pos-l50-b8 { left: 50%; bottom: 8%; }
    .pitch-pos-l50-b82 { left: 50%; bottom: 82%; }
    .pitch-pos-l60-b45 { left: 60%; bottom: 45%; }
    .pitch-pos-l62-b42 { left: 62%; bottom: 42%; }
    .pitch-pos-l62-b45 { left: 62%; bottom: 45%; }
    .pitch-pos-l62-b78 { left: 62%; bottom: 78%; }
    .pitch-pos-l63-b22 { left: 63%; bottom: 22%; }
    .pitch-pos-l65-b65 { left: 65%; bottom: 65%; }
    .pitch-pos-l70-b52 { left: 70%; bottom: 52%; }
    .pitch-pos-l75-b45 { left: 75%; bottom: 45%; }
    .pitch-pos-l80-b55 { left: 80%; bottom: 55%; }
    .pitch-pos-l80-b65 { left: 80%; bottom: 65%; }
    .pitch-pos-l80-b72 { left: 80%; bottom: 72%; }
    .pitch-pos-l85-b28 { left: 85%; bottom: 28%; }

    /* Larguras discretas do comparativo de mercado sem style inline. */
    .progress-pct-0 { width: 0%; }
    .progress-pct-1 { width: 1%; }
    .progress-pct-2 { width: 2%; }
    .progress-pct-3 { width: 3%; }
    .progress-pct-4 { width: 4%; }
    .progress-pct-5 { width: 5%; }
    .progress-pct-6 { width: 6%; }
    .progress-pct-7 { width: 7%; }
    .progress-pct-8 { width: 8%; }
    .progress-pct-9 { width: 9%; }
    .progress-pct-10 { width: 10%; }
    .progress-pct-11 { width: 11%; }
    .progress-pct-12 { width: 12%; }
    .progress-pct-13 { width: 13%; }
    .progress-pct-14 { width: 14%; }
    .progress-pct-15 { width: 15%; }
    .progress-pct-16 { width: 16%; }
    .progress-pct-17 { width: 17%; }
    .progress-pct-18 { width: 18%; }
    .progress-pct-19 { width: 19%; }
    .progress-pct-20 { width: 20%; }
    .progress-pct-21 { width: 21%; }
    .progress-pct-22 { width: 22%; }
    .progress-pct-23 { width: 23%; }
    .progress-pct-24 { width: 24%; }
    .progress-pct-25 { width: 25%; }
    .progress-pct-26 { width: 26%; }
    .progress-pct-27 { width: 27%; }
    .progress-pct-28 { width: 28%; }
    .progress-pct-29 { width: 29%; }
    .progress-pct-30 { width: 30%; }
    .progress-pct-31 { width: 31%; }
    .progress-pct-32 { width: 32%; }
    .progress-pct-33 { width: 33%; }
    .progress-pct-34 { width: 34%; }
    .progress-pct-35 { width: 35%; }
    .progress-pct-36 { width: 36%; }
    .progress-pct-37 { width: 37%; }
    .progress-pct-38 { width: 38%; }
    .progress-pct-39 { width: 39%; }
    .progress-pct-40 { width: 40%; }
    .progress-pct-41 { width: 41%; }
    .progress-pct-42 { width: 42%; }
    .progress-pct-43 { width: 43%; }
    .progress-pct-44 { width: 44%; }
    .progress-pct-45 { width: 45%; }
    .progress-pct-46 { width: 46%; }
    .progress-pct-47 { width: 47%; }
    .progress-pct-48 { width: 48%; }
    .progress-pct-49 { width: 49%; }
    .progress-pct-50 { width: 50%; }
    .progress-pct-51 { width: 51%; }
    .progress-pct-52 { width: 52%; }
    .progress-pct-53 { width: 53%; }
    .progress-pct-54 { width: 54%; }
    .progress-pct-55 { width: 55%; }
    .progress-pct-56 { width: 56%; }
    .progress-pct-57 { width: 57%; }
    .progress-pct-58 { width: 58%; }
    .progress-pct-59 { width: 59%; }
    .progress-pct-60 { width: 60%; }
    .progress-pct-61 { width: 61%; }
    .progress-pct-62 { width: 62%; }
    .progress-pct-63 { width: 63%; }
    .progress-pct-64 { width: 64%; }
    .progress-pct-65 { width: 65%; }
    .progress-pct-66 { width: 66%; }
    .progress-pct-67 { width: 67%; }
    .progress-pct-68 { width: 68%; }
    .progress-pct-69 { width: 69%; }
    .progress-pct-70 { width: 70%; }
    .progress-pct-71 { width: 71%; }
    .progress-pct-72 { width: 72%; }
    .progress-pct-73 { width: 73%; }
    .progress-pct-74 { width: 74%; }
    .progress-pct-75 { width: 75%; }
    .progress-pct-76 { width: 76%; }
    .progress-pct-77 { width: 77%; }
    .progress-pct-78 { width: 78%; }
    .progress-pct-79 { width: 79%; }
    .progress-pct-80 { width: 80%; }
    .progress-pct-81 { width: 81%; }
    .progress-pct-82 { width: 82%; }
    .progress-pct-83 { width: 83%; }
    .progress-pct-84 { width: 84%; }
    .progress-pct-85 { width: 85%; }
    .progress-pct-86 { width: 86%; }
    .progress-pct-87 { width: 87%; }
    .progress-pct-88 { width: 88%; }
    .progress-pct-89 { width: 89%; }
    .progress-pct-90 { width: 90%; }
    .progress-pct-91 { width: 91%; }
    .progress-pct-92 { width: 92%; }
    .progress-pct-93 { width: 93%; }
    .progress-pct-94 { width: 94%; }
    .progress-pct-95 { width: 95%; }
    .progress-pct-96 { width: 96%; }
    .progress-pct-97 { width: 97%; }
    .progress-pct-98 { width: 98%; }
    .progress-pct-99 { width: 99%; }
    .progress-pct-100 { width: 100%; }
</style>
"""


def aplicar_estilos() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
