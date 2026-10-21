# CubeLab — Rubik's Cube Spatial Reasoning Benchmark

**AI Engineering — Assignment 02**  
**Adaptation maintainer:** Zaid Bin Naveed  
**Stack:** Python · FastAPI · Vanilla JavaScript · CSS  
**Mode:** Offline deterministic evaluation (no live LLM integrations)

> **Provenance and scope.** This is an **independently implemented, local-first baseline and UI package**.

## Project overview

CubeLab studies search and action planning in the 3×3 Rubik's Cube state space. It visualizes a scrambled state, solves short scrambles using a bounded bidirectional breadth-first search baseline, and compares the solver against an inverse-scramble control. Every result is generated locally and reproducibly from the selected seed.

### Implemented features

- Responsive dark-theme dashboard with Rubik's Cube **2D unfolded facelet visualization**, scramble difficulty controls, seed selection, metric cards, and comparison table.
- Genuine 54-facelet cube state representation, six faces, and all 18 face-turn notations (`U`, `U'`, `U2`, etc.).
- Seeded random scrambling with consecutive same-face moves excluded.
- Bidirectional BFS with a maximum search depth of 6 in the app; returns an explicit bounded failure when it cannot find a solution.
- Deterministic inverse-scramble and bounded BFS comparison with success and optimality-gap metrics.
- FastAPI endpoints for health, scrambling, solving, model/control metadata, synchronous race execution, and SSE event-stream execution.
- Explicit guardrail rejecting requests for unavailable live model mode.
- Automated tests and a small reproducible evaluation report.

**Important limitation:** These are *algorithmic baselines*, not frontier LLMs. The browser displays an **unfolded cube net**, not a 3D animated cube. No claims are made about external model intelligence or live model latency.

## Quick start — Windows

1. Install Python 3.10+.
2. Extract the project ZIP.
3. Double-click **`START_WINDOWS.bat`**. It will create `.venv`, install dependencies, and launch the local server.
4. Open **http://127.0.0.1:8000** in your browser.

If the browser doesn't open automatically, use the URL manually. The URL is local to the computer running the server; it is **not** a hosted public site.

### Manual start

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

On macOS/Linux, activate with `source .venv/bin/activate`, then run the same pip and uvicorn commands.

### Project links

- Application: http://127.0.0.1:8000
- Swagger API documentation: http://127.0.0.1:8000/docs
- Health check: http://127.0.0.1:8000/api/health

## Reproducible evaluation

Run unit and API tests:

```bash
python -m pytest backend/tests -v
```

Generate the benchmark report from actual local runs:

```bash
python evaluate.py
```

The evaluation uses fixed seed 42 at depths 3, 4, and 5. **Optimality gap** is defined as the number of moves in a successful candidate solution minus the bounded BFS solution length. It is only reported when both a candidate solution and a BFS solution exist.

**Methodological caveat:** Inverse-scramble is given the generated scramble sequence and therefore is not a fair blind solver. It is useful for correctness and comparison, *not* for demonstrating AI reasoning.

## Architecture

```text
AI-Engineering-Assignment-02/
├── backend/
│   ├── app/
│   │   ├── cube_engine.py       # Stickers, turns, scrambling, bounded BFS
│   │   └── main.py              # FastAPI and SSE endpoints
│   └── tests/
│       └── test_engine.py       # Unit and API tests
├── frontend/
│   ├── index.html               # Responsive web dashboard
│   └── static/
│       ├── styles.css
│       └── app.js
├── docs/
│   └── evaluation.md            # Generated local evaluation
├── evaluate.py
├── START_WINDOWS.bat
├── requirements.txt
├── .env.example
└── README.md
```

### API

| Endpoint | Purpose |
| --- | --- |
| `GET /` | Serves web application |
| `GET /api/health` | Service health and declared simulation mode |
| `GET /api/models` | Two deterministic control/baseline descriptions |
| `POST /api/scramble` | Generate seeded scramble |
| `POST /api/solve` | Attempt bounded BFS solution |
| `POST /api/race/run` | Compare local controls |
| `POST /api/race/stream` | Stream results via SSE |

## Security and reproducibility

- No external API credentials are required or collected.
- Browser output is generated with safe DOM text assignment; generated benchmark data isn't injected as HTML.
- Input difficulty and seed are validated server-side.
- Local server binds to `127.0.0.1` by default, not a public network interface.
- No external AI API traffic or model billing occurs.
- Google Fonts are optionally loaded for typography; without internet, the interface falls back to system fonts.

## Verification status

The project test suite, endpoint smoke tests, and the evaluation script were executed in the provided environment. Actual report and result counts are in `docs/evaluation.md`. **Visual cross-browser testing and production deployment have not been performed.**

## Credits

- **Zaid Bin Naveed:** designated maintainer of this adaptation package; independently authored student contributions should be documented before representing them as his work.
- **Independent implementation in this package:** self-contained cube engine, offline evaluation API, tests, and dashboard produced for this adaptation.

**License:** No license is asserted for the upstream repository. This package does not include a copy of its source code or its demo video. Review course requirements and any source permissions before reuse.
