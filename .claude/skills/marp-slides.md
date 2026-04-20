---
name: marp-slides
description: Create HEMERIA customer-facing PPTX presentations from ReqMap analysis data. Triggers on 'marp', 'slides', 'presentation', 'deck', 'conformity report', 'requirements report'.
version: 2.1-reqmap
updated: 2026-04-20
---

# MARP Slides — ReqMap / HEMERIA Edition

## Setup (CLI-only)

```bash
npx @marp-team/marp-cli slides.md --pptx --allow-local-files
```

No VS Code extension needed. PPTX is the default export target for this project.

> **HEMERIA branding note:** `HEMERIA.potx` is in the project root as a visual reference for colors, typography feel, and layout conventions. Marp generates its own PPTX styling — match the spirit of that template (professional, aerospace-grade, restrained palette). Do NOT reference `.potx` files in marp directives.

## Example Decks (read before generating)

The original skill ships 22 reference decks in its `examples/` folder. For ReqMap use cases, prioritize:

| Style | Examples |
|---|---|
| Data / dashboard | `marp_facebook-ads.md`, `marp_fitness.md`, `marp_comparison.md` |
| Reference / sampler | `marp_sample.md` |

## ReqMap-Specific Components

### Conformity Status Colors

Map ReqMap's conformity enum to these colors consistently:

| Value | Color | Hex |
|---|---|---|
| C (Compliant) | Green | `#22c55e` |
| NC (Non-Compliant) | Red | `#ef4444` |
| PC (Partially Compliant) | Yellow | `#f5a623` |
| C TBC | Blue-grey | `#60a5fa` |
| TBC | Grey | `#6b7280` |
| NA / T | Muted | `#555` |

### Conformity Donut Chart

Use for executive summary slide. Circumference for r=110 ≈ 691.

```html
<svg viewBox="0 0 260 260" width="220" style="display:block;margin:auto;">
  <!-- NC segment -->
  <circle cx="130" cy="130" r="110" fill="none" stroke="#ef4444" stroke-width="28"
    stroke-dasharray="138 553" stroke-dashoffset="0" transform="rotate(-90 130 130)"/>
  <!-- PC segment -->
  <circle cx="130" cy="130" r="110" fill="none" stroke="#f5a623" stroke-width="28"
    stroke-dasharray="69 622" stroke-dashoffset="-138" transform="rotate(-90 130 130)"/>
  <!-- C segment -->
  <circle cx="130" cy="130" r="110" fill="none" stroke="#22c55e" stroke-width="28"
    stroke-dasharray="484 207" stroke-dashoffset="-207" transform="rotate(-90 130 130)"/>
  <text x="130" y="125" text-anchor="middle" fill="#fff" font-size="32" font-family="Outfit" font-weight="800">70%</text>
  <text x="130" y="148" text-anchor="middle" fill="#666" font-size="11" font-family="Raleway">Compliant</text>
</svg>
```

Adjust `stroke-dasharray` values: segment length = (pct/100) × 691. Offsets accumulate negatively.

### Requirements Summary Table

```html
<div style="font-family:'Raleway';font-size:0.72em;width:100%;">
  <div style="display:grid;grid-template-columns:2fr 1fr 1fr 1fr;gap:2px;margin-top:12px;">
    <!-- Header -->
    <div style="color:#555;font-size:0.8em;padding:6px 10px;">Requirement</div>
    <div style="color:#555;font-size:0.8em;padding:6px 10px;text-align:center;">Applicability</div>
    <div style="color:#555;font-size:0.8em;padding:6px 10px;text-align:center;">Conformity</div>
    <div style="color:#555;font-size:0.8em;padding:6px 10px;text-align:center;">Status</div>
    <!-- Row -->
    <div class="row" style="padding:8px 10px;color:#ccc;">REQ-001 — Title of requirement</div>
    <div class="row" style="padding:8px 10px;text-align:center;color:#999;">A</div>
    <div class="row" style="padding:8px 10px;text-align:center;">
      <span class="tag" style="background:#22c55e12;color:#22c55e;border:1px solid #22c55e22;">C</span>
    </div>
    <div class="row" style="padding:8px 10px;text-align:center;color:#555;">—</div>
  </div>
</div>
```

### Conformity Tag Variants

```html
<!-- Compliant -->
<span class="tag" style="background:#22c55e12;color:#22c55e;border:1px solid #22c55e22;">C</span>
<!-- Non-Compliant -->
<span class="tag" style="background:#ef444412;color:#ef4444;border:1px solid #ef444422;">NC</span>
<!-- Partial -->
<span class="tag" style="background:#f5a62312;color:#f5a623;border:1px solid #f5a62322;">PC</span>
<!-- TBC -->
<span class="tag" style="background:#6b728012;color:#6b7280;border:1px solid #6b728022;">TBC</span>
```

### Section Metric Card

```html
<div style="background:#080808;border:1px solid #111;border-radius:10px;padding:20px 24px;position:relative;overflow:hidden;">
  <div style="position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,var(--accent),transparent);"></div>
  <div style="color:#555;font-size:0.6em;font-family:'Outfit';text-transform:uppercase;letter-spacing:0.15em;">Section 4.2</div>
  <div style="color:#fff;font-size:2.2em;font-family:'Outfit';font-weight:800;margin:6px 0;">23</div>
  <div style="color:#999;font-size:0.7em;">requirements · 18C / 3PC / 2NC</div>
</div>
```

## Deck Structure for a Conformity Review

Recommended slide order:

1. **Cover** — document title, customer name, date, HEMERIA logo
2. **Executive Summary** — donut chart + 3 metric cards (total reqs, % compliant, open items)
3. **Scope** — which sections / standards were reviewed
4. **Per-Section Breakdown** — one slide per major section, stacked bar or table
5. **Non-Compliant Items** — table of NC/PC requirements with remarks
6. **TBC / Open Items** — timeline or checklist
7. **Conclusion** — next steps, sign-off

## Theme Template (HEMERIA Dark)

```yaml
---
marp: true
theme: default
paginate: true
size: 16:9
style: |
  @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;700;800&family=Raleway:wght@100;200;300&display=swap');
  :root {
    --accent: #1d4ed8;
    --accent-hover: #2563eb;
    --dark: #0a0a0f;
    --card: #0d0d14;
    --border: #1a1a2e;
    --body: #999;
    --label: #555;
    --muted: #444;
    --light: #f0f0f5;
    --green: #22c55e;
    --red: #ef4444;
    --yellow: #f5a623;
  }
  section { background: var(--dark); color: var(--light); font-family: 'Raleway', sans-serif; font-weight: 200; padding: 56px 72px; }
  h1 { font-family: 'Outfit'; font-weight: 800; font-size: 2.6em; color: var(--light); }
  h2 { font-family: 'Raleway'; font-weight: 100; font-size: 1.2em; color: #777; }
  h3 { font-family: 'Outfit'; font-weight: 600; font-size: 0.55em; color: var(--muted); text-transform: uppercase; letter-spacing: 0.2em; }
  strong { color: var(--accent); font-weight: 300; }
  section.lead { display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; }
  .row { transition: background 0.2s; border-radius: 6px; }
  .tag { font-family: 'Outfit'; font-weight: 600; font-size: 0.55em; letter-spacing: 0.12em; text-transform: uppercase; padding: 3px 10px; border-radius: 4px; }
---
```

> Accent color set to HEMERIA blue (`#1d4ed8`). Adjust if brand guidelines differ.

## Core Rules

1. One idea per slide. Overflow clips silently in Marp.
2. h1 = white. Accent for data highlights and brand elements only.
3. Body text `#999`, labels `#555`. Never darker than `#444`.
4. Max 6 rows per list/table slide — split into multiple slides if needed.
5. Use conformity donut on the executive summary slide always.
6. Relative paths only for local images (`./logo.png`).
7. PPTX export: `npx @marp-team/marp-cli slides.md --pptx --allow-local-files`
8. Animations and `<details>` only render in HTML mode — skip for PPTX output.

## Export Command

```bash
npx @marp-team/marp-cli slides.md --pptx --allow-local-files -o output/review-$(date +%Y%m%d).pptx
```
