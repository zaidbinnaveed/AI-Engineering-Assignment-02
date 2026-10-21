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

def test_live_rejected():
    c=TestClient(app)
    assert c.post('/api/race/run',json={'mode':'live'}).status_code==400
