---
marp: true
theme: default
paginate: true
size: 16:9
style: |
  @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;700;800&family=Raleway:wght@100;200;300;400&display=swap');
  :root {
    --accent: #1d4ed8;
    --accent2: #3b82f6;
    --dark: #0a0a0f;
    --card: #0d0d16;
    --border: #1a1a2e;
    --body: #999;
    --label: #555;
    --muted: #444;
    --light: #f0f0f5;
    --green: #22c55e;
    --red: #ef4444;
    --yellow: #f5a623;
  }
  section {
    background: var(--dark);
    color: var(--light);
    font-family: 'Raleway', sans-serif;
    font-weight: 200;
    padding: 52px 72px;
  }
  h1 { font-family: 'Outfit'; font-weight: 800; font-size: 2.4em; color: var(--light); margin: 0 0 8px 0; }
  h2 { font-family: 'Raleway'; font-weight: 100; font-size: 1.15em; color: #777; margin: 0 0 28px 0; }
  h3 { font-family: 'Outfit'; font-weight: 600; font-size: 0.55em; color: var(--muted); text-transform: uppercase; letter-spacing: 0.2em; margin: 0 0 16px 0; }
  strong { color: var(--accent2); font-weight: 400; }
  ul { color: var(--body); font-size: 0.82em; line-height: 1.9; padding-left: 1.2em; }
  li { margin-bottom: 2px; }
  section.lead { display: flex; flex-direction: column; justify-content: center; align-items: flex-start; text-align: left; }
  section.cover { display: flex; flex-direction: column; justify-content: center; align-items: flex-start; }
  .tag { font-family: 'Outfit'; font-weight: 600; font-size: 0.55em; letter-spacing: 0.12em; text-transform: uppercase; padding: 3px 10px; border-radius: 4px; }
  .pill { display: inline-block; font-family: 'Outfit'; font-weight: 600; font-size: 0.58em; padding: 4px 14px; border-radius: 20px; letter-spacing: 0.08em; }
  footer { font-size: 0.5em; color: #333; }
---

<!-- _paginate: false -->
<!-- _footer: '' -->

<div style="height:100%;display:flex;flex-direction:column;justify-content:center;">
  <div style="width:48px;height:3px;background:var(--accent);margin-bottom:32px;"></div>
  <div style="font-family:'Outfit';font-weight:800;font-size:3.2em;color:var(--light);line-height:1.05;">ReqMap</div>
  <div style="font-family:'Raleway';font-weight:100;font-size:1.3em;color:#666;margin-top:10px;">PDF Requirements · Structured Review</div>
  <div style="margin-top:48px;display:flex;gap:12px;">
    <span class="pill" style="background:#1d4ed820;color:var(--accent2);border:1px solid #1d4ed840;">v1.0 MVP</span>
    <span class="pill" style="background:#22222a;color:#555;border:1px solid #2a2a3a;">HEMERIA · 2026</span>
  </div>
</div>

---

### The Problem

# Manual Review at Scale

<div style="display:flex;gap:24px;margin-top:8px;">
  <div style="flex:1;background:var(--card);border:1px solid var(--border);border-radius:10px;padding:22px 24px;position:relative;overflow:hidden;">
    <div style="position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,#ef4444,transparent);"></div>
    <div style="font-family:'Outfit';font-weight:700;font-size:1.05em;color:#ccc;margin-bottom:8px;">PDF documents</div>
    <div style="color:#666;font-size:0.75em;line-height:1.7;">Hundreds of pages · mixed layouts · tables · scanned images · inconsistent numbering</div>
  </div>
  <div style="flex:1;background:var(--card);border:1px solid var(--border);border-radius:10px;padding:22px 24px;position:relative;overflow:hidden;">
    <div style="position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,#f5a623,transparent);"></div>
    <div style="font-family:'Outfit';font-weight:700;font-size:1.05em;color:#ccc;margin-bottom:8px;">Manual extraction</div>
    <div style="color:#666;font-size:0.75em;line-height:1.7;">Copy-paste into spreadsheets · error-prone · slow · no traceability · hard to share</div>
  </div>
  <div style="flex:1;background:var(--card);border:1px solid var(--border);border-radius:10px;padding:22px 24px;position:relative;overflow:hidden;">
    <div style="position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,var(--accent),transparent);"></div>
    <div style="font-family:'Outfit';font-weight:700;font-size:1.05em;color:#ccc;margin-bottom:8px;">ReqMap</div>
    <div style="color:#666;font-size:0.75em;line-height:1.7;">Upload PDF → structured nodes → reviewable in browser → exportable · in seconds</div>
  </div>
</div>

---

### What it does

# PDF → Structured Nodes

<div style="display:flex;align-items:center;gap:0;margin-top:16px;font-family:'Outfit';font-size:0.72em;">

  <div style="background:#0d0d16;border:1px solid #1a1a2e;border-radius:8px;padding:14px 20px;text-align:center;min-width:110px;">
    <div style="font-size:1.8em;margin-bottom:4px;">📄</div>
    <div style="color:#ccc;font-weight:600;">PDF</div>
    <div style="color:#555;font-size:0.8em;margin-top:2px;">any layout</div>
  </div>

  <div style="color:#333;font-size:1.4em;padding:0 8px;">→</div>

  <div style="background:#0d0d16;border:1px solid #1a1a2e;border-radius:8px;padding:14px 20px;text-align:center;min-width:130px;">
    <div style="font-size:1.8em;margin-bottom:4px;">🔍</div>
    <div style="color:#ccc;font-weight:600;">Extract</div>
    <div style="color:#555;font-size:0.8em;margin-top:2px;">text + OCR</div>
  </div>

  <div style="color:#333;font-size:1.4em;padding:0 8px;">→</div>

  <div style="background:#0d0d16;border:1px solid #1a1a2e;border-radius:8px;padding:14px 20px;text-align:center;min-width:130px;">
    <div style="font-size:1.8em;margin-bottom:4px;">🧹</div>
    <div style="color:#ccc;font-weight:600;">Clean MD</div>
    <div style="color:#555;font-size:0.8em;margin-top:2px;">noise removed</div>
  </div>

  <div style="color:#333;font-size:1.4em;padding:0 8px;">→</div>

  <div style="background:#0d0d16;border:1px solid #1a1a2e;border-radius:8px;padding:14px 20px;text-align:center;min-width:130px;">
    <div style="font-size:1.8em;margin-bottom:4px;">🗂️</div>
    <div style="color:#ccc;font-weight:600;">Parse Nodes</div>
    <div style="color:#555;font-size:0.8em;margin-top:2px;">title · req</div>
  </div>

  <div style="color:#333;font-size:1.4em;padding:0 8px;">→</div>

  <div style="background:#1d4ed815;border:1px solid #1d4ed840;border-radius:8px;padding:14px 20px;text-align:center;min-width:130px;">
    <div style="font-size:1.8em;margin-bottom:4px;">✅</div>
    <div style="color:var(--accent2);font-weight:600;">Review UI</div>
    <div style="color:#555;font-size:0.8em;margin-top:2px;">edit · export</div>
  </div>

</div>

<div style="margin-top:28px;color:#555;font-size:0.72em;">
  Two node types produced: &nbsp;<span class="tag" style="background:#1d4ed818;color:var(--accent2);border:1px solid #1d4ed830;">title</span>&nbsp; section headings &nbsp;·&nbsp; <span class="tag" style="background:#22c55e12;color:#22c55e;border:1px solid #22c55e22;">requirement</span>&nbsp; individual requirements with ID, applicability, conformity
</div>

---

### System Architecture

# Three-Layer Design

<div style="display:flex;flex-direction:column;gap:10px;margin-top:4px;">

  <div style="background:var(--card);border:1px solid var(--border);border-radius:10px;padding:16px 24px;display:flex;align-items:center;gap:20px;">
    <div style="min-width:140px;font-family:'Outfit';font-weight:700;font-size:0.85em;color:var(--accent2);">Frontend</div>
    <div style="color:#666;font-size:0.72em;flex:1;">Next.js 15 · React 19 · TanStack Query · Tailwind — upload, customer selector, node review table, conformity editor, dashboard</div>
    <div style="font-family:'Outfit';font-size:0.6em;color:#333;">:3000</div>
  </div>

  <div style="text-align:center;color:#2a2a3e;font-size:0.8em;">▕&nbsp;REST API&nbsp;▏</div>

  <div style="background:var(--card);border:1px solid var(--border);border-radius:10px;padding:16px 24px;display:flex;align-items:center;gap:20px;">
    <div style="min-width:140px;font-family:'Outfit';font-weight:700;font-size:0.85em;color:var(--accent2);">Backend</div>
    <div style="color:#666;font-size:0.72em;flex:1;">FastAPI · SQLAlchemy 2 async · SQLite · background task processing · routers → services → repositories → ORM</div>
    <div style="font-family:'Outfit';font-size:0.6em;color:#333;">:8090</div>
  </div>

  <div style="text-align:center;color:#2a2a3e;font-size:0.8em;">▕&nbsp;Python import&nbsp;▏</div>

  <div style="background:var(--card);border:1px solid var(--border);border-radius:10px;padding:16px 24px;display:flex;align-items:center;gap:20px;">
    <div style="min-width:140px;font-family:'Outfit';font-weight:700;font-size:0.85em;color:var(--accent2);">reqmap lib</div>
    <div style="color:#666;font-size:0.72em;flex:1;">Standalone Python library · PDFExtractor · NodeParser · CLI-usable · customer-parameterized patterns</div>
    <div style="font-family:'Outfit';font-size:0.6em;color:#333;">reqmap/</div>
  </div>

</div>

---

### reqmap library

# Extraction Pipeline

<div style="font-family:'Outfit';font-size:0.7em;margin-top:12px;">

  <div style="display:flex;gap:8px;align-items:stretch;">

    <div style="flex:1;background:var(--card);border:1px solid var(--border);border-radius:8px;padding:16px 18px;">
      <div style="color:var(--accent2);font-weight:600;margin-bottom:8px;">① PDFExtractor</div>
      <div style="color:#666;font-size:0.9em;line-height:1.7;">pymupdf4llm → raw markdown<br>Header/footer removal<br>Inline image OCR injection<br>Markdown cleaning</div>
      <div style="margin-top:10px;color:#333;font-size:0.8em;font-family:'Raleway';">extractor.py</div>
    </div>

    <div style="display:flex;align-items:center;color:#2a2a3e;font-size:1.3em;padding:0 4px;">→</div>

    <div style="flex:1;background:var(--card);border:1px solid var(--border);border-radius:8px;padding:16px 18px;">
      <div style="color:var(--accent2);font-weight:600;margin-bottom:8px;">② NodeParser</div>
      <div style="color:#666;font-size:0.9em;line-height:1.7;">Walks cleaned markdown<br>Matches req_id_pattern<br>Matches title_pattern<br>Filters noise_patterns</div>
      <div style="margin-top:10px;color:#333;font-size:0.8em;font-family:'Raleway';">node_parser.py</div>
    </div>

    <div style="display:flex;align-items:center;color:#2a2a3e;font-size:1.3em;padding:0 4px;">→</div>

    <div style="flex:1;background:#1d4ed810;border:1px solid #1d4ed830;border-radius:8px;padding:16px 18px;">
      <div style="color:var(--accent2);font-weight:600;margin-bottom:8px;">③ Node list</div>
      <div style="color:#666;font-size:0.9em;line-height:1.7;">order · type<br>section · req_id<br>title · description<br>applicability · conformity</div>
      <div style="margin-top:10px;color:#333;font-size:0.8em;font-family:'Raleway';">[{…}, {…}, …]</div>
    </div>

  </div>

  <div style="margin-top:14px;background:#0d0d0d;border:1px solid #1a1a1a;border-radius:6px;padding:10px 16px;font-family:monospace;color:#555;font-size:0.85em;">
    python -m reqmap path/to/doc.pdf &nbsp;<span style="color:#333;">--json</span> &nbsp;<span style="color:#333;">--no-ocr</span> &nbsp;<span style="color:#333;">-v</span>
  </div>

</div>

---

### Customer Configuration

# Zero-Code Customization

<div style="display:flex;gap:20px;margin-top:8px;">

  <div style="flex:1;">
    <div style="color:#555;font-size:0.7em;font-family:'Outfit';text-transform:uppercase;letter-spacing:0.15em;margin-bottom:12px;">config/customers.json</div>
    <div style="background:#0d0d0d;border:1px solid #1a1a1a;border-radius:8px;padding:16px 18px;font-family:monospace;font-size:0.62em;color:#666;line-height:1.8;">
      <span style="color:#1d4ed8;">"airbus"</span>: {<br>
      &nbsp;&nbsp;<span style="color:#555;">"label"</span>: <span style="color:#777;">"Airbus STD"</span>,<br>
      &nbsp;&nbsp;<span style="color:#555;">"req_id_pattern"</span>: <span style="color:#777;">"REQ-\\d+"</span>,<br>
      &nbsp;&nbsp;<span style="color:#555;">"title_pattern"</span>: <span style="color:#777;">"^#{1,3}\\s"</span>,<br>
      &nbsp;&nbsp;<span style="color:#555;">"noise_patterns"</span>: [<span style="color:#777;">"^Page \\d"</span>, …]<br>
      }
    </div>
  </div>

  <div style="flex:1;display:flex;flex-direction:column;gap:10px;justify-content:center;">
    <div style="background:var(--card);border:1px solid var(--border);border-radius:8px;padding:14px 18px;">
      <div style="font-family:'Outfit';font-weight:600;font-size:0.75em;color:#ccc;margin-bottom:4px;">Add a new customer</div>
      <div style="color:#666;font-size:0.68em;">Edit JSON only — no code change. Frontend populates the upload dropdown from <code style="color:#444;">GET /api/v1/customers</code> automatically.</div>
    </div>
    <div style="background:var(--card);border:1px solid var(--border);border-radius:8px;padding:14px 18px;">
      <div style="font-family:'Outfit';font-weight:600;font-size:0.75em;color:#ccc;margin-bottom:4px;">Pattern parameters</div>
      <div style="color:#666;font-size:0.68em;"><strong style="color:#888;">req_id_pattern</strong> — identifies requirement lines<br><strong style="color:#888;">title_pattern</strong> — identifies section headers<br><strong style="color:#888;">noise_patterns</strong> — lines to strip out</div>
    </div>
  </div>

</div>

---

### Backend

# FastAPI Service

<div style="display:flex;gap:20px;margin-top:4px;">

  <div style="flex:1.2;">
    <div style="color:#555;font-size:0.65em;font-family:'Outfit';text-transform:uppercase;letter-spacing:0.15em;margin-bottom:10px;">Layered architecture</div>
    <div style="display:flex;flex-direction:column;gap:6px;font-size:0.7em;">
      <div style="background:var(--card);border:1px solid var(--border);border-radius:6px;padding:10px 14px;display:flex;align-items:center;gap:12px;">
        <span style="color:var(--accent2);font-family:'Outfit';font-weight:600;min-width:80px;">routers/</span>
        <span style="color:#666;">HTTP · request validation · response shaping</span>
      </div>
      <div style="text-align:center;color:#2a2a3e;font-size:0.8em;">↓</div>
      <div style="background:var(--card);border:1px solid var(--border);border-radius:6px;padding:10px 14px;display:flex;align-items:center;gap:12px;">
        <span style="color:var(--accent2);font-family:'Outfit';font-weight:600;min-width:80px;">services/</span>
        <span style="color:#666;">orchestration · background tasks · reqmap calls</span>
      </div>
      <div style="text-align:center;color:#2a2a3e;font-size:0.8em;">↓</div>
      <div style="background:var(--card);border:1px solid var(--border);border-radius:6px;padding:10px 14px;display:flex;align-items:center;gap:12px;">
        <span style="color:var(--accent2);font-family:'Outfit';font-weight:600;min-width:80px;">repositories/</span>
        <span style="color:#666;">data access · async sessions</span>
      </div>
      <div style="text-align:center;color:#2a2a3e;font-size:0.8em;">↓</div>
      <div style="background:var(--card);border:1px solid var(--border);border-radius:6px;padding:10px 14px;display:flex;align-items:center;gap:12px;">
        <span style="color:var(--accent2);font-family:'Outfit';font-weight:600;min-width:80px;">models/</span>
        <span style="color:#666;">SQLAlchemy 2 async ORM · SQLite</span>
      </div>
    </div>
  </div>

  <div style="flex:1;">
    <div style="color:#555;font-size:0.65em;font-family:'Outfit';text-transform:uppercase;letter-spacing:0.15em;margin-bottom:10px;">Key endpoints</div>
    <div style="display:flex;flex-direction:column;gap:6px;font-size:0.68em;font-family:monospace;">
      <div style="background:#0d0d0d;border:1px solid #1a1a1a;border-radius:5px;padding:8px 12px;color:#666;">POST &nbsp;<span style="color:#ccc;">/api/v1/documents/upload</span></div>
      <div style="background:#0d0d0d;border:1px solid #1a1a1a;border-radius:5px;padding:8px 12px;color:#666;">GET &nbsp;&nbsp;<span style="color:#ccc;">/api/v1/documents/{id}</span></div>
      <div style="background:#0d0d0d;border:1px solid #1a1a1a;border-radius:5px;padding:8px 12px;color:#666;">PATCH <span style="color:#ccc;">/api/v1/nodes/{id}</span></div>
      <div style="background:#0d0d0d;border:1px solid #1a1a1a;border-radius:5px;padding:8px 12px;color:#666;">GET &nbsp;&nbsp;<span style="color:#ccc;">/api/v1/customers</span></div>
      <div style="background:#0d0d0d;border:1px solid #1a1a1a;border-radius:5px;padding:8px 12px;color:#666;">DELETE <span style="color:#ccc;">/api/v1/documents/{id}</span></div>
    </div>
    <div style="margin-top:10px;color:#333;font-size:0.62em;font-family:'Raleway';">Pydantic v2 schemas · interactive docs at /api/docs</div>
  </div>

</div>

---

### Frontend

# Review Interface

<div style="display:flex;gap:20px;margin-top:8px;">

  <div style="flex:1;display:flex;flex-direction:column;gap:10px;">

    <div style="background:var(--card);border:1px solid var(--border);border-radius:8px;padding:16px 20px;position:relative;overflow:hidden;">
      <div style="position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,var(--accent),transparent);"></div>
      <div style="font-family:'Outfit';font-weight:700;font-size:0.8em;color:#ccc;margin-bottom:6px;">① Upload</div>
      <div style="color:#666;font-size:0.7em;line-height:1.6;">Select PDF · choose customer extractor · upload triggers background processing · status polling</div>
    </div>

    <div style="background:var(--card);border:1px solid var(--border);border-radius:8px;padding:16px 20px;position:relative;overflow:hidden;">
      <div style="position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,var(--accent),transparent);"></div>
      <div style="font-family:'Outfit';font-weight:700;font-size:0.8em;color:#ccc;margin-bottom:6px;">② Dashboard</div>
      <div style="color:#666;font-size:0.7em;line-height:1.6;">Document list · conformity pie chart per document · delete · open for review</div>
    </div>

    <div style="background:var(--card);border:1px solid var(--border);border-radius:8px;padding:16px 20px;position:relative;overflow:hidden;">
      <div style="position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,var(--accent),transparent);"></div>
      <div style="font-family:'Outfit';font-weight:700;font-size:0.8em;color:#ccc;margin-bottom:6px;">③ Node Review</div>
      <div style="color:#666;font-size:0.7em;line-height:1.6;">Inline edit of applicability &amp; conformity · markdown description viewer · expand/collapse · sorted by order</div>
    </div>

  </div>

  <div style="flex:1;">
    <div style="color:#555;font-size:0.65em;font-family:'Outfit';text-transform:uppercase;letter-spacing:0.15em;margin-bottom:12px;">Conformity values</div>
    <div style="display:flex;flex-direction:column;gap:6px;font-size:0.72em;">
      <div style="display:flex;align-items:center;gap:10px;padding:7px 0;border-bottom:1px solid #111;">
        <span class="tag" style="background:#22c55e12;color:#22c55e;border:1px solid #22c55e22;min-width:60px;text-align:center;">C</span>
        <span style="color:#666;">Compliant</span>
      </div>
      <div style="display:flex;align-items:center;gap:10px;padding:7px 0;border-bottom:1px solid #111;">
        <span class="tag" style="background:#ef444412;color:#ef4444;border:1px solid #ef444422;min-width:60px;text-align:center;">NC</span>
        <span style="color:#666;">Non-Compliant</span>
      </div>
      <div style="display:flex;align-items:center;gap:10px;padding:7px 0;border-bottom:1px solid #111;">
        <span class="tag" style="background:#f5a62312;color:#f5a623;border:1px solid #f5a62322;min-width:60px;text-align:center;">PC</span>
        <span style="color:#666;">Partially Compliant</span>
      </div>
      <div style="display:flex;align-items:center;gap:10px;padding:7px 0;border-bottom:1px solid #111;">
        <span class="tag" style="background:#60a5fa12;color:#60a5fa;border:1px solid #60a5fa22;min-width:60px;text-align:center;">C TBC</span>
        <span style="color:#666;">Compliant — to be confirmed</span>
      </div>
      <div style="display:flex;align-items:center;gap:10px;padding:7px 0;">
        <span class="tag" style="background:#6b728012;color:#6b7280;border:1px solid #6b728022;min-width:60px;text-align:center;">TBC</span>
        <span style="color:#666;">To be confirmed</span>
      </div>
    </div>
  </div>

</div>

---

### Deployment

# Docker · Single Command

<div style="display:flex;gap:20px;margin-top:12px;">

  <div style="flex:1;">
    <div style="background:#0d0d0d;border:1px solid #1a1a1a;border-radius:8px;padding:18px 20px;font-family:monospace;font-size:0.65em;color:#555;line-height:1.9;">
      <span style="color:#2a2a3e;"># Production</span><br>
      <span style="color:#888;">docker compose up --build</span><br>
      <br>
      <span style="color:#2a2a3e;"># Development (hot reload)</span><br>
      <span style="color:#888;">docker compose -f docker-compose.dev.yml up --build</span>
    </div>
  </div>

  <div style="flex:1;display:flex;flex-direction:column;gap:10px;">
    <div style="background:var(--card);border:1px solid var(--border);border-radius:8px;padding:14px 18px;display:flex;justify-content:space-between;align-items:center;">
      <div>
        <div style="font-family:'Outfit';font-weight:600;font-size:0.75em;color:#ccc;">Frontend</div>
        <div style="color:#555;font-size:0.65em;margin-top:2px;">Next.js · hot reload in dev</div>
      </div>
      <span class="tag" style="background:#1d4ed818;color:var(--accent2);border:1px solid #1d4ed830;">:3000</span>
    </div>
    <div style="background:var(--card);border:1px solid var(--border);border-radius:8px;padding:14px 18px;display:flex;justify-content:space-between;align-items:center;">
      <div>
        <div style="font-family:'Outfit';font-weight:600;font-size:0.75em;color:#ccc;">Backend API</div>
        <div style="color:#555;font-size:0.65em;margin-top:2px;">FastAPI · uvicorn</div>
      </div>
      <span class="tag" style="background:#1d4ed818;color:var(--accent2);border:1px solid #1d4ed830;">:8090</span>
    </div>
    <div style="background:var(--card);border:1px solid var(--border);border-radius:8px;padding:14px 18px;display:flex;justify-content:space-between;align-items:center;">
      <div>
        <div style="font-family:'Outfit';font-weight:600;font-size:0.75em;color:#ccc;">API Docs</div>
        <div style="color:#555;font-size:0.65em;margin-top:2px;">Swagger UI</div>
      </div>
      <span class="tag" style="background:#22222a;color:#555;border:1px solid #2a2a3a;">/api/docs</span>
    </div>
  </div>

</div>

---

### Roadmap

# What's Next

<div style="display:flex;flex-direction:column;gap:0;margin-top:16px;position:relative;">

  <div style="position:absolute;left:16px;top:0;bottom:0;width:1px;background:linear-gradient(180deg,var(--accent),#1a1a2e);"></div>

  <div style="display:flex;gap:20px;align-items:flex-start;padding-bottom:24px;padding-left:44px;position:relative;">
    <div style="position:absolute;left:10px;top:4px;width:13px;height:13px;border-radius:50%;background:var(--accent);border:2px solid var(--dark);"></div>
    <div style="flex:1;">
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:6px;">
        <span style="font-family:'Outfit';font-weight:700;font-size:0.85em;color:#ccc;">v1.0 — MVP</span>
        <span class="tag" style="background:#22c55e12;color:#22c55e;border:1px solid #22c55e22;">Current</span>
      </div>
      <div style="color:#666;font-size:0.7em;">Upload PDF · customer extractor selection · background processing · node review · conformity editing · dashboard</div>
    </div>
  </div>

  <div style="display:flex;gap:20px;align-items:flex-start;padding-bottom:24px;padding-left:44px;position:relative;">
    <div style="position:absolute;left:10px;top:4px;width:13px;height:13px;border-radius:50%;background:#1a1a2e;border:2px solid var(--accent);"></div>
    <div style="flex:1;">
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:6px;">
        <span style="font-family:'Outfit';font-weight:700;font-size:0.85em;color:#ccc;">v1.1</span>
        <span class="tag" style="background:#f5a62312;color:#f5a623;border:1px solid #f5a62322;">Planned</span>
      </div>
      <div style="color:#666;font-size:0.7em;">JWT authentication · WebSocket real-time collaboration (stubs already in config)</div>
    </div>
  </div>

  <div style="display:flex;gap:20px;align-items:flex-start;padding-left:44px;position:relative;">
    <div style="position:absolute;left:10px;top:4px;width:13px;height:13px;border-radius:50%;background:#1a1a2e;border:2px solid #2a2a3e;"></div>
    <div style="flex:1;">
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:6px;">
        <span style="font-family:'Outfit';font-weight:700;font-size:0.85em;color:#ccc;">v1.2</span>
        <span class="tag" style="background:#6b728012;color:#6b7280;border:1px solid #6b728022;">Backlog</span>
      </div>
      <div style="color:#666;font-size:0.7em;">DOCX support · CSV / Excel export · audit trail</div>
    </div>
  </div>

</div>

---

<!-- _paginate: false -->
<!-- _footer: '' -->

<div style="height:100%;display:flex;flex-direction:column;justify-content:center;">
  <div style="width:48px;height:3px;background:var(--accent);margin-bottom:32px;"></div>
  <div style="font-family:'Outfit';font-weight:800;font-size:2.4em;color:var(--light);line-height:1.1;">Questions?</div>
  <div style="font-family:'Raleway';font-weight:100;font-size:1.1em;color:#555;margin-top:10px;">ReqMap · HEMERIA · 2026</div>
  <div style="margin-top:40px;font-size:0.68em;color:#333;font-family:monospace;">github · docs · /api/docs</div>
</div>
