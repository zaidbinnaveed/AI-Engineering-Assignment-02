import pytest
from fastapi.testclient import TestClient
from backend.app.cube_engine import SOLVED,MOVES,move,apply,inverse,scramble,solve
from backend.app.main import app

@pytest.mark.parametrize('m',MOVES)
def test_inverse(m):assert move(move(SOLVED,m),inverse(m))==SOLVED
@pytest.mark.parametrize('face','URFDLB')
def test_four_turns(face):assert apply(SOLVED,[face]*4)==SOLVED
@pytest.mark.parametrize('depth',range(1,5))
def test_solver(depth):
    state,_=scramble(depth,seed=100+depth)
    solution=solve(state,max_depth=depth)
    assert solution is not None and apply(state,solution)==SOLVED

def test_deterministic_scramble():assert scramble(5,17)==scramble(5,17)
def test_invalid_move():
    with pytest.raises(ValueError):move(SOLVED,'X')

def test_api():
    client=TestClient(app)
    assert client.get('/api/health').json()['status']=='ok'
    r=client.post('/api/race/run',json={'depth':3,'seed':12})
    assert r.status_code==200
    assert r.json()['mode']=='simulation'
    assert all(x['solved'] for x in r.json()['results'])

def test_live_inference_and_stream(monkeypatch):
    from backend.app import main
    async def fake_model(state, sequence, seed, baseline_depth):
        moves = [inverse(m) for m in reversed(sequence)]
        return {'id':'gpt-oss','kind':'live_llm','name':'GPT-OSS 20B','solved':apply(state,moves)==SOLVED,
                'moves':moves,'status':'solved','raw_response':'model output','elapsed_ms':12}
    monkeypatch.setattr(main, 'run_model', fake_model)
    client = TestClient(app)
    response = client.post('/api/race/run', json={'mode':'live','depth':3,'seed':42})
    assert response.status_code == 200
    assert response.json()['results'][0]['kind'] == 'live_llm'
    assert response.json()['results'][0]['solved']
    streamed = client.post('/api/race/stream', json={'mode':'live','depth':1,'seed':42})
    assert 'event: start' in streamed.text and 'event: complete' in streamed.text
    assert 'model output' in streamed.text

def test_input_limits():
    client = TestClient(app)
    for payload in ({'mode':'unknown'}, {'depth':0}, {'seed':-1}, {'seed':1000000}):
        assert client.post('/api/race/run', json=payload).status_code == 422
    assert client.post('/api/solve', json={'state':SOLVED,'max_depth':8}).status_code == 422

def test_unseeded_stream_is_one_puzzle():
    import json
    response = TestClient(app).post('/api/race/stream', json={'depth':2,'mode':'simulation'})
    frames = [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith('data: ')]
    assert frames[0]['initial_state'] == frames[-1]['initial_state']
    assert frames[0]['scramble'] == frames[-1]['scramble']
