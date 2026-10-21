"""Generate real measured, deterministic local baseline evaluation."""
from datetime import datetime, timezone
from pathlib import Path
from backend.app.main import race_data, RaceRequest

rows=[]
for depth in (3,4,5):
    data=race_data(RaceRequest(depth=depth,seed=42))
    for result in data['results']:
        rows.append((depth,result['name'],'Yes' if result['solved'] else 'No',len(result['moves']),str(result['optimality_gap']) if result['optimality_gap'] is not None else 'N/A',f"{result['elapsed_ms']:.2f}"))
lines=['# Local benchmark evaluation','',f'Generated UTC: {datetime.now(timezone.utc).isoformat(timespec="seconds")}','','**Execution mode: Offline simulation. Not live LLM inference.**','', 'Seed: `42`; depth settings: `3`, `4`, `5`.','','| Scramble depth | Baseline | Solved | Moves | Optimality gap | Measured search time (ms) |','|---:|---|:---:|---:|---:|---:|']
for row in rows:lines.append('| '+' | '.join(map(str,row))+' |')
lines+=['','**Interpretation:** Inverse-scramble is privileged with direct access to scramble history; it is a correctness control. BFS uses the facelet state and a search budget. The inverse control is not a blind AI competitor. BFS times are local measurements that depend on hardware and may vary.','', '**Limitations:** Limited depths and seeds; no multi-seed statistics; no 3D rendering; no external model calls.']
Path('docs').mkdir(exist_ok=True)
Path('docs/evaluation.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('\n'.join(lines))
