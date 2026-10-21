# Local benchmark evaluation

Generated UTC: 2026-10-21T15:45:27+00:00

**Execution mode: Offline simulation. Not live LLM inference.**

Seed: `42`; depth settings: `3`, `4`, `5`.

| Scramble depth | Baseline | Solved | Moves | Optimality gap | Measured search time (ms) |
|---:|---|:---:|---:|---:|---:|
| 3 | Inverse scramble | Yes | 3 | 0 | 0.00 |
| 3 | Bidirectional BFS | Yes | 3 | 0 | 2.77 |
| 4 | Inverse scramble | Yes | 4 | 0 | 0.00 |
| 4 | Bidirectional BFS | Yes | 4 | 0 | 5.31 |
| 5 | Inverse scramble | Yes | 5 | 0 | 0.00 |
| 5 | Bidirectional BFS | Yes | 5 | 0 | 41.30 |

**Interpretation:** Inverse-scramble is privileged with direct access to scramble history; it is a correctness control. BFS uses the facelet state and a search budget. The inverse control is not a blind AI competitor. BFS times are local measurements that depend on hardware and may vary.

**Limitations:** Limited depths and seeds; no multi-seed statistics; no 3D rendering; no external model calls.
