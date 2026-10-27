# Learning Path

Self-paced curriculum across ML concepts, system design, data structures, side projects, and end-to-end builds. Folders are numbered in suggested reading order, but every track is independent.

## The tracks

### 01 · CONCEPTS
**ML / AI concept library**  
Activation functions, transformers, RAG, evaluation, vision, MCP, Docker / kubectl cheatsheets — 50+ pages.

- [Open track](01_concepts/index.html)

### 02 · COMPARISONS
**Cross-platform comparisons**  
LLM providers, agent dev kits, agentic frameworks, RAG strategies — side-by-side.

- [Open track](02_comparisons/index.html)

### 04 · SYSTEM DESIGN
**LLD + HLD, beginner → pro**  
OOP, SOLID, design patterns, UML, scalability, DBs, distributed systems, famous case studies. Includes the database selection guide.

- [Open track](04_system_design/index.html)

### 05 · DATA STRUCTURES
**DSA — beginner → advanced**  
Big-O through trees, graphs, tries, DP, interview patterns. 60-day roadmap.

- [Open track](05_data_structures/index.html)

### 06 · SIDE PROJECTS
**Applied project tracks**  
FastAPI service builds and LangGraph agent workflows, organized by technology under one side-projects hub.

- [Open track](06_side_projects/index.html)

### 07 · LEARNING PROJECTS
**Python OOP → architect**  
p1–p20: from student management CRUD to RAG platform, event-driven queue, API gateway.

- [Open track](07_learning_projects/learning_tracker.html)

### SYSTEM DESIGN ACADEMY
**15 hands-on builds from the systemdesign42 curriculum**  
Fundamentals (rate limiter, consistent hashing, bloom filter, idempotency, URL shortener), case studies (distributed counter, leaderboard, presence, saga, geo lookup), and AI engineering (agentic patterns, multi-agent, memory, context, knowledge Q&A with eval).

- [Open track](system_design_academy/index.html)

### INDUSTRY STANDARDS
**Anthropic · OpenAI · GitHub Copilot — best practices**  
Official guidance on building agents, designing tools, packaging skills, and wiring Claude Code / Codex into your SDLC. Five guides + two runnable sample projects + a stay-updated playbook, every claim cited to the official source.

- [Open track](industry_standards/index.html)

### PROGRAMMING LANGUAGES TRACK
**Learn new languages the way you already know Python**  
A Go &amp; Rust bootcamp (advantages, syntax vs Python, why they're fast, how to pick them up) plus 20 single-file parallel projects mirroring the Python `07_learning_projects`. Now also includes a **Web track** — JavaScript → TypeScript → React — with side-by-side Python/JS comparisons, a JS vs TS guide, and a mermaid-rich DOM explainer.

- [Open track](programming_languages_track/index.html)

### LATEST STACK
**The 2026 applied-AI toolkit — nine pages**  
Multimodal (STT/TTS/vision), Small Language Models, Agentic RAG, WebSockets vs WebRTC, fine-tuning (LoRA/QLoRA with code), voice bots, performance optimisation (quantisation/batching/caching), LLM evaluation, and LitServe. Every page has a mermaid diagram, a code example, and links to the original paper or vendor doc.

- [Open track](latest_stack/index.html)

### 📄 BLUEPRINT
**OOP to Architect blueprint**  
Single-page overview of the whole journey.

- [Open blueprint](OOP%20to%20Architect%20Learning%20Blueprint.html)

## Folder layout

```text
learning_path/
├── README.md                    ← you are here
├── OOP to Architect Learning Blueprint.html
│
├── 01_concepts/                 ← was: docs/
├── 02_comparisons/              ← was: docs_cross_platform_comparison/
├── 04_system_design/            ← was: system_design/
├── 05_data_structures/          ← was: data_structures/
├── 06_side_projects/            ← applied side-project tracks
│   ├── fastapi_projects/        ← FastAPI APIs, async, httpx, auth, production patterns
│   └── langgraph_projects/      ← LangGraph agent workflow examples
├── 07_learning_projects/        ← was: learning_projects/
├── system_design_academy/       ← 15 builds from the systemdesign42 curriculum
│   ├── system_design_fundamentals/   ← rate limiter, hashing, bloom, idempotency, URL shortener
│   ├── system_design_case_studies/   ← counter, leaderboard, presence, saga, geo lookup
│   └── ai_engineering/               ← agentic patterns, multi-agent, memory, context, knowledge Q&A
├── industry_standards/          ← Anthropic / OpenAI / GitHub Copilot best practices
│   ├── anthropic_building_agents.html, anthropic_tools_and_skills.html
│   ├── openai_agents_sdk.html, github_copilot_best_practices.html
│   ├── multi_scenario_playbook.html, stay_updated_motivated.html
│   ├── claude_code_in_sdlc/          ← sample: CLAUDE.md + custom skill + demo module
│   └── codex_in_sdlc/                ← sample: AGENTS.md + Agents-SDK reviewer agent
├── programming_languages_track/ ← Go & Rust bootcamp + 20 parallel projects, plus a JS/TS/React web track
│   ├── bootcamp/                ← why_go_rust, syntax_python_vs_{go,rust}, why_they_are_fast, pick_them_fast
│   ├── js_ts_react/             ← why_javascript, python_vs_javascript, javascript_vs_typescript, the_dom_explained
│   ├── go_projects/             ← p1–p10 Go (single main.go each, stdlib only)
│   └── rust_projects/           ← p1–p10 Rust (single src/main.rs each, stdlib only)
│
├── _notes/                      ← was: to_do/   (personal scratchpad)
└── _archive/                    ← old zip snapshots
```

## Suggested reading order

1. Skim [01_concepts](01_concepts/index.html) for the topic you're curious about.
2. For a real Python career path, follow [07_learning_projects](07_learning_projects/learning_tracker.html) top to bottom.
3. To prep for product-company interviews, do [04_system_design](04_system_design/roadmap.html) + [05_data_structures](05_data_structures/roadmap.html) in parallel (30 + 60 days).
4. To get hands-on with modern Python APIs, build [fastapi_projects](06_side_projects/fastapi_projects/index.html) P1 → P6 in order.
5. Use [langgraph_projects](06_side_projects/langgraph_projects/index.html) when you need agent orchestration.
6. To turn famous system-design patterns into running code, walk through [system_design_academy](system_design_academy/index.html) — fundamentals, case studies, and AI engineering, 15 projects total.
7. To level-up on official best practices for agents/tools/skills and to wire Claude Code or Codex into your day job, read [industry_standards](industry_standards/index.html) — five guides + two runnable sample projects + a stay-updated playbook.
8. To pick up Go and Rust quickly using the Python work you already know, run through [programming_languages_track](programming_languages_track/index.html) — bootcamp pages first, then read each Python p*n* alongside its Go and Rust twins, and use the JS/TS/React web track to prep for a JavaScript bootcamp.
9. For the 2026 applied-AI stack (multimodal, SLMs, agentic RAG, voice bots, fine-tuning, LitServe, eval), read [latest_stack](latest_stack/index.html) — nine focused pages with mermaid diagrams and runnable code.

Renames done in the move to numbered folders are tracked by git as renames (history preserved). Old zips moved to `_archive/`. The personal todo folder is now `_notes/` so it sorts to the bottom.
