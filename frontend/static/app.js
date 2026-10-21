'use strict';
const $ = id => document.getElementById(id);
const SOLVED = [...'URFDLB'].map(f => f.repeat(9)).join('');
const cubeView = new CubeView($('cube'));
let depth = 3, running = false, selected = null, latest = null, initialState = SOLVED;
let replayRun = 0, replayIndex = 0, replayPlaying = false, replayPaused = false;
let currentSettings = null, resultList = [], pendingModel = false, runStarted = 0, ticker = null;
function updateCubeLabels(state) {
  $('cube').setAttribute('aria-label', 'Interactive 3D Rubik cube. '+(state===SOLVED?'Solved.':'Scrambled.')+' Drag or use arrow keys to rotate.');
  $('state-id').textContent = state.slice(0,9)+'…'+state.slice(-9);
  $('state-label').textContent = state===SOLVED?'SOLVED':'SCRAMBLED';
}
function renderCube(state) { cubeView.setState(state); updateCubeLabels(state); }
function hud(message, active=false) { $('turn-hud').textContent=message; $('turn-hud').classList.toggle('active',active); }
function pills(container, moves) {
  container.replaceChildren();
  for (const move of moves) { const span=document.createElement('span'); span.className='move-pill'; span.textContent=move; container.append(span); }
}
function feedback(message, type='') { $('feedback').textContent=message; $('feedback').className='feedback '+type; }
function settings() {
  const seed = $('seed').valueAsNumber;
  if (!Number.isInteger(seed) || seed<0 || seed>999999) throw Error('Enter a whole-number seed between 0 and 999999.');
  return {depth, seed, mode:$('mode').value};
}
function busy(value) {
  running=value;
  document.querySelectorAll('[data-depth], #seed, #mode, #scramble-btn, #run-btn').forEach(el=>el.disabled=value);
  $('run-btn').textContent=value?'Running…':'Run benchmark ↗';
}
function stopReplay() {
  replayRun++; replayPlaying=false; replayPaused=false; replayIndex=0; cubeView.cancel();
  $('replay-btn').textContent='Replay solution';
}
async function playSolution() {
  if(!selected?.moves.length)return;
  stopReplay();const token=replayRun, result=selected;replayPlaying=true;
  renderCube(result.states[0]);$('replay-btn').textContent='Pause';
  for(let index=0;index<result.moves.length;index++){
    if(token!==replayRun)return;
    const turn=result.moves[index];
    $('state-label').textContent='SOLVING';hud(`TURN ${index+1} / ${result.moves.length}   ${turn}`,true);
    $('replay-step').textContent=`${result.name} · ${index+1} / ${result.moves.length} · ${turn}`;
    [...$('solution-moves').children].forEach((element,i)=>element.classList.toggle('playing',i===index));
    const turnFinished=cubeView.turn(turn,result.states[index+1],900);
    cubeView.animation?.updatePlaybackRate(Number($('replay-speed').value));
    const completed=await turnFinished;
    if(!completed||token!==replayRun)return;
    replayIndex=index+1;updateCubeLabels(result.states[replayIndex]);
  }
  replayPlaying=false;replayPaused=false;$('replay-btn').textContent='Replay solution';
  hud(result.solved?'SOLVED · ALL 54 STICKERS VERIFIED':'SEQUENCE COMPLETE · NOT SOLVED',result.solved);
  $('replay-step').textContent=`${result.name} · ${replayIndex} / ${result.moves.length} moves`;
}
function togglePlayback() {
  if(replayPlaying){replayPlaying=false;replayPaused=true;cubeView.pause();$('replay-btn').textContent='Resume';$('state-label').textContent='PAUSED';hud('PAUSED · RESUME TO CONTINUE');}
  else if(replayPaused){replayPaused=false;replayPlaying=true;cubeView.resume();$('replay-btn').textContent='Pause';$('state-label').textContent='SOLVING';hud('SOLVING · '+selected.moves[replayIndex],true);}
  else void playSolution();
}
function clearResults() {
  stopReplay(); renderCube(initialState); latest=null; selected=null; resultList=[]; pendingModel=false;
  $('result-detail').hidden=true;
  $('replay-btn').disabled=true; $('reset-btn').disabled=true; $('download-btn').disabled=true;
  $('replay-step').textContent='Run a benchmark to solve';hud('READY TO SOLVE');
  for (const id of ['shortest','success','latency']) $(id).textContent='—';
  $('last-run').textContent='No experiment yet';
  $('results').replaceChildren();
  const row=document.createElement('tr'),cell=document.createElement('td');cell.colSpan=6;cell.className='empty';
  cell.textContent='Your next discovery starts with a scramble. Run a benchmark to compare approaches.';row.append(cell);$('results').append(row);
}
async function requestJSON(url,payload) {
  const response=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
  const data=await response.json();
  if (!response.ok) throw Error(typeof data.detail==='string'?data.detail:'The server rejected the request. Check the seed and difficulty.');
  return data;
}
async function newScramble() {
  if(running) return;
  let payload;try{payload=settings();}catch(error){feedback(error.message,'error');return;}
  busy(true);clearResults();
  try { const data=await requestJSON('/api/scramble',payload);initialState=data.state;renderCube(data.state);pills($('scramble-moves'),data.scramble);feedback('Puzzle ready. Run the benchmark to test it.'); }
  catch(error){feedback(error.message,'error');} finally{busy(false);}
}
function formatTime(ms){return ms>=1000?(ms/1000).toFixed(1)+' s':Math.round(ms)+' ms';}
function selectResult(result) {
  stopReplay(); selected=result;
  $('result-detail').hidden=false;$('detail-title').textContent=result.name;
  $('detail-kind').textContent=result.kind==='live_llm'?'LIVE MODEL · ENGINE VERIFIED':'LOCAL CONTROL';
  pills($('solution-moves'),result.moves);
  $('raw-response').textContent=result.error || result.raw_response || (result.moves.length?'Generated moves: '+result.moves.join(' '):'No solution found within the search budget.');
  $('replay-btn').disabled=!result.moves.length;$('reset-btn').disabled=false;
  $('replay-step').textContent='0 / '+result.moves.length+' moves';renderCube(initialState);hud(result.moves.length?'SOLUTION READY · '+result.name.toUpperCase():'NO VALID MOVES TO ANIMATE');
}
function drawResults() {
  $('results').replaceChildren();
  const rows=[...resultList].sort((a,b)=>(a.kind==='live_llm'?-1:0)-(b.kind==='live_llm'?-1:0));
  if(pendingModel) rows.unshift({id:'pending',name:'GPT-OSS 20B',kind:'live_llm',pending:true});
  for(const result of rows){
    const row=document.createElement('tr');
    const name=document.createElement('td');name.textContent=result.name;
    const sub=document.createElement('small');sub.textContent=result.kind==='live_llm'?'Pollinations · live LLM':result.id==='bfs'?'Facelet search · local':'Scramble history · local';name.append(sub);row.append(name);
    const status=document.createElement('td'),tag=document.createElement('span');tag.className='result-tag';
    if(result.pending){tag.textContent='GENERATING';tag.classList.add('pending');}
    else {tag.textContent=result.solved?'VERIFIED SOLVED':result.status==='error'?'SERVICE ERROR':result.status==='invalid_output'?'INVALID OUTPUT':result.status==='budget_limit'?'BUDGET LIMIT':'NOT SOLVED';if(!result.solved)tag.classList.add('failure');}
    status.append(tag);row.append(status);
    for(const value of [result.pending?'—':result.moves.length,result.optimality_gap??'—',result.pending?'…':formatTime(result.elapsed_ms)]){const td=document.createElement('td');td.textContent=value;row.append(td);}
    const action=document.createElement('td');if(!result.pending){const button=document.createElement('button');button.className='small-btn';button.textContent='View ↗';button.setAttribute('aria-label','Inspect '+result.name+' result');button.addEventListener('click',()=>selectResult(result));action.append(button);}row.append(action);$('results').append(row);
  }
  $('success').textContent=resultList.filter(x=>x.solved).length+' / '+(resultList.length+(pendingModel?1:0));
  const live=resultList.find(x=>x.kind==='live_llm');$('latency').textContent=live?formatTime(live.elapsed_ms):pendingModel?'…':'—';
}
function handleEvent(type,data) {
  if(type==='start'){initialState=data.initial_state;renderCube(initialState);pills($('scramble-moves'),data.scramble);if(data.mode==='live'){$('state-label').textContent='THINKING';hud('WAITING FOR LIVE MODEL MOVES');}}
  if(type==='result'){resultList.push(data);if(data.kind==='live_llm'){pendingModel=false;selectResult(data);if(data.moves.length)void playSolution();}drawResults();}
  if(type==='error')throw Error(data.message);
  if(type==='complete'){
    pendingModel=false;latest=data;resultList=data.results;drawResults();
    $('shortest').textContent=data.baseline_depth??'N/A';$('last-run').textContent='Seed '+currentSettings.seed+' · '+depth+' scramble moves';
    $('download-btn').disabled=false;
    const live=data.results.find(x=>x.kind==='live_llm');
    const candidate=live||data.results.find(x=>x.id==='bfs'&&x.solved)||data.results[0];
    if(selected?.id!==candidate.id){selectResult(candidate);if(candidate.moves.length)void playSolution();}
    if(live?.error) feedback(live.error+' Local controls are available below.','error');
    else feedback(live?(live.solved?'Live answer verified. The 3D cube is playing the model moves automatically.':'Live answer received. The engine found that it does not solve this cube.'):'Local controls completed. Choose Live LLM to call the model.');
  }
}
async function run() {
  if(running)return;
  try{currentSettings=settings();}catch(error){feedback(error.message,'error');return;}
  clearResults();busy(true);pendingModel=currentSettings.mode==='live';drawResults();
  runStarted=Date.now();if(pendingModel){$('state-label').textContent='THINKING';hud('WAITING FOR LIVE MODEL MOVES');}feedback(pendingModel?'Calling GPT-OSS 20B. Free inference can take up to 75 seconds.':'Running local search…','running');
  ticker=setInterval(()=>{if(pendingModel)feedback('GPT-OSS 20B is generating · '+Math.floor((Date.now()-runStarted)/1000)+'s elapsed','running');},1000);
  const controller=new AbortController(),timeout=setTimeout(()=>controller.abort(),100000);
  try{
    const response=await fetch('/api/race/stream',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(currentSettings),signal:controller.signal});
    if(!response.ok){const error=await response.json();throw Error(error.detail||'Benchmark request failed.');}
    const reader=response.body.getReader(),decoder=new TextDecoder();let buffer='';
    while(true){const {done,value}=await reader.read();if(done)break;buffer+=decoder.decode(value,{stream:true});let end;
      while((end=buffer.indexOf('\n\n'))!==-1){const frame=buffer.slice(0,end);buffer=buffer.slice(end+2);const event=frame.split('\n').find(x=>x.startsWith('event: '));const payload=frame.split('\n').find(x=>x.startsWith('data: '));if(event&&payload)handleEvent(event.slice(7),JSON.parse(payload.slice(6)));}
    }
    if(!latest)throw Error('Connection closed before the benchmark finished. Please retry.');
  }catch(error){pendingModel=false;drawResults();feedback(error.name==='AbortError'?'Benchmark timed out. Please retry.':error.message,'error');}
  finally{clearInterval(ticker);clearTimeout(timeout);busy(false);}
}
$('replay-btn').addEventListener('click',togglePlayback);
$('view-reset-btn').addEventListener('click',()=>cubeView.resetCamera());
$('reset-btn').addEventListener('click',()=>{stopReplay();renderCube(initialState);hud('SCRAMBLED · READY TO REPLAY');$('replay-step').textContent='0 / '+selected.moves.length+' moves';[...$('solution-moves').children].forEach(element=>element.classList.remove('playing'));});
$('replay-speed').addEventListener('change',()=>{if(cubeView.animation)cubeView.animation.updatePlaybackRate(Number($('replay-speed').value));});
$('download-btn').addEventListener('click',()=>{if(!latest)return;const url=URL.createObjectURL(new Blob([JSON.stringify(latest,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='cubelab-seed-'+latest.seed+'.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);});
document.querySelectorAll('[data-depth]').forEach(button=>button.addEventListener('click',()=>{document.querySelectorAll('[data-depth]').forEach(el=>{const active=el===button;el.classList.toggle('selected',active);el.setAttribute('aria-pressed',String(active));});depth=Number(button.dataset.depth);newScramble();}));
$('seed').addEventListener('change',newScramble);
$('mode').addEventListener('change',()=>{clearResults();const live=$('mode').value==='live';$('mode-stat').textContent=live?'LIVE':'LOCAL';$('mode-caption').textContent=live?'Hosted language model':'Deterministic controls';feedback(live?'Ready for a live model request.':'Local controls selected. No model request will be made.');});
$('scramble-btn').addEventListener('click',newScramble);$('run-btn').addEventListener('click',run);
fetch('/api/health').then(r=>{if(!r.ok)throw Error();return r.json();}).then(()=>$('health').textContent='Local server online').catch(()=>$('health').textContent='Server unavailable');
renderCube(SOLVED);newScramble();
