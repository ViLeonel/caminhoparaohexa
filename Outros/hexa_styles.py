"""Design system compartilhado do aplicativo."""

from __future__ import annotations

import streamlit as st

__all__ = [
    "CSS",
    "HIGH_CONTRAST_CSS",
    "aplicar_estilos",
]


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
        --color-background: var(--navy-900);
        --color-surface: var(--navy-800);
        --color-text: var(--white);
        --color-text-muted: var(--slate-400);
        --color-highlight: var(--gold);
        --color-success: var(--green);
        --color-warning: var(--orange);
        --color-danger: var(--red);
        --color-focus: #60A5FA;
        --grid-row-height: 2.5rem;
        --grid-row-height-comfortable: 3rem;
        --grid-header-height: 2.625rem;
        --grid-cell-padding-x: .65rem;
        --grid-cell-padding-y: .5rem;
        --space-page-top: .75rem;
        --space-sidebar-top: .65rem;
        --space-hero-bottom: 1rem;
        --type-display: clamp(2.25rem, 4.5vw, 2.75rem);
        --type-h1: clamp(2rem, 4vw, 2.5rem);
        --type-h2: clamp(1.55rem, 3vw, 1.875rem);
        --type-h3: clamp(1.2rem, 2vw, 1.4rem);
        --type-body-lg: 1.0625rem;
        --type-body: 1rem;
        --type-small: .875rem;
        --type-label: .75rem;
        --weight-regular: 400;
        --weight-medium: 500;
        --weight-semibold: 600;
        --weight-bold: 700;
    }

    .stApp {
        background-color: var(--navy-900);
        color: var(--white);
        font-size: var(--type-body);
        line-height: 1.55;
    }

    .block-container {
        max-width: 1500px;
        padding-top: var(--space-page-top);
        padding-bottom: 3rem;
    }

    .page-header {
        max-width: 920px;
        margin: .25rem 0 1.5rem;
    }

    .app-title {
        margin: 0;
        color: var(--white);
        font-size: var(--type-h1);
        font-weight: var(--weight-bold);
        line-height: 1.12;
        letter-spacing: -.025em;
        text-align: left;
        text-wrap: balance;
    }

    .app-title::after {
        content: "";
        display: block;
        width: 3.5rem;
        height: 3px;
        margin-top: .7rem;
        border-radius: 999px;
        background: var(--gold);
    }

    .project-subtitle {
        max-width: 760px;
        margin: .8rem 0 0;
        color: var(--slate-300);
        font-size: var(--type-body-lg);
        line-height: 1.6;
        text-align: left;
    }

    .section-header {
        max-width: 920px;
        margin: 2rem 0 1rem;
    }

    .section-eyebrow {
        margin: 0 0 .35rem;
        color: var(--gold);
        font-size: var(--type-label);
        font-weight: var(--weight-semibold);
        line-height: 1.3;
        letter-spacing: .08em;
        text-transform: uppercase;
    }

    .section-title {
        margin: 0;
        color: var(--white);
        font-weight: var(--weight-semibold);
        line-height: 1.2;
        letter-spacing: -.018em;
        text-wrap: balance;
    }

    .section-title-2 { font-size: var(--type-h2); }
    .section-title-3 { font-size: var(--type-h3); }

    .convocation-builder-title {
        margin: 0 0 1rem;
        color: var(--white);
        font-size: clamp(1.75rem, 3vw, 2.5rem);
        font-weight: var(--weight-bold);
        line-height: 1.14;
        letter-spacing: -.025em;
        text-wrap: balance;
    }

    .section-subtitle {
        max-width: 760px;
        margin: .45rem 0 0;
        color: var(--slate-400);
        font-size: var(--type-small);
        line-height: 1.55;
    }

    .project-hero {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: clamp(1rem, 3vw, 2rem);
        max-width: 1120px;
        margin: 0 auto var(--space-hero-bottom);
        padding: .25rem 1rem .65rem;
    }

    .project-trophy {
        flex: 0 0 auto;
        width: clamp(68px, 8vw, 104px);
        color: var(--gold);
        filter: drop-shadow(0 8px 16px rgba(0, 0, 0, .4));
    }

    .world-cup-trophy {
        display: block;
        width: 100%;
        height: auto;
        fill: currentColor;
    }

    .world-cup-trophy .trophy-detail {
        fill: none;
        stroke: var(--navy-900);
        stroke-width: 3;
        stroke-linecap: round;
        opacity: .72;
    }

    .project-hero-copy {
        min-width: 0;
        max-width: 900px;
    }

    .project-hero-title {
        margin: 0 0 .55rem;
        color: var(--white);
        font-size: var(--type-display);
        font-weight: var(--weight-bold);
        line-height: 1.08;
        letter-spacing: -.03em;
        text-wrap: balance;
    }

    .project-hero-subtitle {
        max-width: 860px;
        margin: 0;
        color: var(--slate-300);
        font-size: var(--type-body-lg);
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
        font-weight: var(--weight-semibold);
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
        font-weight: 700;
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
        font-size: .8rem;
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
        font-weight: 700;
    }

    .bench-name {
        color: var(--white);
        font-size: .82rem;
        font-weight: 700;
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
        font-size: var(--type-label);
        text-transform: uppercase;
        font-weight: var(--weight-semibold);
        letter-spacing: .04em;
    }

    .summary-value {
        color: var(--white);
        font-size: 1.05rem;
        font-weight: var(--weight-semibold);
        margin-top: 3px;
    }

    .summary-footnote {
        color: var(--slate-400);
        font-size: .72rem;
        text-align: center;
        margin-top: 12px;
    }

    .profile-card {
        position: relative;
        isolation: isolate;
        min-height: 360px;
        padding: 1.15rem;
        overflow: hidden;
        border: 3px solid var(--gold);
        text-align: left;
        background:
            radial-gradient(circle at 90% 12%, rgba(234, 179, 8, .24), transparent 34%),
            linear-gradient(145deg, #111827 0%, var(--navy-950) 58%, #172554 100%);
    }

    .profile-card::before,
    .profile-card::after {
        content: "";
        position: absolute;
        z-index: -1;
        pointer-events: none;
    }

    .profile-card::before {
        inset: auto -18% -36% 22%;
        height: 72%;
        transform: rotate(-11deg);
        border: 1px solid rgba(234, 179, 8, .18);
        background: rgba(30, 41, 59, .46);
    }

    .profile-card::after {
        top: 0;
        right: 0;
        width: 44%;
        height: 5px;
        background: linear-gradient(90deg, transparent, var(--gold));
    }

    .profile-card-topline {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: .75rem;
    }

    .profile-position-badge,
    .profile-evaluation-status {
        display: inline-flex;
        align-items: center;
        min-height: 30px;
        border-radius: 999px;
        font-size: .7rem;
        font-weight: var(--weight-bold);
        line-height: 1.2;
        letter-spacing: .045em;
        text-transform: uppercase;
    }

    .profile-position-badge {
        padding: .4rem .7rem;
        border: 1px solid rgba(234, 179, 8, .72);
        background: rgba(234, 179, 8, .12);
        color: var(--gold);
    }

    .profile-evaluation-status {
        max-width: 58%;
        padding: .4rem .65rem;
        justify-content: flex-end;
        color: var(--slate-300);
        text-align: right;
    }

    .profile-card-identity {
        margin-top: 1.35rem;
    }

    .profile-card-kicker {
        color: var(--slate-400);
        font-size: .68rem;
        font-weight: var(--weight-semibold);
        letter-spacing: .08em;
        text-transform: uppercase;
    }

    .profile-card h2 {
        margin: .35rem 0 .85rem;
        color: var(--white);
        font-size: clamp(1.85rem, 4vw, 2.55rem);
        font-weight: var(--weight-bold);
        line-height: 1.02;
        letter-spacing: -.035em;
        overflow-wrap: anywhere;
    }

    .profile-position-inline {
        margin: .15rem 0 1rem;
        color: var(--gold);
        font-size: .78rem;
        font-weight: var(--weight-bold);
        letter-spacing: .08em;
        line-height: 1.35;
        text-transform: uppercase;
    }

    .profile-club {
        display: grid;
        gap: .18rem;
        margin: 0;
    }

    .profile-club span {
        color: var(--slate-400);
        font-size: .68rem;
        font-weight: var(--weight-semibold);
        letter-spacing: .045em;
        text-transform: uppercase;
    }

    .profile-club strong {
        color: var(--slate-300);
        font-size: .95rem;
        font-weight: var(--weight-semibold);
        line-height: 1.35;
    }

    .profile-game-stats {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: .55rem;
        margin: 2rem 0 0;
    }

    .profile-game-stat {
        display: flex;
        flex-direction: column;
        min-width: 0;
        padding: .8rem .45rem;
        border: 1px solid rgba(148, 163, 184, .28);
        border-radius: 10px;
        background: rgba(2, 6, 23, .66);
        text-align: center;
    }

    .profile-game-stat dd {
        order: 1;
        margin: 0;
        color: var(--gold);
        font-size: clamp(1.25rem, 2.7vw, 1.65rem);
        font-weight: var(--weight-bold);
        line-height: 1;
        white-space: nowrap;
    }

    .profile-game-stat dt {
        order: 2;
        margin-top: .4rem;
        color: var(--slate-400);
        font-size: .62rem;
        font-weight: var(--weight-semibold);
        line-height: 1.25;
        text-transform: uppercase;
    }

    .profile-position-full {
        margin: .8rem 0 0;
        color: var(--slate-300);
        font-size: .75rem;
        line-height: 1.35;
        text-align: right;
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
        font-weight: 700;
        text-transform: uppercase;
    }

    .rating-value {
        color: var(--white);
        font-size: 1.25rem;
        font-weight: 700;
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
        padding: clamp(1.2rem, 2vw, 1.6rem);
        border-left: 5px solid var(--gold);
        margin-bottom: 1.5rem;
    }

    .market-grid {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 1rem;
        margin: 0;
    }

    .market-metric {
        min-width: 0;
        padding: 1rem;
        border: 1px solid rgba(148, 163, 184, .22);
        border-radius: 12px;
        background: rgba(15, 23, 42, .62);
    }

    .market-metric--primary {
        border-color: rgba(234, 179, 8, .52);
        background: rgba(234, 179, 8, .08);
    }

    .market-label {
        margin: 0;
        color: var(--slate-400);
        font-size: var(--type-label);
        text-transform: uppercase;
        font-weight: var(--weight-semibold);
        line-height: 1.4;
        letter-spacing: .04em;
    }

    .market-value {
        margin: .55rem 0 0;
        color: var(--white);
        font-size: clamp(1.08rem, 2vw, 1.3rem);
        font-weight: var(--weight-semibold);
        line-height: 1.25;
        overflow-wrap: anywhere;
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
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 1rem;
        margin: 1.25rem 0 0;
        padding-top: 1.1rem;
        border-top: 1px solid rgba(148, 163, 184, .18);
    }

    .market-date-item {
        min-width: 0;
    }

    .market-date-item dt {
        margin: 0;
        color: var(--slate-400);
        font-size: .72rem;
        font-weight: var(--weight-semibold);
        line-height: 1.4;
        letter-spacing: .025em;
        text-transform: uppercase;
    }

    .market-date-item dd {
        margin: .35rem 0 0;
        color: var(--slate-300);
        font-size: .875rem;
        line-height: 1.45;
        overflow-wrap: anywhere;
    }

    .market-card-info {
        margin: 1.5rem 0 0;
        padding-top: .9rem;
        border-top: 1px dashed rgba(148, 163, 184, .18);
        color: var(--slate-400);
        font-size: .75rem;
        font-style: italic;
        line-height: 1.6;
    }

    .market-card-info em {
        font-style: inherit;
    }

    .stat-box {
        padding: 18px;
        border-left: 6px solid var(--gold);
        margin-bottom: 14px;
        color: var(--slate-300);
        line-height: 1.6;
    }

    .stat-box strong { color: var(--white); }

    .kpi-group {
        margin: 1.25rem 0 1.6rem;
    }

    .kpi-group + .kpi-group {
        margin-top: .5rem;
    }

    .kpi-group-header {
        margin-bottom: .7rem;
    }

    .kpi-group-title {
        margin: 0;
        color: var(--slate-300);
        font-size: 1rem;
        font-weight: var(--weight-semibold);
        line-height: 1.35;
    }

    .kpi-group-description {
        margin: .25rem 0 0;
        color: var(--slate-400);
        font-size: var(--type-small);
        line-height: 1.5;
    }

    .kpi-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: .75rem;
    }

    .kpi-card {
        position: relative;
        min-width: 0;
        min-height: 86px;
        padding: .8rem .9rem .75rem;
        overflow: hidden;
        border: 1px solid rgba(148, 163, 184, .28);
        border-radius: 12px;
        background: rgba(2, 6, 23, .64);
        box-shadow: 0 3px 12px rgba(0, 0, 0, .16);
    }

    .kpi-card::before {
        content: "";
        position: absolute;
        inset: 0 auto 0 0;
        width: 3px;
        background: var(--slate-500);
    }

    .kpi-destaque::before { background: var(--gold); }
    .kpi-positivo::before { background: var(--green); }
    .kpi-informativo::before { background: var(--blue); }

    .kpi-label,
    .kpi-value,
    .kpi-context {
        display: block;
        min-width: 0;
        overflow-wrap: anywhere;
    }

    .kpi-label {
        color: var(--slate-400);
        font-size: var(--type-label);
        font-weight: var(--weight-semibold);
        line-height: 1.3;
        letter-spacing: .035em;
        text-transform: uppercase;
    }

    .kpi-value {
        margin-top: .3rem;
        color: var(--white);
        font-size: clamp(1.35rem, 2.2vw, 1.65rem);
        font-weight: var(--weight-semibold);
        line-height: 1.12;
        letter-spacing: -.018em;
    }

    .kpi-context {
        margin-top: .35rem;
        color: var(--slate-400);
        font-size: .75rem;
        line-height: 1.35;
    }


    .player-data-panel {
        margin: .2rem 0 .35rem;
    }

    .player-data-groups {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 1rem;
    }

    .player-data-group {
        min-width: 0;
        padding: 1rem 1.05rem;
        border: 1px solid rgba(148, 163, 184, .22);
        border-radius: 12px;
        background:
            linear-gradient(180deg, rgba(30, 41, 59, .58), rgba(15, 23, 42, .42));
    }

    .player-data-group--wide {
        grid-column: 1 / -1;
    }

    .player-data-group-title {
        margin: 0 0 .35rem;
        padding-bottom: .65rem;
        border-bottom: 2px solid rgba(234, 179, 8, .58);
        color: var(--white);
        font-size: .875rem;
        font-weight: var(--weight-semibold);
        line-height: 1.35;
    }

    .player-data-list {
        display: grid;
        gap: 0;
        margin: 0;
    }

    .player-data-group--wide .player-data-list {
        grid-template-columns: repeat(2, minmax(0, 1fr));
        column-gap: 1.25rem;
    }

    .player-data-item {
        min-width: 0;
        padding: .78rem 0;
        border-bottom: 1px solid rgba(148, 163, 184, .16);
    }

    .player-data-item:last-child {
        border-bottom: 0;
    }

    .player-data-group--wide .player-data-item:nth-last-child(-n + 2) {
        border-bottom: 0;
    }

    .player-data-term {
        margin: 0;
        color: var(--slate-400);
        font-size: .7rem;
        font-weight: var(--weight-semibold);
        line-height: 1.35;
        letter-spacing: .04em;
        text-transform: uppercase;
    }

    .player-data-description {
        margin: .32rem 0 0;
        color: var(--white);
        font-size: .94rem;
        font-weight: var(--weight-regular);
        line-height: 1.5;
        overflow-wrap: anywhere;
    }

    .contract-details {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 0 1.5rem;
        margin: 0;
    }

    .contract-item {
        min-width: 0;
        padding: .8rem 0;
        border-bottom: 1px solid rgba(148, 163, 184, .2);
    }

    .contract-term {
        margin: 0;
        color: var(--slate-400);
        font-size: var(--type-label);
        font-weight: var(--weight-semibold);
        line-height: 1.3;
        letter-spacing: .035em;
        text-transform: uppercase;
    }

    .contract-description {
        margin: .3rem 0 0;
        color: var(--white);
        font-size: .9375rem;
        font-weight: var(--weight-regular);
        line-height: 1.5;
        overflow-wrap: anywhere;
    }

    .sidebar-title {
        color: var(--white);
        margin-top: 0;
        font-size: 1rem;
        font-weight: var(--weight-semibold);
        letter-spacing: .04em;
        text-align: center;
    }

    section[data-testid="stSidebar"] {
        background-color: var(--navy-950) !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stSidebarContent"] {
        padding-top: var(--space-sidebar-top);
    }

    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] label {
        color: var(--white) !important;
    }

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
        .pitch-container { height: clamp(520px, 72vh, 620px); }
        .tactical-list-grid { grid-template-columns: 1fr; }
        .player-node { width: 112px; }
        .player-name-tag { font-size: .68rem; }
        .player-rating-tag, .player-empty-tag { font-size: .57rem; }
        .market-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
        .player-data-groups { grid-template-columns: 1fr; }
        .player-data-group--wide { grid-column: auto; }
    }

    @media (max-width: 600px) {
        .block-container {
            padding-top: .5rem;
            padding-left: .75rem;
            padding-right: .75rem;
        }
        .project-hero {
            flex-direction: column;
            gap: .65rem;
            padding: 0 .25rem 1rem;
            text-align: center;
        }
        .page-header {
            margin-top: 0;
            margin-bottom: 1.25rem;
        }
        .app-title { font-size: clamp(1.85rem, 8vw, 2.15rem); }
        .project-subtitle { font-size: 1rem; }
        .project-trophy { width: 60px; }
        .project-hero-title { font-size: clamp(2rem, 10vw, 2.4rem); }
        .project-hero-subtitle {
            font-size: 1rem;
            line-height: 1.55;
        }
        .market-grid,
        .market-dates,
        .player-data-group--wide .player-data-list {
            grid-template-columns: 1fr;
        }
        .market-card {
            padding: 1rem;
        }
        .market-metric {
            padding: .9rem;
        }
        .section-header { margin-top: 1.6rem; }
        .kpi-grid,
        .contract-details {
            grid-template-columns: 1fr;
        }
        .kpi-card { min-height: 80px; }
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
        .profile-card {
            min-height: 330px;
            padding: 1rem;
        }
        .profile-card-identity { margin-top: 1.8rem; }
        .profile-evaluation-status { max-width: 62%; }
        .profile-game-stats { gap: .4rem; margin-top: 1.5rem; }
        .profile-game-stat { padding: .7rem .3rem; }
        .profile-game-stat dt { font-size: .56rem; }
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
    .profile-highlight { color: var(--gold); font-weight: 700; }
    .summary-positive { color: var(--green); }

    .market-card-info { border-left-color: var(--blue); }

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
        font-weight: 700;
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
        font-weight: 700;
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
    .pitch-pos-l50-b76 { left: 50%; bottom: 76%; }
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

    .skip-link {
        position: fixed;
        top: .5rem;
        left: .5rem;
        z-index: 10000;
        transform: translateY(-180%);
        background: var(--white);
        color: var(--navy-950);
        border: 3px solid var(--color-focus);
        border-radius: .5rem;
        padding: .75rem 1rem;
        font-weight: 700;
    }
    .skip-link:focus { transform: translateY(0); }

    :where(a, button, input, textarea, select, [role="button"], [role="radio"],
    [role="checkbox"], [role="switch"], [role="tab"], summary):focus-visible {
        outline: 3px solid var(--color-focus) !important;
        outline-offset: 3px !important;
        box-shadow: 0 0 0 5px var(--navy-950) !important;
    }

    [data-baseweb="select"] > div,
    [data-baseweb="input"] > div,
    [data-baseweb="textarea"] > div {
        min-height: 44px;
    }

    button, [role="button"], [role="radio"], [role="checkbox"], [role="switch"], summary {
        min-height: 44px;
    }

    .sr-only {
        position: absolute !important;
        width: 1px !important;
        height: 1px !important;
        padding: 0 !important;
        margin: -1px !important;
        overflow: hidden !important;
        clip: rect(0, 0, 0, 0) !important;
        white-space: nowrap !important;
        border: 0 !important;
    }

    .live-region { margin: .5rem 0 1rem; }
    .pitch-container:focus, .tactical-list:focus, .bench-box:focus {
        outline: 3px solid var(--color-focus);
        outline-offset: 4px;
    }

    @media (max-width: 900px), (min-resolution: 1.5dppx) {
        .block-container { max-width: 100%; }
        .player-name-tag { white-space: normal; overflow: visible; }
    }

    @media (forced-colors: active) {
        * { forced-color-adjust: auto; }
        .player-card-pitch, .bench-card, .tactical-list-item,
        .evaluation-meta-card, .kpi-card, .contract-item {
            border: 2px solid CanvasText !important;
        }
        .world-cup-trophy {
            color: CanvasText;
            forced-color-adjust: auto;
        }
    }

</style>
"""


HIGH_CONTRAST_CSS = """
<style>
    :root {
        --navy-950: #000000;
        --navy-900: #000000;
        --navy-800: #111111;
        --slate-500: #E5E7EB;
        --slate-400: #F3F4F6;
        --slate-300: #FFFFFF;
        --white: #FFFFFF;
        --gold: #FFF200;
        --green: #7CFF6B;
        --orange: #FFD166;
        --red: #FF7B7B;
        --blue: #7DD3FC;
        --color-focus: #00E5FF;
    }
    .stApp { background: #000000 !important; color: #FFFFFF !important; }
    .player-card-pitch, .bench-card, .tactical-list-item,
    .summary-card, .profile-card, .market-card, .legend-box,
    .evaluation-meta-card, .kpi-card, .contract-item {
        background: #000000 !important;
        border-width: 3px !important;
    }
    .project-subtitle, .project-hero-subtitle, .profile-secondary,
    .market-label, .bench-club, .tactical-list-slot, .kpi-context,
    .contract-term, .section-subtitle {
        color: #FFFFFF !important;
    }
    .project-trophy, .section-eyebrow { color: #FFF200 !important; }
    .world-cup-trophy .trophy-detail { stroke: #000000 !important; }
    a { text-decoration: underline !important; text-decoration-thickness: 2px !important; }
</style>
"""


RC5_CSS = """
<style>
    .evaluation-context {
        display: flex;
        justify-content: space-between;
        gap: 1rem;
        align-items: center;
        flex-wrap: wrap;
        margin: 0 0 1.5rem;
        padding: .9rem 1rem;
        border: 1px solid var(--slate-500);
        border-left: 5px solid var(--gold);
        border-radius: 12px;
        background: var(--navy-800);
    }
    .evaluation-context-main,
    .evaluation-context-stats {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: .45rem .9rem;
    }
    .evaluation-context-main strong {
        color: var(--gold);
        font-size: 1rem;
    }
    .evaluation-context-main span,
    .evaluation-context-stats span {
        color: var(--slate-300);
        font-size: .88rem;
        line-height: 1.4;
    }
    .evaluation-context-stats span {
        padding: .28rem .55rem;
        border: 1px solid var(--slate-500);
        border-radius: 999px;
    }
    .contract-details {
        line-height: 1.55;
    }
    .market-card-info {
        margin: 1.5rem 0 0;
        padding-top: .9rem;
        border-top: 1px dashed rgba(148, 163, 184, .18);
        color: var(--slate-400);
        font-size: .75rem;
        font-style: italic;
        line-height: 1.6;
    }
    .executive-table-card {
        display: block;
        margin: 1rem 0 1.15rem;
        padding: 0;
        overflow: hidden;
        border: 1px solid rgba(148, 163, 184, .24);
        border-radius: 14px;
        background:
            linear-gradient(180deg, rgba(30, 41, 59, .58), rgba(2, 6, 23, .78));
        box-shadow: 0 10px 24px rgba(0, 0, 0, .18);
        line-height: normal;
    }

    .executive-table-scroll {
        display: block;
        width: 100%;
        margin: 0;
        padding: 0;
        overflow-x: auto;
        overflow-y: hidden;
        overscroll-behavior-inline: contain;
        scrollbar-gutter: stable;
    }

    .executive-table-card--tall .executive-table-scroll {
        max-height: 42rem;
        overflow-y: auto;
    }

    .executive-table-card--wide .executive-table {
        min-width: 1120px;
    }

    .executive-table {
        width: 100%;
        margin: 0 !important;
        border: 0;
        border-collapse: separate;
        border-spacing: 0;
        table-layout: auto;
        background: transparent;
    }

    .executive-table col {
        min-width: 0;
    }

    .executive-table th,
    .executive-table td {
        min-width: 0;
        padding: var(--grid-cell-padding-y) var(--grid-cell-padding-x);
        border-right: 1px solid rgba(148, 163, 184, .16);
        border-bottom: 1px solid rgba(148, 163, 184, .16);
        vertical-align: middle;
    }

    .executive-table tr > *:last-child {
        border-right: 0;
    }

    .executive-table tbody tr:last-child > * {
        border-bottom: 0;
    }

    .executive-table thead th {
        position: sticky;
        top: 0;
        z-index: 2;
        background: rgba(15, 23, 42, .98);
        color: var(--slate-400);
        font-size: .68rem;
        font-weight: var(--weight-semibold);
        line-height: 1.3;
        letter-spacing: .045em;
        text-transform: uppercase;
    }

    .executive-table tbody th {
        background: rgba(15, 23, 42, .42);
        color: var(--white);
        font-weight: var(--weight-semibold);
    }

    .executive-table tbody td {
        color: var(--slate-300);
        font-variant-numeric: tabular-nums;
    }

    .executive-table tbody tr:nth-child(even) > *:not(.executive-table-column--accent) {
        background-color: rgba(15, 23, 42, .28);
    }

    .executive-table tbody tr:hover > *:not(.executive-table-column--accent) {
        background-color: rgba(30, 41, 59, .56);
    }

    .executive-table-column--accent {
        background: rgba(234, 179, 8, .08);
    }

    .executive-table thead .executive-table-column--accent {
        background: rgba(58, 53, 35, .98);
    }

    .executive-table tbody .executive-table-column--accent {
        color: var(--gold);
    }

    .executive-table-card--wide .executive-table thead th:first-child,
    .executive-table-card--wide .executive-table tbody th:first-child {
        position: sticky;
        left: 0;
        box-shadow: 1px 0 0 rgba(148, 163, 184, .16);
    }

    .executive-table-card--wide .executive-table thead th:first-child {
        z-index: 4;
        background: rgba(15, 23, 42, .995);
    }

    .executive-table-card--wide .executive-table tbody th:first-child {
        z-index: 1;
        background: rgba(11, 18, 32, .98);
    }

    .executive-table-card--wide .executive-table tbody tr:nth-child(even) th:first-child {
        background: rgba(18, 28, 48, .99);
    }

    .executive-table-align--esquerda {
        text-align: left;
    }

    .executive-table-align--centro {
        text-align: center;
    }

    .executive-table-align--direita {
        text-align: right;
    }

    .executive-table-value {
        display: inline-block;
        color: inherit;
        font-size: .875rem;
        font-weight: var(--weight-semibold);
        line-height: 1.3;
        white-space: nowrap;
    }

    .executive-table-column--accent .executive-table-value {
        font-size: .925rem;
        font-weight: var(--weight-bold);
    }

    .executive-table-caption {
        display: block;
        margin-top: .14rem;
        color: var(--slate-400);
        font-size: .66rem;
        font-weight: var(--weight-regular);
        line-height: 1.35;
    }

    .executive-table-value--positive {
        color: var(--green);
    }

    .executive-table-value--negative {
        color: #FCA5A5;
    }

    .executive-table-cell--progress {
        min-width: 8.5rem;
    }

    .executive-table-progress {
        display: block;
        width: 100%;
        height: 4px;
        margin-top: .28rem;
        overflow: hidden;
        border-radius: 999px;
        background: rgba(100, 116, 139, .28);
    }

    .executive-table-progress > span {
        display: block;
        height: 100%;
        border-radius: inherit;
        background: linear-gradient(90deg, var(--orange), var(--gold), var(--green));
    }

    .executive-table-scroll:focus-visible {
        outline: 3px solid var(--color-focus);
        outline-offset: -3px;
    }

    .evaluation-meta-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: .75rem;
        margin: .9rem 0 1rem;
    }
    .evaluation-meta-card {
        min-width: 0;
        padding: .8rem .9rem;
        border: 1px solid var(--navy-800);
        border-radius: 10px;
        background: var(--navy-950);
    }
    .evaluation-meta-card--status {
        grid-column: 1 / -1;
    }
    .evaluation-meta-label {
        color: var(--slate-400);
        font-size: var(--type-label);
        font-weight: var(--weight-semibold);
        line-height: 1.3;
        text-transform: uppercase;
        letter-spacing: .04em;
    }
    .evaluation-meta-value {
        margin-top: .35rem;
        color: var(--white);
        font-size: clamp(1rem, 1.7vw, 1.2rem);
        font-weight: var(--weight-semibold);
        line-height: 1.25;
        overflow-wrap: normal;
        word-break: normal;
    }
    .evaluation-meta-value--status {
        font-size: clamp(1.05rem, 1.8vw, 1.3rem);
        text-wrap: balance;
    }
    .evaluation-meta-value--numeric,
    .evaluation-meta-value--date {
        white-space: nowrap;
    }
    .evaluation-meta-emphasis {
        color: var(--gold);
        font-size: clamp(1.15rem, 2vw, 1.4rem);
    }
    @media (max-width: 700px) {
        .evaluation-context,
        .evaluation-context-main,
        .evaluation-context-stats {
            align-items: flex-start;
            flex-direction: column;
            width: 100%;
        }
        .evaluation-context-stats span {
            width: 100%;
            border-radius: 8px;
        }
        .contract-details,
        .evaluation-meta-grid {
            grid-template-columns: 1fr;
        }
        .executive-table-card {
            border-radius: 12px;
        }
        .executive-table-card:not(.executive-table-card--wide) .executive-table th,
        .executive-table-card:not(.executive-table-card--wide) .executive-table td {
            padding: .48rem .42rem;
        }
        .executive-table thead th {
            font-size: .6rem;
        }
        .executive-table-value {
            font-size: .82rem;
        }
        .executive-table-column--accent .executive-table-value {
            font-size: .92rem;
        }
        .executive-table-caption {
            font-size: .6rem;
        }
        .evaluation-meta-card--status {
            grid-column: auto;
        }
    }
    @media (forced-colors: active) {
        .evaluation-context {
            border: 2px solid CanvasText;
        }
        .evaluation-context-stats span {
            border: 1px solid CanvasText;
        }
    }
</style>
"""


def aplicar_estilos(*, alto_contraste: bool = False) -> None:
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown(RC5_CSS, unsafe_allow_html=True)
    if alto_contraste:
        st.markdown(HIGH_CONTRAST_CSS, unsafe_allow_html=True)
