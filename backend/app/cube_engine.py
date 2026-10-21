"""Facelet-based 3x3 Rubik's cube; Singmaster moves via spatial rotations."""
from collections import deque
from dataclasses import dataclass
import random

FACES = 'URFDLB'
SOLVED = ''.join(f*9 for f in FACES)
MOVES = tuple(f+s for f in FACES for s in ('', "'", '2'))
NORMAL = {'U':(0,1,0),'D':(0,-1,0),'R':(1,0,0),'L':(-1,0,0),'F':(0,0,1),'B':(0,0,-1)}

# Each sticker is represented by (cubie coordinate, face normal).
def stickers():
    a=[]
    for f in FACES:
        for row in range(3):
            for col in range(3):
                if f=='U': p=(col-1,1,row-1)
                elif f=='D':p=(col-1,-1,1-row)
                elif f=='F':p=(col-1,1-row,1)
                elif f=='B':p=(1-col,1-row,-1)
                elif f=='R':p=(1,1-row,1-col)
                else:p=(-1,1-row,col-1)
                a.append((p,NORMAL[f]))
    return tuple(a)
STICKERS=stickers()
INDEX={v:i for i,v in enumerate(STICKERS)}
def rotate(v,axis,sign):
    x,y,z=v
    if axis==0:return (x,-sign*z,sign*y)
    if axis==1:return (sign*z,y,-sign*x)
    return (-sign*y,sign*x,z)
def permutation(face):
    normal=NORMAL[face]; axis=next(i for i,v in enumerate(normal) if v); side=normal[axis]
    # Clockwise as viewed from the selected outward face.
    mapping=[]
    for p,n in STICKERS:
        if p[axis]==side:
            target=(rotate(p,axis,-side),rotate(n,axis,-side))
        else:target=(p,n)
        mapping.append(INDEX[target])
    return tuple(mapping)
PERMS={f:permutation(f) for f in FACES}
def move(state, notation):
    if len(state)!=54 or any(state.count(f)!=9 for f in FACES):raise ValueError('invalid facelets')
    if notation not in MOVES:raise ValueError('invalid move')
    p=PERMS[notation[0]]
    for _ in range(2 if notation.endswith('2') else 3 if notation.endswith("'") else 1):
        out=list(state)
        for src,dest in enumerate(p):out[dest]=state[src]
        state=''.join(out)
    return state
def apply(state,sequence):
    for m in sequence:state=move(state,m)
    return state
def inverse(m):return m if m.endswith('2') else m[0] if m.endswith("'") else m+"'"
def scramble(depth=5,seed=None):
    if not 1<=depth<=30:raise ValueError('depth must be 1..30')
    rng=random.Random(seed); seq=[]
    for _ in range(depth):
        choices=[m for m in MOVES if not seq or m[0]!=seq[-1][0]]
        seq.append(rng.choice(choices))
    return apply(SOLVED,seq),seq

def solve(state,max_depth=6,max_nodes=120000):
    """Bounded bidirectional BFS. Returns None if depth/node budget is exceeded."""
    if state==SOLVED:return []
    if not 0<=max_depth<=8:raise ValueError('max_depth must be 0..8')
    front={state:()}; back={SOLVED:()}; fa={state};fb={SOLVED}; nodes=2
    for i in range(max_depth):
        if not fa or not fb:break
        expand_front=len(fa)<=len(fb)
        layer=fa if expand_front else fb
        own=front if expand_front else back
        other=back if expand_front else front
        next_layer=set()
        for cur in layer:
            path=own[cur]
            for m in MOVES:
                if path and m[0]==path[-1][0]:continue
                nxt=move(cur,m)
                if nxt in own:continue
                new_path=path+(m,)
                own[nxt]=new_path;nodes+=1
                if nxt in other:
                    if expand_front:
                        result=new_path+tuple(inverse(t) for t in reversed(other[nxt]))
                    else:
                        result=other[nxt]+tuple(inverse(t) for t in reversed(new_path))
                    if len(result)<=max_depth:return list(result)
                next_layer.add(nxt)
                if nodes>max_nodes:return None
        if expand_front:fa=next_layer
        else:fb=next_layer
    return None
