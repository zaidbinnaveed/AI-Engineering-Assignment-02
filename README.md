# CubeLab — Live Cube Reasoning Arena

AI Engineering · Assignment 02 · Zaid Bin Naveed

A small FastAPI + vanilla JavaScript assignment that scrambles a Rubik's cube, calls a **real free hosted LLM**, and checks its answer against the cube engine. Includes a responsive dashboard, streamed progress, an interactive 3D Rubik cube with animated face-layer turns, JSON export, and two local reference algorithms.

## Run locally

**Open: http://127.0.0.1:8000** (or http://localhost:8000).

On Windows, double-click `START_WINDOWS.bat`. It creates `.venv`, installs the small Python dependency set, and starts the server. Keep its terminal open; press Ctrl+C to stop. If already running, open the URL directly.

Manual setup (Python 3.10+):

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

On macOS/Linux, replace `.venv\Scripts\python.exe` with `.venv/bin/python`.

- Dashboard: http://localhost:8000
- Interactive API: http://localhost:8000/docs
- Server health: http://localhost:8000/api/health

This URL runs on your computer. It is not a public deployment. No Node build, database, GPU, or API key is needed. Internet is required for the live LLM; local controls work without it.

## Try a live simulation

1. Choose Warmup, Standard, or Challenge (3, 4, or 5 scramble moves).
2. Set a seed, or leave it at `42`.
3. Keep **Live LLM + controls** selected and click **Run benchmark**.
4. Local reference results arrive first; the model row shows its actual waiting time.
5. Watch the 3D cube solve automatically when the model answer arrives. Drag the cube to rotate your view; use Pause/Resume, animation speed, Reset, and Reset view to inspect the solve. Click **Replay solution** to play it again. **Export JSON** saves the complete experiment, including the raw model answer and states.

The app uses the anonymous [Pollinations text API](https://text.pollinations.ai/models), model `openai-fast`, currently described by its live catalog as **GPT-OSS 20B**. It makes an actual server-side POST to `https://text.pollinations.ai/`; it does not use OpenAI's paid API. No credentials or billing setup are configured.

The free service can change, cache responses, rate limit requests, or become unavailable. Requests time out after 75 seconds. Upstream errors and invalid outputs appear as failures; the app never substitutes a deterministic solution for an LLM response. Only one live inference runs at a time. Do not submit private data: the generated scramble and facelets are sent to Pollinations.

## What is being measured

| Approach | Input | Execution |
| --- | --- | --- |
| GPT-OSS 20B | Scramble history + current facelets | Live hosted model request |
| Inverse scramble | Scramble history | Deterministic correctness control |
| Bidirectional BFS | Current facelets | Local bounded search |

This is a **history-assisted planning task**, not a blind cube-solving intelligence benchmark. The prompt explains inverse turns but does not include a precomputed solution. The LLM produces its own move list. All returned moves must use the 18 standard Singmaster turns; the backend applies them and compares all 54 facelets with the solved cube.

BFS is limited to 6 moves and 120,000 explored nodes. A missing reference is a budget limit, not a proof of impossibility. Gap is solution length minus the reference length and is reported only for solved candidates with a reference. Times are measured locally: live latency includes the complete HTTP round trip and possible provider caching. This is a single-puzzle demonstration, not a statistical model ranking. The visualization uses 26 individual 3D cubies and 54 colored stickers, with true face-layer rotations. All 18 turn directions match the backend geometry. A live answer begins playback as soon as its SSE result arrives; the cube waits for the model before moving. Animations use native CSS 3D and the Web Animations API, with no extra library or CDN. Reduced-motion preferences shorten each turn.

## Backend and API

| Endpoint | Purpose |
| --- | --- |
| `GET /api/health` | Local server health and enabled provider; does not probe upstream availability |
| `GET /api/models` | Live model and local reference metadata |
| `POST /api/scramble` | Seeded puzzle, with `depth` and `seed` |
| `POST /api/solve` | Bounded search from a 54-character facelet state |
| `POST /api/race/run` | Full result JSON; `mode` is `live` or `simulation` |
| `POST /api/race/stream` | SSE `start`, `result`, `progress`, `complete`, and explicit error events |

Race request example:

```json
{"depth":3,"seed":42,"mode":"live"}
```

The UI explicitly selects live mode. For compatibility with the offline evaluation script, API requests that omit `mode` default to `simulation` (local controls only).

Inputs are validated, bounded search runs off the async event loop, network calls have timeouts, and generated content is displayed using safe DOM text assignment. The server binds to loopback by default. The frontend uses system fonts and needs no external assets.

## Verification

```powershell
python -m pytest backend/tests -q
python evaluate.py
```

The suite covers cube move inverses, solver correctness, seeded generation, API validation, live request/stream integration, model response parsing, engine verification, malformed output, and upstream HTTP failures. Provider boundary tests use controlled responses; a separate real-network smoke run is recorded in [docs/live-smoke.json](docs/live-smoke.json).

Verified on 2026-10-21: **44 tests passed**. Real live smoke run, seed 42, depth 3: scramble `R U L2`; GPT-OSS returned `L2 U' R'`; engine verification passed; gap 0; measured request time about 13.1 seconds. This is one observed result, not a guarantee of future availability or accuracy.

The headless browser check also passed: all 18 3D rotations match independently generated Python move fixtures; live SSE results trigger automatic solving; each rotating layer contains 9 cubies; pause freezes the current turn and resume reaches solved; keyboard orbit and view reset work; both favicon routes load; and the 390px mobile layout has no page overflow or browser runtime exceptions. See [browser verification](docs/browser-verification.json), [desktop screenshot](docs/live-result-desktop.png), [paused 3D turn](docs/3d-turn-paused.png), and [mobile screenshot](docs/dashboard-mobile.png).

`evaluate.py` writes [docs/evaluation.md](docs/evaluation.md) for **offline references only**. It intentionally does not consume free model requests.

## Files

```text
backend/app/cube_engine.py    Cube state, turns, scrambling, bounded BFS
backend/app/live_models.py    Hosted inference, parsing, verification
backend/app/main.py           FastAPI, static files, SSE
backend/tests/                Engine, API, provider boundary tests
frontend/index.html          Dashboard
frontend/static/app.js       Streaming, automatic solving, playback, export
frontend/static/cube3d.js    3D cubies, layer rotations, camera controls
frontend/static/favicon.svg Cube favicon
frontend/static/styles.css   Responsive interface
START_WINDOWS.bat            Windows launcher
```

## Attribution

This independently implemented adaptation is informed by Muhammad Abbas's [AI-Engineering-Assignment2](https://github.com/muhammad1234-max/AI-Engineering-Assignment2) project concept. It is not a clone of the original code; the original author's work and reported evaluations are not represented as Zaid's. Zaid Bin Naveed is the designated adaptation maintainer. The package contains its own cube engine, dashboard, local controls, and live integration. No license is asserted for the upstream project; follow your course's attribution and collaboration requirements.
