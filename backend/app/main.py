"""Local-first benchmark API. Simulation is explicitly labelled; no fabricated model responses."""
import asyncio
import json
import os
import time
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from .cube_engine import SOLVED, MOVES, apply, scramble, solve

ROOT=Path(__file__).resolve().parents[2]
app=FastAPI(title='CubeLab | AI Engineering Assignment 2',version='1.0.0')
app.mount('/static',StaticFiles(directory=str(ROOT/'frontend/static')),name='static')

class ScrambleRequest(BaseModel):
    depth:int=Field(default=4,ge=1,le=20)
    seed:int|None=None
class SolveRequest(BaseModel):
    state:str
    max_depth:int=Field(default=6,ge=0,le=8)
class RaceRequest(BaseModel):
    depth:int=Field(default=4,ge=1,le=20)
    seed:int|None=None
    mode:str='simulation'

@app.get('/')
def home():return FileResponse(ROOT/'frontend/index.html')
@app.get('/api/health')
def health():return {'status':'ok','mode':'simulation','live_models_enabled':False,'engine':'3x3 facelets'}
@app.get('/api/models')
def models():return {'mode':'simulation','models':[{'id':'inverse','name':'Inverse scramble','kind':'deterministic baseline'}, {'id':'bfs','name':'Bidirectional BFS','kind':'exact bounded search'}]}
@app.post('/api/scramble')
def new_scramble(req:ScrambleRequest):
    state,seq=scramble(req.depth,req.seed)
    return {'state':state,'scramble':seq,'solved':SOLVED}
@app.post('/api/solve')
def solve_state(req:SolveRequest):
    if len(req.state)!=54 or any(req.state.count(f)!=9 for f in 'URFDLB'):
        raise HTTPException(422,'Invalid state')
    t=time.perf_counter();result=solve(req.state,req.max_depth)
    return {'found':result is not None,'moves':result,'elapsed_ms':round((time.perf_counter()-t)*1000,2),'bounded_depth':req.max_depth}

def race_data(req):
    if req.mode!='simulation':raise HTTPException(400,'Only local simulation is implemented. Live model calls are not available.')
    state,seq=scramble(req.depth,req.seed)
    t=time.perf_counter();path=solve(state,min(req.depth+2,6));baseline_ms=round((time.perf_counter()-t)*1000,2)
    inverse_path=[m if m.endswith('2') else m[:1] if m.endswith("'") else m+"'" for m in reversed(seq)]
    # Actual deterministic policies; not LLM outputs.
    candidates=[('inverse','Inverse scramble',inverse_path,0.0),('bfs','Bidirectional BFS',path,baseline_ms)]
    results=[]
    for id,name,moves,elapsed in candidates:
        final=apply(state,moves) if moves is not None else None
        results.append({'id':id,'name':name,'moves':moves or [],'solved':final==SOLVED,'elapsed_ms':elapsed,'optimality_gap':len(moves)-len(path) if moves is not None and path is not None and final==SOLVED else None,'kind':'baseline','status':'completed' if moves is not None else 'depth_limit'})
    return {'mode':'simulation','scramble':seq,'initial_state':state,'baseline_depth':len(path) if path is not None else None,'results':results,'disclaimer':'Deterministic baselines only. These are not real AI model API results.'}
@app.post('/api/race/run')
def run(req:RaceRequest):return race_data(req)
@app.post('/api/race/stream')
async def stream(req:RaceRequest):
    data=race_data(req)
    async def iterator():
        yield 'event: start\ndata: '+json.dumps({'mode':'simulation','initial_state':data['initial_state'],'scramble':data['scramble']})+'\n\n'
        for item in data['results']:
            yield 'event: result\ndata: '+json.dumps(item)+'\n\n'
            await asyncio.sleep(0)
        yield 'event: complete\ndata: '+json.dumps(data)+'\n\n'
    return StreamingResponse(iterator(),media_type='text/event-stream')
