"""Free hosted inference; every model answer is verified by the cube engine."""
import json
import re
import time
import httpx
from .cube_engine import MOVES, SOLVED, apply

MODEL = 'openai-fast'
MODEL_NAME = 'GPT-OSS 20B'
ENDPOINT = 'https://text.pollinations.ai/'

def parse_moves(raw):
    match = re.search(r'\{[\s\S]*\}', raw)
    if not match:
        raise ValueError('Model did not return a JSON object with a moves array.')
    data = json.loads(match.group())
    moves = data.get('moves')
    if not isinstance(moves, list) or len(moves) > 60 or any(not isinstance(m, str) or m not in MOVES for m in moves):
        raise ValueError('Model returned invalid cube notation (maximum 60 moves).')
    return moves

async def run_model(state, sequence, seed, baseline_depth):
    prompt = (
        'You are solving a 3x3 Rubiks cube. It started solved and was scrambled with '
        + ' '.join(sequence) + '. '
        'Return a solution that restores the solved state. You may use the scramble history. '
        'Undo operations in reverse order; a prime turn is the inverse of a plain turn, '
        'and a double turn is its own inverse. Use standard Singmaster notation. '
        'Return ONLY JSON like {"moves":["R\u0027","U2"]}. No explanations. '
        'The current 54 facelets in URFDLB face order are: ' + state
    )
    started = time.perf_counter()
    result = dict(id='gpt-oss', name=MODEL_NAME, provider='Pollinations', model=MODEL,
                  kind='live_llm', moves=[], solved=False, optimality_gap=None,
                  status='error', raw_response='', states=[state])
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(75, connect=15), follow_redirects=True) as client:
            response = await client.post(ENDPOINT, json={
                'model': MODEL, 'messages': [{'role': 'user', 'content': prompt}],
                'seed': seed if seed is not None else 42, 'jsonMode': True,
                'temperature': 0, 'max_tokens': 200,
            })
            response.raise_for_status()
        raw = response.text[:12000]
        try:
            envelope = response.json()
            if isinstance(envelope, dict) and 'choices' in envelope:
                raw = envelope['choices'][0]['message']['content']
        except (ValueError, KeyError, IndexError, TypeError):
            pass
        result['raw_response'] = raw
        moves = parse_moves(raw)
        states = [state]
        for turn in moves:
            states.append(apply(states[-1], [turn]))
        solved = states[-1] == SOLVED
        result.update(moves=moves, states=states, solved=solved,
                      status='solved' if solved else 'unsolved',
                      optimality_gap=len(moves)-baseline_depth if solved and baseline_depth is not None else None)
    except httpx.TimeoutException:
        result['error'] = 'Free model service timed out. Retry or run the local baselines.'
    except httpx.HTTPStatusError as exc:
        result['error'] = f'Free model service returned HTTP {exc.response.status_code}. Please retry later.'
    except httpx.RequestError:
        result['error'] = 'Cannot reach the free model service. Check your internet connection.'
    except (ValueError, TypeError) as exc:
        result['status'] = 'invalid_output'
        result['error'] = str(exc)
    result['elapsed_ms'] = round((time.perf_counter()-started)*1000, 2)
    return result
