# SlideDeck AI (Monorepo)

> **Enterprise-grade Presentation Generator.**
> *Unified repository for the Next.js Frontend and Python FastAPI Backend.*

## 1. Project Overview

**SlideDeck AI** is an automated presentation engine that converts user prompts into high-fidelity PowerPoint (`.pptx`) files while strictly adhering to corporate brand guidelines.

The engine supports **three generation modes**:

| Mode | Description |
|------|-------------|
| 🆕 **From Scratch** | Generate a presentation entirely from an AI prompt — no template needed. |
| 📄 **Template-Based** | Upload a `.pptx` template (master slides, brand assets, color scheme). The engine fills in content while preserving the template's design system. |
| 🔍 **Reference-Based** | Upload a reference `.pptx`. The engine analyzes its structure, fonts, colors, and layout patterns and produces a *new* deck that matches the style. |

This repository uses a **Polyglot Monorepo** architecture:

* **Backend (`apps/api`):** Python/FastAPI engine that orchestrates LLMs and manipulates OOXML.
* **Frontend (`apps/web`):** Next.js/React application serving as the "Canvas" interface.
* **Shared Contract:** The backend is the "Source of Truth" for data models. TypeScript interfaces are auto-generated from Python Pydantic models to ensure type safety across the stack.

---

## 2. Architecture & Data Flow

The system relies on a strict **Intermediate Representation (IR)** protocol:

```
┌──────────┐    prompt + file     ┌──────────────┐
│  Browser  │ ──────────────────▶ │   FastAPI     │
│ (Next.js) │                     │   Backend     │
└─────┬─────┘                     └──────┬───────┘
      │                                  │
      │  ◀── preview PNGs ──             │
      │  ◀── presentation JSON ──        ▼
      │                           ┌──────────────┐
      │                           │  Scanner      │ ← (optional) extract design
      │                           │  (template/   │   tokens from uploaded .pptx
      │                           │   reference)  │
      │                           └──────┬───────┘
      │                                  ▼
      │                           ┌──────────────┐
      │                           │  LLM Service  │ Gemini / OpenAI / Claude
      │                           │  (prompt →    │ → structured IR JSON
      │                           │   JSON)       │
      │                           └──────┬───────┘
      │                                  ▼
      │                           ┌──────────────┐
      │                           │  Builder      │ IR JSON → .pptx
      │                           │  (python-pptx)│
      │                           └──────┬───────┘
      │                                  ▼
      │                           ┌──────────────┐
      │                           │  Renderer     │ .pptx → PDF → PNGs
      │                           │  (LibreOffice)│
      └──────────◀────────────────└──────────────┘
```

**Step-by-step flow:**

1. **User Input:** User submits a prompt and optionally uploads a template or reference `.pptx`.
2. **API Call:** Frontend sends the prompt (+ file, if any) to `POST /api/generate`.
3. **Template Analysis** *(optional)*: If a file was provided, the `Scanner` extracts design tokens (colors, fonts, layouts, master slides) and injects them into the LLM prompt as constraints.
4. **LLM Processing:** The configured LLM provider (Gemini / OpenAI / Claude) generates a JSON object conforming to the IR schema.
5. **Generation:** The `Builder` uses `python-pptx` to create the `.pptx` — either from scratch or by populating the uploaded template's slide masters.
6. **Rendering:** LibreOffice converts each slide to PNG for preview.
7. **Response:** JSON (IR + metadata) + preview URLs are returned to the frontend.

---

## 3. Monorepo Structure

```text
/slidedeck-ai
│
├── /apps
│   ├── /api                # 🐍 Python Backend (FastAPI + python-pptx)
│   │   ├── /app            # Application Logic
│   │   │   ├── /core       # Config (env vars, settings)
│   │   │   ├── /engine     # Builder (IR→PPTX), Scanner (PPTX→tokens), Renderer (PPTX→PNG)
│   │   │   ├── /models     # Pydantic Models (SOURCE OF TRUTH for the IR)
│   │   │   ├── /services   # LLM Integration (Gemini, OpenAI, Claude)
│   │   │   └── /routers    # API Endpoints
│   │   ├── pyproject.toml  # Python Dependencies (Poetry)
│   │   └── Dockerfile      # Backend Container (w/ LibreOffice)
│   │
│   └── /web                # ⚛️ TypeScript Frontend (Next.js + Tailwind)
│       ├── /src
│       │   ├── /components # UI Components (Header, ChatPanel, SlidePreview)
│       │   ├── /lib        # API Client, Zustand Store
│       │   └── /types      # ⚠️ GENERATED TYPES (Do not edit manually)
│       ├── package.json    # JS Dependencies
│       └── Dockerfile      # Frontend Container
│
├── /scripts
│   └── gen-types.sh        # Script to sync Python Models -> TypeScript Interfaces
│
├── /infrastructure         # Infrastructure as Code
│   └── docker-compose.yml  # Orchestrates the full local stack
│
├── .env.example            # Required environment variables
├── .gitignore
└── README.md

```

---

## 4. Technology Stack

### Backend (`apps/api`)

* **Language:** Python 3.11+
* **Framework:** FastAPI (async, streaming-ready).
* **Core Libs:** `python-pptx` (OOXML manipulation), `pydantic` + `pydantic-settings` (validation & config).
* **AI Providers (pluggable):**
  * Google Gemini 2.0 Flash (`google-generativeai`)
  * OpenAI GPT-4o (`openai`)
  * Anthropic Claude 3.5 Sonnet (`anthropic`)
* **Rendering:** LibreOffice headless → PDF → PNG.

### Frontend (`apps/web`)

* **Framework:** Next.js 16 (App Router).
* **Styling:** Tailwind CSS v4.
* **State:** Zustand (client state).
* **Type Safety:** TypeScript (auto-synced with backend Pydantic models).

### DevOps

* **Containerization:** Docker & Docker Compose.
* **Scripts:** Shell (`gen-types.sh`).

---

## 5. Getting Started (Local Development)

### Prerequisites

* Docker & Docker Compose
* Node.js 20+
* Python 3.11+

### Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/your-org/slidedeck-ai.git
cd slidedeck-ai

# 2. Set up environment variables
cp .env.example .env
# Edit .env — at minimum, set ONE of the LLM provider keys:
#   GEMINI_API_KEY, OPENAI_API_KEY, or ANTHROPIC_API_KEY

# 3. Start the stack
docker-compose -f infrastructure/docker-compose.yml up --build
```

* **Frontend:** http://localhost:3000
* **Backend API Docs (Swagger):** http://localhost:8000/docs

### Running Without Docker

```bash
# Backend
cd apps/api && poetry install && uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal)
cd apps/web && npm install && npm run dev
```

---

## 6. Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | At least one | Google AI Studio API key. |
| `OPENAI_API_KEY` | provider key | OpenAI platform API key. |
| `ANTHROPIC_API_KEY` | is required | Anthropic Console API key. |
| `LLM_PROVIDER` | No | Default provider: `gemini`, `openai`, or `claude`. Defaults to `gemini`. |
| `OUTPUT_DIR` | No | Directory for generated files. Defaults to `/tmp/slidedeck-ai/output`. |

---

## 7. Development Workflow & Type Sync

### The Golden Rule: Python is the Source of Truth

Never manually edit the TypeScript interfaces in `apps/web/src/types/`. They are downstream artifacts generated from the Pydantic models.

### How to add a new field

1. **Modify the Pydantic model** in `apps/api/app/models/slide.py`:
   ```python
   class TextBox(BaseModel):
       # ... existing fields ...
       border_color: Optional[str] = None  # ← new field
   ```

2. **Regenerate TypeScript types:**
   ```bash
   ./scripts/gen-types.sh
   ```

3. **Use the new field** in the frontend — the TypeScript interface now includes `border_color`.

---

## 8. Key Scripts

| Command | Description |
| --- | --- |
| `docker-compose -f infrastructure/docker-compose.yml up` | Starts the full stack. |
| `./scripts/gen-types.sh` | Regenerates TS interfaces from Python models. |
| `cd apps/api && poetry install` | Installs backend deps locally (for IDE support). |
| `cd apps/web && npm install` | Installs frontend deps locally. |

---

## 9. Deployment Strategy (MVP)

Since the frontend and backend are decoupled, they can be deployed independently:

| Component | Recommended Platform | Notes |
|-----------|---------------------|-------|
| **Frontend** | Vercel | Point to `apps/web`. Vercel auto-detects Next.js. |
| **Backend** | Render / Railway / Fly.io | Point to `apps/api`. Use the Dockerfile. |

> [!IMPORTANT]
> The backend container **must** have `libreoffice` installed for slide preview rendering. The provided `Dockerfile` handles this automatically.

> [!NOTE]
> If deploying to a provider with ephemeral storage (e.g., Render), generated `.pptx` files will be lost on restart. For production, consider storing outputs in an S3-compatible bucket.

---

## 10. License & IP

Internal Tool — Proprietary.

---

## 11. Implementation Roadmap

This roadmap guides the development of SlideDeck AI, from core engine to production polish.

### Phase 1: Core Backend Engine ✅

- [x] **Data Modeling:** Pydantic IR models (`Presentation`, `Slide`, `TextBox`, `ImageElement`, `ChartElement`).
- [x] **Builder:** `python-pptx` engine converts IR JSON → `.pptx` (text, images, chart tables).
- [x] **LLM Service:** Gemini 2.0 Flash with structured JSON output.
- [x] **Renderer:** LibreOffice headless PPTX → PDF → PNG.
- [x] **API Routes:** `POST /api/generate`, `GET /api/download/{id}`, `GET /api/preview/{id}/{index}`.

### Phase 2: Frontend Canvas ✅

- [x] **Design System:** Dark violet/cyan theme, Inter + JetBrains Mono, Tailwind v4.
- [x] **ChatPanel:** Prompt input with examples and slide count selector.
- [x] **SlidePreview:** Navigation carousel with thumbnail strip.
- [x] **State + API:** Zustand store + typed `fetch` client.

### Phase 3: Template & Reference Support 🔧 *(next)*

- [ ] **Scanner:** Extract design tokens (colors, fonts, master layouts) from an uploaded `.pptx`.
- [ ] **Template Mode:** Populate a `.pptx` template with AI-generated content, preserving slide masters and brand.
- [ ] **Reference Mode:** Analyze a reference `.pptx` and produce a new deck matching its visual style.
- [ ] **Upload UI:** File upload component in ChatPanel for template/reference files.
- [ ] **API Update:** Extend `POST /api/generate` to accept optional `template_file` / `reference_file`.

### Phase 4: Multi-Provider LLM & Feedback Loop

- [ ] **Pluggable LLM:** Abstract the LLM call behind a provider interface (Gemini / OpenAI / Claude), selectable via `LLM_PROVIDER` env var.
- [ ] **Feedback Mechanism:** Allow users to request changes ("Make title bigger", "Change color") → sends a refinement prompt to the LLM with the current IR as context.
- [ ] **Conversation History:** Maintain prompt history per session for iterative refinement.

### Phase 5: Production Polish

- [ ] **Theme Engine:** Predefined color palettes and font pairings.
- [ ] **Asset Management:** Unsplash/Pexels integration for stock images.
- [ ] **Export Improvements:** Direct download button (already functional), batch export, PDF export.
- [ ] **Persistent Storage:** S3-compatible object store for generated files (replaces ephemeral `/tmp`).