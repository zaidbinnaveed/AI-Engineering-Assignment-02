'use strict';
/* CSS 3D cubies use the same coordinates and face order as cube_engine.py. */
(() => {
  const FACES = 'URFDLB';
  const NORMALS = {U:[0,1,0], R:[1,0,0], F:[0,0,1], D:[0,-1,0], L:[-1,0,0], B:[0,0,-1]};
  const SIDES = {U:'rotateX(90deg)', D:'rotateX(-90deg)', R:'rotateY(90deg)', L:'rotateY(-90deg)', F:'', B:'rotateY(180deg)'};
  const STEP = 61, HALF = 30;
  function facelets() {
    const items = [];
    for (const [faceIndex, face] of [...FACES].entries()) {
      for (let row=0; row<3; row++) for (let col=0; col<3; col++) {
        let p;
        if (face==='U') p=[col-1,1,row-1];
        else if (face==='D') p=[col-1,-1,1-row];
        else if (face==='F') p=[col-1,1-row,1];
        else if (face==='B') p=[1-col,1-row,-1];
        else if (face==='R') p=[1,1-row,1-col];
        else p=[-1,1-row,col-1];
        items.push({p, n:NORMALS[face], face, index:faceIndex*9+row*3+col});
      }
    }
    return items;
  }
  const STICKERS = facelets();
  function turnSpec(move) {
    if (!/^[URFDLB](2|')?$/.test(move)) throw Error('Invalid cube turn');
    const normal=NORMALS[move[0]], axis=normal.findIndex(value=>value!==0), side=normal[axis];
    // Reflect the engine's upward Y into the browser's downward Y coordinates.
    const angle=-side*90*(axis===1?1:-1)*(move.endsWith('2')?2:move.endsWith("'")?-1:1);
    return {axis, side, angle, transform:`rotate${'XYZ'[axis]}(${angle}deg)`};
  }
  class CubeView {
    static facelets = facelets;
    static turnSpec = turnSpec;
    constructor(element) {
      this.element=element; this.pitch=-24; this.yaw=-34; this.animation=null; this.turning=false;
      this.updateCamera();
      const viewport=element.closest('.cube-stage');
      let drag=null;
      viewport.addEventListener('pointerdown', event=>{
        if(event.button!==0) return;
        drag={x:event.clientX,y:event.clientY}; viewport.setPointerCapture(event.pointerId);
        viewport.classList.add('dragging'); element.focus({preventScroll:true});
      });
      viewport.addEventListener('pointermove', event=>{
        if(!drag)return;
        this.yaw+=(event.clientX-drag.x)*.5; this.pitch=Math.max(-85,Math.min(85,this.pitch-(event.clientY-drag.y)*.5));
        drag={x:event.clientX,y:event.clientY}; this.updateCamera();
      });
      const release=()=>{drag=null;viewport.classList.remove('dragging');};
      viewport.addEventListener('pointerup',release);viewport.addEventListener('pointercancel',release);
      element.addEventListener('keydown',event=>{
        if(!['ArrowLeft','ArrowRight','ArrowUp','ArrowDown','Home'].includes(event.key))return;
        event.preventDefault();
        if(event.key==='Home')this.resetCamera();
        else{this.yaw+=event.key==='ArrowLeft'?-15:event.key==='ArrowRight'?15:0;this.pitch=Math.max(-85,Math.min(85,this.pitch+(event.key==='ArrowUp'?-15:event.key==='ArrowDown'?15:0)));this.updateCamera();}
      });
    }
    updateCamera(){this.element.style.transform=`rotateX(${this.pitch}deg) rotateY(${this.yaw}deg)`;}
    resetCamera(){this.pitch=-24;this.yaw=-34;this.updateCamera();}
    setState(state) {
      this.cancel(); this.state=state; this.element.dataset.state=state; this.element.replaceChildren();
      const colors=new Map(STICKERS.map(sticker=>[[...sticker.p,sticker.face].join(','),{color:state[sticker.index],index:sticker.index}]));
      for(let x=-1;x<=1;x++)for(let y=-1;y<=1;y++)for(let z=-1;z<=1;z++){
        if(x===0&&y===0&&z===0)continue;
        const cubie=document.createElement('div');cubie.className='cubie';cubie.dataset.position=[x,y,z].join(',');
        cubie.style.transform=`translate3d(${x*STEP}px,${-y*STEP}px,${z*STEP}px)`;
        for(const face of FACES){
          const side=document.createElement('div');side.className='cubie-side side-'+face;
          side.style.transform=`${SIDES[face]} translateZ(${HALF}px)`;
          const sticker=colors.get([x,y,z,face].join(','));
          if(sticker){const tile=document.createElement('span');tile.className='sticker tile '+sticker.color;tile.dataset.index=sticker.index;side.append(tile);}
          cubie.append(side);
        }
        this.element.append(cubie);
      }
      this.element.setAttribute('aria-label','3D Rubik’s cube. Drag or use arrow keys to rotate.');
    }
    async turn(move, nextState, duration=900) {
      const {axis,side,transform}=turnSpec(move);
      const layer=document.createElement('div');layer.className='turning-layer';layer.dataset.move=move;
      for(const cubie of [...this.element.children])if(Number(cubie.dataset.position?.split(',')[axis])===side)layer.append(cubie);
      this.element.append(layer);this.turning=true;this.element.dataset.turn=move;
      const reduced=window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      const animation=layer.animate([{transform:`rotate${'XYZ'[axis]}(0deg)`},{transform}],{duration:reduced?120:duration,easing:'cubic-bezier(.35,0,.2,1)',fill:'forwards'});
      this.animation=animation;
      try{await animation.finished;}catch{return false;}
      if(this.animation!==animation)return false;
      this.animation=null;this.turning=false;this.element.removeAttribute('data-turn');
      this.setState(nextState);return true;
    }
    pause(){this.animation?.pause();}
    resume(){this.animation?.play();}
    cancel(){if(this.animation){this.animation.cancel();this.animation=null;}this.turning=false;this.element.removeAttribute('data-turn');}
  }
  window.CubeView=CubeView;
})();
