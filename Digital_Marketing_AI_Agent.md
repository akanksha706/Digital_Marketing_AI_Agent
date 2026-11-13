# Digital Marketing AI Agent — Comprehensive Architecture & Codebase Guide

---

## 1. Executive Summary & Purpose

The **Digital Marketing AI Agent** is an autonomous, full-stack creative marketing platform. It converts raw product concepts, user ideas, website URLs, or uploaded photographs into publication-grade visual campaigns, high-definition video reels, and social media copy in under sixty seconds.

### The Problem It Solves
Traditional social media marketing requires multiple tools and manual coordination across copywriters, graphic designers, stock photo searches, and video editors:
- Hours spent brainstorming copy, quotes, and hashtags.
- Searching for royalty-free stock imagery or fighting image diffusion prompts.
- Manually adjusting typography, logos, and contrast in desktop editing software.
- Animating static assets into social video reels for platforms like Instagram, TikTok, and YouTube Shorts.

### What the AI Agent Delivers Automatically
1. **Publication-Ready Social Media Posters (1080 × 1080)**: Studio-quality images with dynamic headlines, meaningful quotes, brand taglines, and integrated company logos positioned in clean headroom or floor spaces.
2. **14-Second High-Definition Video Reels (720 × 1280, 9:16 Vertical)**: Cinema-grade animated videos with natural character movements (gestures, facial reactions, eye contact), gentle ambient camera push-in, and professional brand outro cards.
3. **Platform-Optimized Copywriting**: Complete post captions formatted with structured bullet points, emojis, calls to action, and relevant hashtags tailored for Instagram, LinkedIn, and X.
4. **Automated Publishing & Scheduling**: Direct integration with LinkedIn and automated scheduling queues.

---

## 2. End-to-End Creative Pipeline

Every creative request flows through a five-stage intelligent pipeline that guarantees topical accuracy, physical realism, and typography readability:

```
                  ┌──────────────────────────────────────────────┐
                  │       Input: User Prompt, URL, or Photo      │
                  └──────────────────────┬───────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ Stage 1: Real-Time Web Knowledge Retrieval (Firecrawl Search Engine)            │
│ • Performs live web lookups to retrieve up-to-the-minute product information,   │
│   cultural facts, architectural styles, and authentic aesthetic benchmarks.     │
│ • Eliminates AI hallucinations, outdated models, and generic templates.         │
└────────────────────────────────────────┬────────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ Stage 2: Creative Art Direction & Story Copywriting (LLaMA 3.1 8B Instruct)     │
│ • Acts as the Creative Director, Copywriter, and Visual Cinematographer.        │
│ • Generates compelling editorial headlines, inspirational quotes, and captions. │
│ • Produces a detailed photographic brief specifying lighting, camera lenses,    │
│   compositional headroom, and realistic character actions.                      │
└────────────────────────────────────────┬────────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ Stage 3: Cinema-Grade Image Generation (Flux.1 Schnell Diffusion)               │
│ • Renders 8K-quality photorealistic visuals from the creative brief.            │
│ • Applies strict physical reality safeguards: complete human bodies, natural   │
│   hands, and firmly supported objects (no floating or disembodied items).       │
└────────────────────────────────────────┬────────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ Stage 4: Neural Video Motion & Reel Synthesis (Wan 2.2 / LTX-Video)             │
│ • Animates characters with smooth biological movement (smiling, turning, hands).│
│ • Paced across 14 seconds with smooth commercial motion interpolation and       │
│   gradual camera push-in, avoiding jerky loops or frantic speedups.             │
└────────────────────────────────────────┬────────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ Stage 5: Studio Compositing, Safe Space Analysis & Brand Outro                  │
│ • Scans the visual background to find unobstructed headroom or lower thirds.   │
│ • Layers typography with luminous contrast and 3D drop shadows.                 │
│ • Attaches the 42Works brand mark and animated signature logo outro.            │
└────────────────────────────────────────┬────────────────────────────────────────┘
                                         │
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │ Ready-to-Publish Poster, Video Reel & Caption│
                  └──────────────────────────────────────────────┘
```

---

## 3. Core Functional Capabilities

### A. Prompt-to-Poster & Video Studio
Users enter a concept in plain everyday phrasing (for example: *"Promote our new custom AI workflow software"* or *"Create an elegant Guru Nanak Jayanti celebration poster"*). The system:
- Grounds the request in real-world facts.
- Generates the clean background artwork.
- Performs computer-vision safe-space analysis to position the text without covering faces or central subjects.
- Renders the composite poster and animates a matching 14-second video reel.

### B. URL Campaign Synthesizer
Users paste a web address or product landing page. The built-in web crawler extracts the core value proposition, key features, and brand tone to draft an aligned marketing poster and social post automatically.

### C. Custom Photo Upload Studio
Users upload their own product photos or company images. The system evaluates the image, adjusts framing and balance, applies safety checks, and overlays editorial typography and brand elements.

### D. Google Calendar Holiday Inspirations
Connects to Google Calendar to track upcoming holidays, national observances, and cultural events, presenting ready-made creative concepts before deadlines arrive.

### E. Social Scheduling & LinkedIn Publishing
Enables one-click publishing directly to LinkedIn company pages or adds posts to an automated calendar queue with custom scheduled dates and times.

### F. Multi-Tier Review & Approval System
Allows marketing managers to review generated assets, cycle through states (`DRAFT`, `IN_REVIEW`, `APPROVED`, `REJECTED`), edit text overlays interactively, and export high-resolution PNGs.

---

## 4. Built-In Quality Safeguards

To prevent the common visual flaws found in generative AI models, this system enforces four strict automated safeguards:

### 1. Physical Gravity & Complete Human Anatomy Shield
- **Complete Bodies**: Every human figure must be fully formed, showing their head, face, eyes, neck, shoulders, and torso. Disembodied hands, floating arms, and headless figures are strictly prevented.
- **Support by Gravity**: Every object (dish, bowl, cup, phone, tool, laptop) must be supported—either resting firmly on a solid surface (such as a wooden table or desk) or held securely from underneath by visible hands with natural fingers. Floating or levitating objects in mid-air are forbidden.

### 2. Topic Grounding & Anti-Cross-Contamination
- When creating posters for modern commercial products (e.g., enterprise software, financial tools, retail), the AI grounds the visual setting strictly in modern architectural environments and professional actions.
- Traditional and cultural events remain true to authentic historical iconography (e.g., authentic portraits, sacred shrines, traditional lighting) rather than mixing unrelated holiday elements.
- Taglines dynamically match the occasion (e.g., `GURPURAB • 2026`, `BHAI DOOJ • 2026`, `TECHNOLOGY • 2026`).

### 3. Automatic Safe Space & High-Contrast Typography
- **Facial Protection**: Text is never placed over human faces or primary action points. The layout engine measures lightness and detail across vertical regions to find clean headroom (top) or floor space (bottom).
- **Legibility Guarantee**: Text overlays utilize luminous white lettering (`#FFFFFF`) with multi-layered 3D ambient drop shadows. Even against glowing amber domes, candlelight, or bright daylight, every word remains readable.

### 4. Paced Video Motion Interpolation
- Rather than looping a quick 2-second clip on fast-forward, the video engine distributes character movement smoothly across the 14-second reel.
- The primary action unfolds naturally during the first 7 to 8 seconds, followed by an emotional reaction hold with a gentle camera zoom-in before transitioning to the brand outro card.

### 5. Environmental Framing & Lens Physics Guard
- **No Macro Crops on Actions**: Whenever a prompt describes outdoor environments, water/river rituals (e.g. standing in the Ganges), or held objects (bamboo soop, aarti thali, laptop, product), the engine automatically enforces **Medium Shot framing (waist-up or knee-deep, 35mm-50mm wide lens)**.
- **Full Action Room**: The subject's torso, active arms, hands, held props, and surrounding water or floor surfaces remain fully visible, providing the necessary spatial room for physical motions like circular aarti or typing. Tight macro face zooms that cut off the body or river are strictly banned.

### 6. Zero-Echo Creative Copywriting Engine
- **No Verbatim Copy-Pasting**: The creative director deconstructs human prompts rather than repeating them word-for-word. Prompts containing phrases like "Surya Aarti by the Ganges" or "Create a poster for..." are transformed into original, evocative editorial headlines (e.g. *"Sacred Dawn of Devotion"*, *"Arghya to the Divine Sun"*).

### 7. Visual Layout Calibration & Zero-Crop Boundary Margins
- **Safe Vertical Anchor Ratios**: Bottom-aligned typography is anchored at vertical ratio `0.65` (headline) and `0.77` (quote), guaranteeing the entire block (tagline, headline, decorative bar, and 3-line reflection quote) terminates comfortably before `y = 0.84`. This guarantees a 16%+ clean breathing margin from the bottom edge so text is never truncated, cut off, or covered by mobile platform controls.
- **Headroom Protection**: Top-aligned typography is calibrated to start at `y = 0.10` and wrap by `y = 0.28`, protecting subjects' faces, eyes, and hair from textual overlap.

### 8. Autonomous AI Color Selection & Photometric Contrast
- **Real-Time Pixel Zone Sampling**: The visual layout engine samples actual pixel luminances (`mean_lum`) and RGB values within the selected text crop.
- **Autonomous High-Contrast Assignment**: Automatically resolves typography tones without human interference:
  - Dark/Dusk/River scenes (`mean_lum < 140`): Assigns luminous white (`#FFFFFF`) or radiant warm gold (`#F5C042`) with multi-layered 3D ambient drop shadows.
  - Bright/High-Key daylight scenes (`mean_lum >= 140`): Assigns crisp obsidian slate (`#0F172A`).

### 9. Unified Poster-to-Video Synchronized Editing
- **Dual-Asset Synchronous Revisions**: Modifications to headlines, quotes, colors, or layout positioning requested in the review interface automatically update both the high-resolution poster and the cinema video reel simultaneously.

### 10. Subject-First Prompt Architecture & Waist-Level Prop Holding
- **First-20-Words Rule**: Text-to-image diffusion models (Flux.1 Schnell) prioritize the first 20–30 words. The creative director places the exact subject, gender (*"A serene Indian woman"*), authentic attire (*"traditional festive saree with vermilion sindoor"*), setting (*"standing waist-deep in the sacred river at golden sunrise"*), and specific props (*"flat woven bamboo soop filled with fresh bananas, green coconuts, and burning clay diya lamps"*) at the very beginning of the prompt.
- **Waist-Level Holding Mandate (No Chin Blocks)**: Held trays and objects are anchored at waist or mid-torso height supported from underneath, never at chin or mouth height. This guarantees human faces remain 100% visible and unmasked, allowing video motion diffusion models to animate smooth clockwise circular aarti actions without body deformities.

---

## 5. Complete Codebase Directory & File Guide

Below is the complete file and directory breakdown of the entire project, explaining the exact responsibility of every folder and code file.

```
Digital_Marketing/
├── Backend/                 # Python FastAPI backend server & AI orchestration
│   ├── app/                 # Application source code
│   │   ├── adapters/        # Third-party integrations (AI models, storage, social media)
│   │   ├── api/             # REST API routers, endpoints, and request dependencies
│   │   ├── core/            # Configuration, security, error handling, and prompt rules
│   │   ├── db/              # Database models, connection sessions, and migrations
│   │   ├── domain/          # Pydantic data schemas and validation models
│   │   ├── interfaces/      # Abstract contract classes defining system interfaces
│   │   ├── services/        # Core business logic, video engines, and compositors
│   │   └── workers/         # Background tasks and recurring cron jobs
│   ├── scripts/             # Database maintenance and diagnostic scripts
│   ├── static/              # Publicly served static files
│   ├── storage/             # Generated media assets (posters, video reels, brand logos)
│   └── tests/               # Automated unit and integration test suite
└── Frontend/                # React TypeScript web application
    ├── public/              # Static public web assets, brand logos, and icons
    └── src/                 # React application source code
        ├── api/             # Backend API HTTP client
        ├── assets/          # Static component images
        ├── components/      # Reusable UI components and modal dialogs
        ├── context/         # React global state providers (Authentication)
        ├── types/           # TypeScript interface definitions
        └── views/           # Primary application screens and dashboards
```

---

### 5.1 Backend File & Folder Breakdown

#### Root Files (`Backend/`)
| File | Role & Purpose |
| :--- | :--- |
| `.env` | Environment configuration file containing secret API keys (Cloudflare, Hugging Face, Firecrawl, LinkedIn, PostgreSQL). |
| `.env.example` | Template file showing all required environment variables for quick setup. |
| `app.db` / `marketing.db` | Local SQLite database fallback instances used during offline or local development. |
| `requirements.txt` | Complete list of Python package dependencies (FastAPI, SQLAlchemy, Pillow, ImageIO, AsyncPG, etc.). |
| `upsert_knowledge.py` | Standalone script to populate the local brand and marketing knowledge base. |

---

#### Application Entry & Core Configuration (`Backend/app/`)
| File | Role & Purpose |
| :--- | :--- |
| `app/__init__.py` | Marks the `app` directory as an importable Python package. |
| `app/main.py` | The main FastAPI application entry point. Configures CORS, mounts API routes, manages startup/shutdown events, and serves static storage folders. |

---

#### Core Architecture (`Backend/app/core/`)
| File | Role & Purpose |
| :--- | :--- |
| `core/config.py` | Central settings management using Pydantic Settings. Loads and validates all environment variables, storage paths, and AI model names. |
| `core/errors.py` | Custom application exceptions (e.g., generation failures, safety blocks, authentication errors) for standardized error responses. |
| `core/prompts.py` | **Crucial Prompt Engineering Engine**. Defines director system prompts, visual guidelines, physical gravity rules, complete human anatomy constraints, and negative prompt shields. |
| `core/security.py` | Security utilities for password hashing (bcrypt), JWT access token creation, and user authentication verification. |

---

#### Adapters Layer (`Backend/app/adapters/`)
Implements concrete integrations with external services and third-party APIs.

- **AI Adapters (`adapters/ai/`)**:
  - `cloudflare_image.py`: Calls Cloudflare Workers AI running `@cf/black-forest-labs/flux-1-schnell` to generate photorealistic base images from enhanced briefs.
  - `cloudflare_text.py`: Calls Cloudflare Workers AI running `@cf/meta/llama-3.1-8b-instruct`. Integrates live web research to draft headlines, quotes, captions, and photographic briefs.
  - `video_adapter.py`: Calls Hugging Face Diffusers running `Wan2.1-I2V-14B-720P` or `LTX-Video` to animate static images into high-definition video reels.

- **Publisher Adapters (`adapters/publishers/`)**:
  - `linkedin_adapter.py`: Authenticates via OAuth 2.0 and publishes approved posters, video reels, and formatted captions directly to LinkedIn company or personal profiles.
  - `instagram_adapter.py`: Publisher adapter structure for publishing media and captions to Instagram via Meta Graph API.

- **Safety & Guardrails (`adapters/safety/`)**:
  - `guardrails.py`: Scans incoming user prompts and uploaded images to enforce content safety, brand suitability, and safety compliance before processing.

- **Web Scrapers (`adapters/scrapers/`)**:
  - `firecrawl_adapter.py`: Interfaces with the Firecrawl API to crawl public websites, extract clean markdown content, and search the live web for topic grounding.

- **Storage Adapters (`adapters/storage/`)**:
  - `local_storage.py`: Handles saving, reading, and organizing image files, video reels, and brand logos on the local file system.

---

#### REST API Layer (`Backend/app/api/`)
Defines the HTTP endpoints exposed to the frontend interface.

- `api/dependencies.py`: FastAPI dependency injection helpers for database sessions, current authenticated user verification, and permission checks.
- `api/v1/router.py`: Central routing hub that mounts all sub-endpoints under the `/api/v1` namespace.
- **Endpoints (`api/v1/endpoints/`)**:
  - `admin.py`: Administrative routes to view platform statistics, user lists, and system health metrics.
  - `assistant.py`: Interactive AI marketing assistant chat endpoint for advice, campaign brainstorming, and suggestions.
  - `auth.py`: User registration, login, JWT token issuance, and password management.
  - `custom_creatives.py`: Handles custom user image uploads, safety verification, and overlaying brand typography onto user photos.
  - `linkedin_oauth.py`: Manages the LinkedIn OAuth 2.0 authorization flow (login, token exchange, and profile retrieval).
  - `posters.py`: The core poster generation endpoint (`POST /generate`), poster retrieval, deletion, and PNG re-export.
  - `reviews.py`: Manages the approval workflow (`IN_REVIEW`, `APPROVED`, `REJECTED`) and manual headline/quote edits.
  - `schedules.py`: Manages the campaign calendar and scheduling posts for future publication.
  - `url_campaigns.py`: Accepts a website URL, extracts page content via Firecrawl, and generates a tailored campaign poster.
  - `videos.py`: Generates 14-second animated video reels from posters (`POST /generate_from_poster`), checks rendering status, and serves video streams.

---

#### Database Layer (`Backend/app/db/`)
- `db/base.py`: SQLAlchemy declarative base class for database entity mapping.
- `db/models.py`: Database table definitions:
  - `User`: Accounts, passwords, and roles.
  - `Poster`: Generated posters, clean artwork paths, final composite paths, headlines, quotes, captions, and approval status.
  - `Video`: Animated video reels, frame counts, durations, and file paths.
  - `Schedule`: Scheduled posts, target social platforms, and publication timestamps.
  - `Review`: Editorial comments, review statuses, and approval history.
  - `Brand`: Brand style settings, logo files, and color palettes.
- `db/session.py`: PostgreSQL asynchronous engine and session factory (`async_sessionmaker`).
- `db/repositories/`: Repository pattern helpers for isolated database query operations.

---

#### Domain Schemas (`Backend/app/domain/schemas/`)
Defines Pydantic data models for request validation and response serialization.
- `analytics.py`: Data models for engagement statistics, post reach, and platform metrics.
- `auth.py`: Schemas for user registration, login credentials, and token payloads.
- `brand.py`: Schemas for brand profiles, colors, typography preferences, and logo uploads.
- `knowledge_graph.py`: Schemas for domain knowledge nodes, entities, and relationships.
- `poster.py`: Schemas for poster generation requests, visual plans, and responses.
- `review.py`: Schemas for review status changes and feedback notes.
- `schedule.py`: Schemas for scheduled publication items and calendar event objects.

---

#### Abstract Interfaces (`Backend/app/interfaces/`)
Defines abstract base classes (contracts) that decouple business logic from concrete third-party services:
- `image_generator.py`: Contract for AI image generation providers.
- `text_generator.py`: Contract for AI text and creative direction providers.
- `video_generator.py`: Contract for neural video motion providers.
- `safety_checker.py`: Contract for content moderation and safety evaluation.
- `social_publisher.py`: Contract for social platform posting adapters.
- `storage_provider.py`: Contract for media file storage backends.

---

#### Business Services Layer (`Backend/app/services/`)
Contains the core business logic, visual analysis, and compositing algorithms.

| File | Role & Purpose |
| :--- | :--- |
| `services/visual_knowledge_service.py` | **Live Web Grounding Engine**. Executes live Firecrawl searches before generation to extract authentic product features, cultural facts, and visual aesthetics, preventing hallucinations. |
| `services/visual_director.py` | **Art Director & Safe-Space Analyzer**. Analyzes background images to find empty headroom (top) or floor space (bottom), measures luminance to guarantee contrast, and directs layout composition. |
| `services/poster_compositor.py` | **Graphic Design Compositor**. Uses Pillow to render dynamic occasion taglines, multi-line headlines, elegant quotes, and brand logos with 3D drop shadows onto the base artwork. |
| `services/video_service.py` | **Neural Video Motion Engine**. Animates static images into 14-second video reels using Wan 2.2 / LTX-Video, applying smooth commercial motion pacing and attaching the brand outro card. |
| `services/generation_service.py` | **Main Orchestration Service**. Coordinates the complete workflow: Web search → Creative direction → Image generation → Visual compositing → Database storage. |
| `services/custom_upload_service.py` | Manages the workflow for user-uploaded photographs, applying framing checks and layering brand typography. |
| `services/google_calendar_service.py` | Interacts with Google Calendar API to fetch upcoming holidays and marketing dates. |
| `services/url_crawler_service.py` | Coordinates web scraping of user-provided URLs to extract marketing points. |
| `services/review_service.py` | Handles status transitions, approval tracking, and interactive text edits for marketing assets. |
| `services/scheduling_service.py` | Manages the calendar queue for pending and published social posts. |
| `services/knowledge_graph.py` | Manages brand voice guidelines, industry knowledge, and creative memory. |

---

#### Background Workers (`Backend/app/workers/`)
- `workers/scheduler_worker.py`: Background worker that checks for pending scheduled posts and triggers automatic publishing to social media when their publish time arrives.

---

#### Maintenance Scripts (`Backend/scripts/`)
- `scripts/add_analytics_cols.py`: Database migration script adding analytics columns to existing tables.
- `scripts/check_tables.py`: Diagnostic utility to inspect existing database tables and row counts.
- `scripts/manage_db.py`: Database management utility to create, reset, or inspect database schemas.
- `scripts/setup_guide_table.py`: Initializes reference tables for brand guidelines.
- `scripts/test_dynamic_inpaint.py`: Diagnostic script for testing image editing and inpainting routines.
- `scripts/update_password.py`: Utility to update or reset administrative user passwords.
- `scripts/upsert_to_pinecone.py`: Utility to sync marketing knowledge vectors into Pinecone vector storage.

---

#### Storage Folders (`Backend/storage/`)
- `storage/audio/`: Background audio tracks and sound beds used for video reel compositing.
- `storage/brand/`: Official brand assets (e.g., `42works_logo.png`, `42Works_logo2.png`).
- `storage/posters/`: Stores generated clean backgrounds (`_background.png`) and final styled posters (`_final.png`).
- `storage/videos/`: Stores generated video reels (`_reel.mp4`) and neural raw video clips.

---

#### Test Suite (`Backend/tests/`)
- `tests/conftest.py`: Pytest fixtures, test database setup, and mock configurations.
- `tests/test_auth_and_users.py`: Tests user registration, login, and JWT validation.
- `tests/test_poster_generation.py`: Tests the poster generation pipeline and compositing logic.
- `tests/test_review_workflow.py`: Tests poster review status transitions and comment tracking.
- `tests/test_scheduling_workflow.py`: Tests scheduling queues and post publishing timers.
- `tests/test_knowledge_graph_and_admin.py`: Tests knowledge base queries and administrator endpoints.

---

### 5.2 Frontend File & Folder Breakdown

The Frontend is built with React, TypeScript, Vite, and Tailwind CSS. It provides a visual dashboard for generating, previewing, editing, and publishing marketing materials.

#### Configuration & Build Files (`Frontend/`)
| File | Role & Purpose |
| :--- | :--- |
| `package.json` | Defines frontend dependencies (React, Lucide icons, Tailwind, Axios) and scripts (`dev`, `build`, `lint`). |
| `vite.config.ts` | Vite build configuration, development server settings, and path alias setups. |
| `tsconfig.json` / `tsconfig.app.json` / `tsconfig.node.json` | TypeScript configuration files defining strict type checking rules and compilation targets. |
| `.oxlintrc.json` | Linter configuration for code quality and consistency. |
| `index.html` | Single Page Application HTML root entry point. |

---

#### Public Assets (`Frontend/public/`)
| File | Role & Purpose |
| :--- | :--- |
| `42works_logo.png` / `42Works_logo2.png` | Official company logos displayed across the navigation bar and export cards. |
| `favicon.ico`, `favicon.png`, `favicon.svg` | Browser tab icons and application favicons. |
| `icons.svg` | SVG sprite definitions for UI iconography. |

---

#### Application Core (`Frontend/src/`)
| File | Role & Purpose |
| :--- | :--- |
| `src/main.tsx` | The root entry point of the React application. Mounts the root component into the DOM. |
| `src/App.tsx` | Main application shell. Sets up the top navigation bar, routing views, authentication protection, and footer. |
| `src/index.css` / `src/App.css` | Global styling, Tailwind CSS utility imports, color themes, and custom animations. |

---

#### API Client (`Frontend/src/api/`)
| File | Role & Purpose |
| :--- | :--- |
| `src/api/client.ts` | Centralized Axios HTTP client. Automatically attaches JWT tokens to requests, handles backend error responses, and defines typed API calling methods. |

---

#### Shared UI Components (`Frontend/src/components/`)
| File | Role & Purpose |
| :--- | :--- |
| `Navbar.tsx` | Top navigation bar featuring brand branding, active page links, user profile badge, and sign-out actions. |
| `Footer.tsx` | Application footer with version info, status indicators, and company links. |
| `AppreciativePoster.tsx` | Interactive poster card component displaying generated artwork, headlines, action buttons, and review status badges. |
| `ReviewModal.tsx` | Modal dialog allowing marketing managers to inspect artwork, edit headlines and quotes, and approve or reject assets. |
| `ChangePasswordModal.tsx` | Modal dialog allowing users to securely update their account credentials. |
| `RadialCursor.tsx` | Interactive decorative UI element providing modern visual polish on hover. |
| `SocialIcons.tsx` | Vector brand icon components for LinkedIn, Instagram, Facebook, and X. |
| `SparkyMascot.tsx` | Animated mascot avatar providing interactive hints, loading states, and creative encouragement. |

---

#### Global State (`Frontend/src/context/`)
| File | Role & Purpose |
| :--- | :--- |
| `src/context/AuthContext.tsx` | Global authentication state manager. Keeps track of current logged-in user, JWT tokens, login/logout functions, and route protection. |

---

#### TypeScript Data Types (`Frontend/src/types/`)
| File | Role & Purpose |
| :--- | :--- |
| `src/types/index.ts` | Centralized TypeScript interface definitions matching backend schemas (`Poster`, `Video`, `User`, `Schedule`, `ReviewStatus`, etc.). |

---

#### Primary Screens & Views (`Frontend/src/views/`)
| File | Role & Purpose |
| :--- | :--- |
| `StudioPage.tsx` | **The Core Creative Studio**. Allows users to create posters from prompts, website URLs, or custom uploaded photos. Features live generation status, preview canvas, and 14-second video reel generation. |
| `LibraryPage.tsx` | **Creative Asset Gallery**. Displays all historical posters and video reels with search, category filtering, high-res download, and delete options. |
| `SchedulesPage.tsx` | **Social Publishing Calendar**. Visual planner showing scheduled posts, publication dates, and social platform destinations. |
| `AdminPage.tsx` | **Platform Administration Dashboard**. View system users, generation analytics, and backend health status. |
| `LoginPage.tsx` | **Authentication Screen**. Secure sign-in portal for marketing team members. |

---

## 6. Environment Variables & Third-Party Service Keys

The backend relies on the following external services configured in `Backend/.env`:

| Variable Name | Service Provider | Purpose |
| :--- | :--- | :--- |
| `CLOUDFLARE_API_TOKEN` | Cloudflare Workers AI | Powers LLaMA 3.1 8B (text/creative direction) and Flux.1 Schnell (image generation). |
| `CLOUDFLARE_ACCOUNT_ID` | Cloudflare Workers AI | Identifies your Cloudflare account endpoint. |
| `HUGGINGFACE_API_TOKEN` | Hugging Face | Powers Wan 2.2 / LTX-Video neural video motion models. |
| `FIRECRAWL_API_KEY` | Firecrawl API | Powers real-time live web searches and web page scraping. |
| `DATABASE_URL` | PostgreSQL | Connection string for database persistence (`postgresql+asyncpg://...`). |
| `JWT_SECRET` | Internal Security | Cryptographic secret for signing user session tokens. |
| `LINKEDIN_CLIENT_ID` | LinkedIn Developer Portal | OAuth 2.0 app client ID for LinkedIn posting. |
| `LINKEDIN_CLIENT_SECRET` | LinkedIn Developer Portal | OAuth 2.0 app client secret for LinkedIn posting. |

---

## 7. Developer Onboarding: Running & Testing the Project

### Prerequisites
- Python 3.11 or 3.12
- Node.js (v18 or higher) and npm
- PostgreSQL database instance
- FFmpeg installed and available on system PATH

### 1. Starting the Backend
```bash
cd "Backend"

# Activate the virtual environment
.venv\Scripts\activate   # Windows
source .venv/bin/activate # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Run database migrations / setup tables
python scripts/manage_db.py

# Start the FastAPI server with auto-reload
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
The backend API documentation is interactively accessible at `http://127.0.0.1:8000/docs`.

### 2. Starting the Frontend
```bash
cd "Frontend"

# Install packages
npm install

# Start local development server
npm run dev
```
The frontend interface opens at `http://localhost:5173/`.

### 3. Running Automated Tests
```bash
cd "Backend"
pytest tests/ -v
```

---

## 8. Summary of Recent Improvements

1. **Live Search Integration (`visual_knowledge_service.py`)**: The system queries the live web prior to generation, eliminating outdated or hallucinated details.
2. **Physical Gravity Safeguards (`prompts.py`)**: Human figures must have complete bodies, and all objects must be physically supported, eliminating floating plates, dishes, or disembodied limbs.
3. **Paced Video Interpolation (`video_service.py`)**: Video reels are rendered as 14-second continuous cinematic animations with purposeful character actions rather than fast-forward loops.
4. **Adaptive Text Contrast (`visual_director.py` & `poster_compositor.py`)**: Layout engine ensures luminous white typography with 3D drop shadows on headroom or floor areas, guaranteeing clear readability across all scenes.
5. **Streaming Ultrafast FFmpeg Video Re-Composition Engine (`video_service.py`)**: Precomputes glow templates and typography overlays once outside the frame loop, streaming raw RGB24 frames directly to FFmpeg via `stdin` using `-preset ultrafast` for sub-6-second instant text updates.
6. **Wan 2.2 / Wan 2.1 Motion Architecture (`video_adapter.py`)**: High-fidelity character action guidance (e.g. clockwise circular aarti motion, devotional smiles, water ripples) and automatic fallback hierarchy.
7. **Interactive Video Typography Transformer (`ReviewModal.tsx`)**: Live preview bounding box and approval toolbar for dragging, scaling, and rotating text directly over the video canvas with exact coordinate preservation.
