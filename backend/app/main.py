"""Small local benchmark API with real, verified hosted model inference."""
import asyncio
import json
import time
from pathlib import Path
from typing import Literal
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from .cube_engine import SOLVED, apply, scramble, solve, inverse
from .live_models import run_model, MODEL, MODEL_NAME

ROOT = Path(__file__).resolve().parents[2]
app = FastAPI(title='CubeLab | AI Engineering Assignment 2', version='2.0.0')
app.mount('/static', StaticFiles(directory=str(ROOT/'frontend/static')), name='static')
# One inference request at a time keeps anonymous usage modest.
live_lock = asyncio.Lock()

class ScrambleRequest(BaseModel):
    depth: int = Field(default=3, ge=1, le=20)
    seed: int | None = Field(default=None, ge=0, le=999999)

class SolveRequest(BaseModel):
    state: str = Field(min_length=54, max_length=54)
    max_depth: int = Field(default=6, ge=0, le=6)

class RaceRequest(ScrambleRequest):
    mode: Literal['live', 'simulation'] = 'simulation'

@app.get('/')
def home():
    return FileResponse(ROOT/'frontend/index.html')

@app.get('/api/health')
def health():
    return {'status':'ok', 'mode':'live', 'live_models_enabled':True,
            'provider':'Pollinations', 'model': MODEL, 'engine':'3x3 facelets',
            'note':'Server health does not guarantee upstream model availability.'}

@app.get('/api/models')
def models():
    return {'mode':'live', 'models':[
        {'id':'gpt-oss','name':MODEL_NAME,'model':MODEL,'provider':'Pollinations','kind':'live_llm'},
        {'id':'inverse','name':'Inverse scramble','kind':'deterministic control'},
        {'id':'bfs','name':'Bidirectional BFS','kind':'bounded search'}]}

@app.post('/api/scramble')
def new_scramble(req: ScrambleRequest):
    state, sequence = scramble(req.depth, req.seed)
    return {'state':state,'scramble':sequence,'solved':SOLVED}

@app.post('/api/solve')
def solve_state(req: SolveRequest):
    if any(req.state.count(face) != 9 for face in 'URFDLB') or any(req.state[i*9+4] != face for i,face in enumerate('URFDLB')):
        raise HTTPException(422, 'Invalid facelets or face centers')
    started = time.perf_counter()
    result = solve(req.state, req.max_depth)
    return {'found':result is not None,'moves':result,
            'elapsed_ms':round((time.perf_counter()-started)*1000,2),'bounded_depth':req.max_depth}

def race_data(req, initial=None):
    """Local reference results; used by the reproducible offline evaluation too."""
    state, sequence = initial if initial is not None else scramble(req.depth, req.seed)
    started = time.perf_counter()
    path = solve(state, min(req.depth, 6))
    baseline_ms = round((time.perf_counter()-started)*1000,2)
    started = time.perf_counter()
    inverse_path = [inverse(turn) for turn in reversed(sequence)]
    inverse_ms = round((time.perf_counter()-started)*1000, 2)
    results = []
    for id, name, moves, elapsed in [('inverse','Inverse scramble',inverse_path,inverse_ms),('bfs','Bidirectional BFS',path,baseline_ms)]:
        states = [state]
        for turn in moves or []:
            states.append(apply(states[-1], [turn]))
        solved = moves is not None and states[-1] == SOLVED
        results.append({'id':id,'name':name,'moves':moves or [],'states':states,
                        'solved':solved,'elapsed_ms':elapsed,
                        'optimality_gap':len(moves)-len(path) if solved and path is not None else None,
                        'kind':'baseline','status':'solved' if solved else 'budget_limit'})
    return {'mode':req.mode,'seed':req.seed,'scramble':sequence,'initial_state':state,
            'baseline_depth':len(path) if path is not None else None,'results':results,
            'disclaimer':'History-assisted task: LLM and inverse control see the scramble. BFS uses facelets. This is not a blind spatial reasoning test.'}

async def inference(data, req):
    if live_lock.locked():
        raise HTTPException(429, 'A live benchmark is already running. Please wait for it to finish.')
    async with live_lock:
        return await run_model(data['initial_state'], data['scramble'], req.seed, data['baseline_depth'])

@app.post('/api/race/run')
async def run(req: RaceRequest):
    data = await asyncio.to_thread(race_data, req)
    if req.mode == 'live':
        data['results'].insert(0, await inference(data, req))
    return data

@app.post('/api/race/stream')
async def stream(req: RaceRequest):
    if req.mode == 'live' and live_lock.locked():
        raise HTTPException(429, 'A live benchmark is already running. Please wait.')
    async def iterator():
        state, sequence = scramble(req.depth, req.seed)
        yield event('start', {'mode':req.mode,'initial_state':state,'scramble':sequence})
        data = await asyncio.to_thread(race_data, req, (state, sequence))
        for result in data['results']:
            yield event('result', result)
        if req.mode == 'live':
            yield event('progress', {'message':'Waiting for GPT-OSS 20B via Pollinations...'})
            task = asyncio.create_task(inference(data, req))
            try:
                while not task.done():
                    done, _ = await asyncio.wait({task}, timeout=5)
                    if not done:
                        yield ': heartbeat\n\n'
                result = await task
                data['results'].insert(0, result)
                yield event('result', result)
            except HTTPException as exc:
                yield event('error', {'message':exc.detail})
            finally:
                if not task.done():
                    task.cancel()
        yield event('complete', data)
    return StreamingResponse(iterator(), media_type='text/event-stream',
                             headers={'Cache-Control':'no-cache','X-Accel-Buffering':'no'})

def event(name, data):
    return f'event: {name}\ndata: {json.dumps(data)}\n\n'
