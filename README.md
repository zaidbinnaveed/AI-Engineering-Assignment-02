# AI Engineering Assignment 2
## Rubik's Cube AI Model Benchmark

**Maintainer:** Zaid Bin Naveed  
**Course:** AI Engineering — Assignment 2  
**Technology:** Python, FastAPI, JavaScript, HTML5, CSS3  
**Project Status:** Adaptation and independent evaluation

### Overview

An interactive AI benchmarking platform for evaluating model-driven decision-making using the Rubik's Cube as a spatial reasoning environment.

The platform compares different AI models on shared cube configurations, tracks their decisions, and evaluates solution efficiency against a deterministic search-based baseline.

### Key Features

- Interactive 3D-style Rubik's Cube visualization
- AI model comparison and race execution
- Deterministic cube-state simulation
- Bidirectional breadth-first search baseline
- Real-time execution updates through Server-Sent Events
- Performance monitoring and benchmark aggregation
- Offline simulation and configurable live API access
- REST APIs implemented with FastAPI
- Automated backend testing

### System Architecture

| Component | Responsibility |
|---|---|
| Cube Engine | Cube states, legal moves, scramble generation |
| Search Solver | Shortest-path search within supported limits |
| Model Adapter | Model requests, response parsing, API configuration |
| Benchmark Runner | Concurrent execution and metrics |
| FastAPI Backend | REST endpoints and real-time event streaming |
| Web Frontend | Interactive arena, controls, telemetry and results |

### Project Structure

```text
AI-Engineering-Assignment-02/
├── backend/
│   ├── app/
│   │   ├── cube_engine.py
│   │   ├── openrouter_client.py
│   │   ├── benchmark_runner.py
│   │   └── main.py
│   ├── data/
│   └── tests/
├── frontend/
│   ├── index.html
│   └── static/
│       ├── css/
│       └── js/
├── docs/
├── requirements.txt
├── .env.example
└── README.md
```

### Installation

Requires Python 3.10 or newer.

**1. Clone the repository**

```bash
git clone https://github.com/zaidbinnaveed/AI-Engineering-Assignment-02.git
cd AI-Engineering-Assignment-02
```

**2. Create a virtual environment**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

**4. Configure environment variables**

```powershell
Copy-Item .env.example .env
```

Offline simulation should be used by default. Configure an API key only when explicitly enabling real model calls.

**5. Run the backend**

```bash
python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

**6. Open the application**

http://127.0.0.1:8000

Interactive API documentation:

http://127.0.0.1:8000/docs

### Testing

Run the backend test suite:

```bash
python -m pytest backend/tests -v
```

Additional verification:

```bash
python run_verification.py
```

Passing test counts and benchmark results should be added after execution and independent verification.

### Evaluation Methodology

Performance can be evaluated using:

| Metric | Description |
|---|---|
| Success Rate | Percentage of puzzles solved |
| Solution Length | Total moves used |
| Optimality Gap | Difference from baseline shortest-path length |
| Execution Time | Time required for an attempted solution |
| Model Latency | Response time per model invocation |
| Invalid Responses | Unparseable or illegal model actions |

Simulation results must be clearly distinguished from results obtained through real model API calls. Historical source data must not be represented as newly collected experimental evidence.

### Security and Reliability

- Keep API credentials outside source control.
- Configure request budgets and timeouts.
- Validate model-generated actions before execution.
- Avoid exposing credentials through frontend JavaScript.
- Record execution mode and model configuration for reproducibility.

### Contributions

**Zaid Bin Naveed** — Adaptation maintainer.

Document independently implemented features, testing, UI improvements, and newly collected evaluation results here once verified.

### License

Review the source project's licensing and obtain any necessary permissions before redistribution. Preserve applicable notices.

---

**AI Engineering — Assignment 2**  
Zaid Bin Naveed
