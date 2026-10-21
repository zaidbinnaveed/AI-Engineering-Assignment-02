"""Provider boundary tests: parse, verify, and expose failures without fake answers."""
import asyncio
import json
import httpx
import pytest
from backend.app import live_models
from backend.app.cube_engine import scramble, SOLVED

@pytest.mark.parametrize('raw', ['No solution', '{"moves":["X"]}', '{"moves":[null]}', '{"moves":"R"}', '{"moves":['+','.join(['"R"']*61)+']}'])
def test_bad_model_output(raw):
    with pytest.raises(ValueError):
        live_models.parse_moves(raw)

def test_fenced_json():
    assert live_models.parse_moves("```json\n" + json.dumps({"moves": ["R'", "U2"]}) + "\n```") == ["R'", "U2"]

@pytest.mark.parametrize('reply,status,expected', [
    (json.dumps({"moves": ["U'"]}),200,"solved"),
    ('{"moves":["U"]}',200,'unsolved'),
    ('{"moves":["X"]}',200,'invalid_output'),
    ('rate limited',429,'error'),
])
def test_provider_boundary(monkeypatch, reply, status, expected):
    original = httpx.AsyncClient
    def handler(request):
        assert request.method == 'POST'
        assert request.url.host == 'text.pollinations.ai'
        return httpx.Response(status, text=reply)
    monkeypatch.setattr(live_models.httpx, 'AsyncClient', lambda **kwargs: original(transport=httpx.MockTransport(handler), **kwargs))
    from backend.app.cube_engine import apply
    result = asyncio.run(live_models.run_model(apply(SOLVED,['U']), ['U'], 42, 1))
    assert result['status'] == expected
    assert result['solved'] == (expected == 'solved')
    if expected == 'solved':
        assert result['states'][-1] == SOLVED
    if expected in ('error', 'invalid_output'):
        assert result['moves'] == [] and result['error']
