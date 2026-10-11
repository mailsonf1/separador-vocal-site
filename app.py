import os
import re
from urllib.parse import urlparse, unquote

import requests
from flask import Flask, request, jsonify, render_template_string, Response
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024

API_BASE = "https://mvsep.com/api"
API_KEY = os.environ.get("MVSEP_API_KEY", "")
ALLOWED_EXTENSIONS = {"mp3", "wav", "flac", "m4a", "ogg", "aac", "aiff", "wma"}

HTML = r"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MFSTUDIO | Separador e Masterizador</title>
<style>
:root{--bg:#090916;--panel:#131329;--text:#f7f7ff;--muted:#aaaac8;--purple:#9b5cff;--pink:#ff3eaa;--cyan:#22e6ff;--lime:#b8ff4b;--orange:#ffad42}
*{box-sizing:border-box}body{margin:0;min-height:100vh;background:radial-gradient(ellipse at 8% 0%,#44208055,transparent 35%),radial-gradient(ellipse at 100% 20%,#005e7950,transparent 32%),var(--bg);color:var(--text);font-family:Inter,system-ui,-apple-system,"Segoe UI",sans-serif}
.container{width:min(960px,92%);margin:0 auto;padding:32px 0 60px}header{display:flex;align-items:center;justify-content:space-between;gap:16px;margin-bottom:48px}.brand{display:flex;align-items:center;gap:12px;font-weight:900;letter-spacing:1px;font-size:22px}.brand-mark{width:44px;height:44px;border-radius:14px;display:grid;place-items:center;font-size:23px;background:linear-gradient(135deg,var(--purple),var(--pink));box-shadow:0 0 30px #9b5cff55}.pill{border:1px solid #ffffff20;border-radius:999px;padding:8px 13px;color:var(--cyan);font-size:12px;font-weight:800;letter-spacing:1px}.hero{text-align:center;margin-bottom:32px}.eyebrow{color:var(--cyan);font-size:12px;font-weight:900;letter-spacing:3px;text-transform:uppercase}h1{font-size:clamp(36px,7vw,62px);line-height:1.05;margin:15px 0;letter-spacing:-2px}.gradient-text{background:linear-gradient(90deg,var(--cyan),#b38aff,var(--pink));-webkit-background-clip:text;background-clip:text;color:transparent}.subtitle{max-width:590px;margin:0 auto;color:var(--muted);line-height:1.7;font-size:15px}.panel{background:linear-gradient(145deg,#17172fef,#101020f5);border:1px solid #ffffff18;border-radius:26px;padding:clamp(18px,4vw,32px);box-shadow:0 24px 70px #00000040;margin-bottom:22px}.upload-area{border:2px dashed #8c63ff88;background:linear-gradient(135deg,#9b5cff0d,#22e6ff08);border-radius:20px;padding:36px 16px;text-align:center;transition:.2s ease}.upload-area.dragover{border-color:var(--cyan);background:#22e6ff12;transform:scale(1.01)}.upload-icon{width:68px;height:68px;margin:0 auto 15px;display:grid;place-items:center;font-size:32px;border-radius:22px;background:linear-gradient(135deg,#9b5cff30,#ff3eaa25)}.upload-area h2{font-size:20px;margin:8px 0}.upload-area p{color:var(--muted);font-size:13px}.file-name{display:none;margin-top:14px;color:var(--lime);font-size:13px;overflow-wrap:anywhere}input[type=file]{display:none}button,.choose-button{border:0;cursor:pointer;color:white;font-weight:800;font-size:13px;border-radius:13px;padding:12px 15px;transition:transform .15s,filter .15s}button:hover,.choose-button:hover{transform:translateY(-2px);filter:brightness(1.1)}button:disabled{opacity:.45;cursor:not-allowed;transform:none}.choose-button{display:inline-block;background:#282849;border:1px solid #ffffff20;margin-top:10px}.primary{width:100%;margin-top:20px;padding:17px;background:linear-gradient(90deg,#853dff,#ff3eaa);box-shadow:0 10px 28px #a23dff35;font-size:15px}.status{display:none;margin-top:20px;border-radius:14px;padding:14px 16px;background:#22e6ff0c;border:1px solid #22e6ff35;color:var(--cyan);font-size:13px;line-height:1.6;overflow-wrap:anywhere}.status.error{color:#ff819f;border-color:#ff3eaa66;background:#ff3eaa0c}.progress-track{display:none;height:7px;border-radius:99px;background:#ffffff12;margin-top:13px;overflow:hidden}.progress-bar{height:100%;width:35%;border-radius:99px;background:linear-gradient(90deg,var(--cyan),var(--purple),var(--pink));animation:progress 1.5s ease-in-out infinite alternate}@keyframes progress{from{transform:translateX(-15%)}to{transform:translateX(190%)}}.section-title{display:flex;justify-content:space-between;align-items:center;gap:12px;margin-bottom:20px}.section-title h2{margin:0;font-size:21px}.section-title span{color:var(--muted);font-size:12px}.results{display:none}.track-list{display:grid;gap:12px}.track{--accent:var(--purple);border:1px solid #ffffff15;background:#ffffff06;border-radius:17px;padding:15px;min-width:0}.track-top{display:flex;align-items:center;gap:14px;min-width:0}.track-icon{flex:0 0 48px;height:48px;border-radius:15px;display:grid;place-items:center;font-size:25px;background:#ffffff10;border:1px solid #ffffff20}.track-info{flex:1;min-width:0}.track-info strong{display:block;font-size:14px;overflow-wrap:anywhere}.track-info small{display:block;color:var(--muted);font-size:12px;margin-top:5px}.track-actions{display:flex;flex-wrap:wrap;gap:8px;justify-content:flex-end}.download{background:var(--accent);color:#090916}.master-btn{background:#292344;border:1px solid #9b5cff66}.track:nth-child(1){--accent:var(--orange)}.track:nth-child(2){--accent:var(--cyan)}.track:nth-child(3){--accent:var(--lime)}.track:nth-child(4){--accent:var(--pink)}.track:nth-child(5){--accent:var(--purple)}.master-panel{display:none;margin-top:16px;padding:16px;border:1px solid #9b5cff44;border-radius:15px;background:#0b0b1b}.master-panel h3{margin:0 0 5px;font-size:16px}.master-help{font-size:12px;color:var(--muted);line-height:1.5;margin:0 0 15px}.controls{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}.control label{display:flex;justify-content:space-between;gap:10px;font-size:12px;color:#e8e6ff;margin-bottom:7px}.control output{color:var(--cyan);font-variant-numeric:tabular-nums}.control input[type=range]{width:100%;accent-color:var(--purple)}.master-actions{display:flex;gap:8px;flex-wrap:wrap;margin-top:15px}.process-btn{background:linear-gradient(90deg,#853dff,#ff3eaa)}.secondary{background:#282849;border:1px solid #ffffff20}.preview{width:100%;height:38px;margin-top:12px;display:none}footer{text-align:center;color:#777797;font-size:12px;padding-top:15px}.fineprint{color:#8585a8;font-size:11px;line-height:1.5;margin-top:10px}@media(max-width:560px){header{margin-bottom:35px}.pill{display:none}.track-top{align-items:flex-start;gap:10px}.track-icon{flex-basis:42px;height:42px;font-size:22px}.track-actions{width:100%;justify-content:flex-start;margin-top:12px}.track-actions button{flex:1}.track-info strong{font-size:13px}.controls{grid-template-columns:1fr}}
</style>
</head>
<body><div class="container">
<header><div class="brand"><div class="brand-mark">♫</div><span>MF<span class="gradient-text">STUDIO</span></span></div><div class="pill">AUDIO LAB · ONLINE</div></header>
<section class="hero"><div class="eyebrow">Seu som. Do seu jeito.</div><h1>Separe sua música<br><span class="gradient-text">em segundos.</span></h1><p class="subtitle">Extraia voz, bateria, baixo e outros instrumentos. Baixe cada faixa e faça ajustes de masterização individualmente.</p></section>
<section class="panel"><form id="uploadForm"><div class="upload-area" id="dropArea"><div class="upload-icon">🎧</div><h2>Escolha sua música</h2><p>Arraste o arquivo para cá ou selecione no seu dispositivo.</p><label class="choose-button" for="audioFile">📂 Selecionar arquivo</label><input id="audioFile" name="audiofile" type="file" accept=".mp3,.wav,.flac,.m4a,.ogg,.aac,.aiff,.wma" required><div class="file-name" id="fileName"></div></div><button class="primary" id="submitButton" type="submit">✨ Separar minha música</button></form><div class="status" id="status"></div><div class="progress-track" id="progressTrack"><div class="progress-bar"></div></div></section>
<section class="panel results" id="results"><div class="section-title"><h2>🎵 Suas faixas</h2><span id="trackCount"></span></div><div class="track-list" id="trackList"></div></section>
<footer>MFSTUDIO · Ferramentas para quem ama música<div class="fineprint">A restauração e a masterização são feitas no navegador. A suavização espectral é experimental, funciona melhor com ajustes moderados e está limitada a 5 minutos por faixa para evitar travamentos.</div></footer></div>
<script>
const form=document.getElementById('uploadForm'),audioFile=document.getElementById('audioFile'),fileName=document.getElementById('fileName'),dropArea=document.getElementById('dropArea'),statusBox=document.getElementById('status'),submitButton=document.getElementById('submitButton'),progressTrack=document.getElementById('progressTrack'),results=document.getElementById('results'),trackList=document.getElementById('trackList'),trackCount=document.getElementById('trackCount');
let originalBaseName='Audio',pollingTimer=null;
audioFile.addEventListener('change',()=>showSelectedFile(audioFile.files[0]));
function showSelectedFile(file){if(!file)return;fileName.textContent='✓ '+file.name;fileName.style.display='block';originalBaseName=file.name.replace(/\.[^.]+$/,'').trim()||'Audio'}
['dragenter','dragover'].forEach(n=>dropArea.addEventListener(n,e=>{e.preventDefault();dropArea.classList.add('dragover')}));['dragleave','drop'].forEach(n=>dropArea.addEventListener(n,e=>{e.preventDefault();dropArea.classList.remove('dragover')}));
dropArea.addEventListener('drop',e=>{const files=e.dataTransfer.files;if(!files.length)return;const dt=new DataTransfer();dt.items.add(files[0]);audioFile.files=dt.files;showSelectedFile(files[0])});
function setStatus(message,isError=false){statusBox.textContent=message;statusBox.style.display='block';statusBox.classList.toggle('error',isError)}
function getTrackInfo(url,name){const t=((url||'')+' '+(name||'')).toLowerCase();if(t.includes('instrumental'))return{label:'Instrumental',emoji:'🎼'};if(t.includes('vocal')||t.includes('voice'))return{label:'Voz isolada',emoji:'🎤'};if(t.includes('drum'))return{label:'Bateria',emoji:'🥁'};if(t.includes('bass'))return{label:'Baixo',emoji:'🎸'};if(t.includes('other'))return{label:'Outros instrumentos',emoji:'🎹'};if(t.includes('guitar'))return{label:'Guitarra',emoji:'🎸'};if(t.includes('piano'))return{label:'Piano',emoji:'🎹'};if(t.includes('strings'))return{label:'Cordas',emoji:'🎻'};if(t.includes('woodwind'))return{label:'Sopros',emoji:'🎷'};if(t.includes('brass'))return{label:'Metais',emoji:'🎺'};return{label:name||'Faixa separada',emoji:'🎵'}}
function getExtension(url){try{const p=new URL(url,location.origin).pathname,m=p.match(/\.([a-z0-9]{2,5})$/i);return m?m[1].toLowerCase():'mp3'}catch{return'mp3'}}
function safeFilenamePart(n){return n.replace(/[<>:"/\\|?*\x00-\x1F]/g,'_').replace(/\s+/g,' ').trim().replace(/[. ]+$/,'')||'Audio'}
function downloadUrl(url,name){return '/api/baixar?url='+encodeURIComponent(url)+'&name='+encodeURIComponent(name)}
function makeRange(label,min,max,step,value,unit=' dB'){const id='m_'+Math.random().toString(36).slice(2);const wrap=document.createElement('div');wrap.className='control';const lab=document.createElement('label');lab.htmlFor=id;const span=document.createElement('span');span.textContent=label;const out=document.createElement('output');out.textContent=value+unit;lab.append(span,out);const input=document.createElement('input');input.type='range';input.id=id;input.min=min;input.max=max;input.step=step;input.value=value;input.addEventListener('input',()=>out.textContent=input.value+unit);wrap.append(lab,input);return{wrap,input}}
function addMasterPanel(row,url,downloadName,trackTitle){
 const panel=document.createElement('div');panel.className='master-panel';
 const heading=document.createElement('h3');heading.textContent='🧹 Restaurar e masterizar: '+trackTitle;
 const help=document.createElement('p');help.className='master-help';help.textContent='A suavização espectral tenta reduzir ressonâncias estreitas que podem soar metálicas após a separação. Use com moderação: nenhum filtro consegue reconstruir perfeitamente o áudio perdido. O original não será alterado.';
 const controls=document.createElement('div');controls.className='controls';
 const cleanup=makeRange('Suavização de artefatos',0,50,5,20,'%');
 const gain=makeRange('Volume',-12,12,0.5,0,' dB'),bass=makeRange('Graves · 120 Hz',-9,9,0.5,0,' dB'),mids=makeRange('Médios · 1 kHz',-9,9,0.5,0,' dB'),treble=makeRange('Agudos · 8 kHz',-9,9,0.5,0,' dB'),threshold=makeRange('Compressão',-36,-6,1,-18,' dB');
 [cleanup,gain,bass,mids,treble,threshold].forEach(x=>controls.append(x.wrap));
 const actions=document.createElement('div');actions.className='master-actions';
 const process=document.createElement('button');process.className='process-btn';process.textContent='🧹 Limpar e baixar WAV';
 const reset=document.createElement('button');reset.className='secondary';reset.textContent='Restaurar ajustes';
 const audio=document.createElement('audio');audio.className='preview';audio.controls=true;actions.append(process,reset);panel.append(heading,help,controls,actions,audio);row.append(panel);
 reset.addEventListener('click',()=>{[[cleanup,20],[gain,0],[bass,0],[mids,0],[treble,0],[threshold,-18]].forEach(([o,v])=>{o.input.value=v;o.input.dispatchEvent(new Event('input'))});audio.pause();audio.removeAttribute('src');audio.style.display='none'});
 process.addEventListener('click',async()=>{
  process.disabled=true;process.textContent='⏳ Limpando e processando...';
  try{
   const response=await fetch(downloadUrl(url,downloadName));if(!response.ok)throw new Error('Não foi possível carregar a faixa para restauração.');
   const bytes=await response.arrayBuffer();const AudioCtx=window.AudioContext||window.webkitAudioContext;if(!AudioCtx)throw new Error('Seu navegador não oferece suporte ao processamento de áudio.');
   const decodeCtx=new AudioCtx();let decoded;try{decoded=await decodeCtx.decodeAudioData(bytes.slice(0))}finally{await decodeCtx.close()}
   if(decoded.length>decoded.sampleRate*60*20)throw new Error('Para evitar falta de memória, esta versão limita cada faixa a 20 minutos.');
   const amount=Number(cleanup.input.value)/100;
   if(amount>0 && decoded.length>decoded.sampleRate*60*5)throw new Error('A limpeza espectral está limitada a faixas de até 5 minutos para evitar que o navegador trave. Reduza a duração da faixa ou deixe Suavização de artefatos em 0%.');
   let sourceBuffer=decoded;
   if(amount>0){
    setStatus('Aplicando suavização espectral em '+trackTitle+'. Isso pode levar algum tempo...');
    const cleaned=new AudioBuffer({length:decoded.length,numberOfChannels:decoded.numberOfChannels,sampleRate:decoded.sampleRate});
    for(let channel=0;channel<decoded.numberOfChannels;channel++){
     const output=spectralSmoothChannel(decoded.getChannelData(channel),amount);
     cleaned.copyToChannel(output,channel);
    }
    sourceBuffer=cleaned;
   }
   const offline=new OfflineAudioContext(sourceBuffer.numberOfChannels,sourceBuffer.length,sourceBuffer.sampleRate);const source=offline.createBufferSource();source.buffer=sourceBuffer;
   const low=offline.createBiquadFilter();low.type='lowshelf';low.frequency.value=120;low.gain.value=Number(bass.input.value);
   const mid=offline.createBiquadFilter();mid.type='peaking';mid.frequency.value=1000;mid.Q.value=0.8;mid.gain.value=Number(mids.input.value);
   const high=offline.createBiquadFilter();high.type='highshelf';high.frequency.value=8000;high.gain.value=Number(treble.input.value);
   const compressor=offline.createDynamicsCompressor();compressor.threshold.value=Number(threshold.input.value);compressor.knee.value=12;compressor.ratio.value=3;compressor.attack.value=0.005;compressor.release.value=0.22;
   const gainNode=offline.createGain();gainNode.gain.value=Math.pow(10,Number(gain.input.value)/20);
   const limiter=offline.createDynamicsCompressor();limiter.threshold.value=-1;limiter.knee.value=0;limiter.ratio.value=20;limiter.attack.value=0.003;limiter.release.value=0.1;
   source.connect(low);low.connect(mid);mid.connect(high);high.connect(compressor);compressor.connect(gainNode);gainNode.connect(limiter);limiter.connect(offline.destination);source.start();
   const rendered=await offline.startRendering();const wav=audioBufferToWav(rendered);const blob=new Blob([wav],{type:'audio/wav'});const blobUrl=URL.createObjectURL(blob);
   if(audio.src.startsWith('blob:'))URL.revokeObjectURL(audio.src);audio.src=blobUrl;audio.style.display='block';audio.load();
   const a=document.createElement('a');a.href=blobUrl;a.download=safeFilenamePart(downloadName.replace(/\.[^.]+$/,''))+' - Restaurado.wav';document.body.append(a);a.click();a.remove();
   setStatus('Processamento concluído para '+trackTitle+'. A faixa restaurada foi baixada em WAV. Compare com o original: se o som ficar abafado, reduza a suavização.');
  }catch(err){setStatus(err.message||'Não foi possível restaurar esta faixa.',true)}finally{process.disabled=false;process.textContent='🧹 Limpar e baixar WAV'}
 });return panel
}
function spectralSmoothChannel(input,amount){
 // STFT de 1024 pontos: atenua parcialmente picos espectrais muito estreitos, preservando a fase.
 // É uma suavização leve, não uma restauração neural nem uma garantia de remoção de todo artefato.
 const N=1024,hop=512,half=N/2,eps=1e-9,length=input.length;
 const window=new Float32Array(N);for(let n=0;n<N;n++)window[n]=0.5-0.5*Math.cos(2*Math.PI*n/(N-1));
 const out=new Float64Array(length+N),norm=new Float64Array(length+N),re=new Float64Array(N),im=new Float64Array(N),mag=new Float64Array(half+1),smooth=new Float64Array(half+1);
 function fft(real,imag,inverse){
  for(let i=1,j=0;i<N;i++){let bit=N>>1;for(;j&bit;bit>>=1)j^=bit;j^=bit;if(i<j){let tr=real[i];real[i]=real[j];real[j]=tr;tr=imag[i];imag[i]=imag[j];imag[j]=tr}}
  for(let size=2;size<=N;size<<=1){const angle=(inverse?2:-2)*Math.PI/size,wr0=Math.cos(angle),wi0=Math.sin(angle),halfSize=size>>1;for(let base=0;base<N;base+=size){let wr=1,wi=0;for(let j=0;j<halfSize;j++){const even=base+j,odd=even+halfSize,tr=wr*real[odd]-wi*imag[odd],ti=wr*imag[odd]+wi*real[odd];real[odd]=real[even]-tr;imag[odd]=imag[even]-ti;real[even]+=tr;imag[even]+=ti;const nextWr=wr*wr0-wi*wi0;wi=wr*wi0+wi*wr0;wr=nextWr}}}
  if(inverse)for(let i=0;i<N;i++){real[i]/=N;imag[i]/=N}
 }
 for(let start=-half;start<length;start+=hop){
  for(let n=0;n<N;n++){const ix=start+n;re[n]=(ix>=0&&ix<length?input[ix]:0)*window[n];im[n]=0}
  fft(re,im,false);
  for(let k=0;k<=half;k++)mag[k]=Math.hypot(re[k],im[k]);
  for(let k=0;k<=half;k++){let sum=0,count=0;for(let d=-2;d<=2;d++){const j=k+d;if(j>=0&&j<=half){sum+=mag[j];count++}}smooth[k]=sum/count}
  for(let k=1;k<half;k++){
   const m=mag[k],local=smooth[k];if(m>local*1.22&&m>eps){const excess=Math.min(0.7,Math.max(0,(m-local*1.22)/(m+eps)));const factor=1-amount*excess;re[k]*=factor;im[k]*=factor;const mirror=N-k;re[mirror]*=factor;im[mirror]*=factor}
  }
  fft(re,im,true);
  for(let n=0;n<N;n++){const ix=start+n;if(ix>=0&&ix<out.length){const w=window[n];out[ix]+=re[n]*w;norm[ix]+=w*w}}
 }
 const result=new Float32Array(length);for(let i=0;i<length;i++)result[i]=norm[i]>1e-7?out[i]/norm[i]:input[i];return result
}
function audioBufferToWav(buffer){const channels=buffer.numberOfChannels,length=buffer.length,dataSize=length*channels*2,array=new ArrayBuffer(44+dataSize),view=new DataView(array);function writeStr(offset,s){for(let i=0;i<s.length;i++)view.setUint8(offset+i,s.charCodeAt(i))}writeStr(0,'RIFF');view.setUint32(4,36+dataSize,true);writeStr(8,'WAVE');writeStr(12,'fmt ');view.setUint32(16,16,true);view.setUint16(20,1,true);view.setUint16(22,channels,true);view.setUint32(24,buffer.sampleRate,true);view.setUint32(28,buffer.sampleRate*channels*2,true);view.setUint16(32,channels*2,true);view.setUint16(34,16,true);writeStr(36,'data');view.setUint32(40,dataSize,true);let offset=44;const arrays=[];for(let c=0;c<channels;c++)arrays.push(buffer.getChannelData(c));for(let i=0;i<length;i++){for(let c=0;c<channels;c++){let sample=Math.max(-1,Math.min(1,arrays[c][i]));view.setInt16(offset,sample<0?sample*32768:sample*32767,true);offset+=2}}return array}
function renderTracks(files){trackList.innerHTML='';results.style.display='block';const valid=files.filter(f=>f&&(f.url||f.download_url||f.file));trackCount.textContent=valid.length+(valid.length===1?' faixa':' faixas');valid.forEach(file=>{const url=file.url||file.download_url||file.file,info=getTrackInfo(url,file.name||file.title||''),ext=getExtension(url),base=safeFilenamePart(originalBaseName),name=base+' - '+info.label+'.'+ext,row=document.createElement('div');row.className='track';const top=document.createElement('div');top.className='track-top';const icon=document.createElement('div');icon.className='track-icon';icon.textContent=info.emoji;const details=document.createElement('div');details.className='track-info';const title=document.createElement('strong');title.textContent=info.emoji+' '+base+' - '+info.label;const subtitle=document.createElement('small');subtitle.textContent='Arquivo .'+ext.toUpperCase()+' · Pronto para baixar';details.append(title,subtitle);const actions=document.createElement('div');actions.className='track-actions';const dl=document.createElement('button');dl.className='download';dl.type='button';dl.textContent='⬇ Baixar original';dl.addEventListener('click',()=>location.href=downloadUrl(url,name));const master=document.createElement('button');master.className='master-btn';master.type='button';master.textContent='🎚️ Masterizar';actions.append(dl,master);top.append(icon,details,actions);row.append(top);const panel=addMasterPanel(row,url,name,info.label);master.addEventListener('click',()=>{const open=panel.style.display==='block';panel.style.display=open?'none':'block';master.textContent=open?'🎚️ Masterizar':'✕ Fechar masterização'});trackList.append(row)});if(!valid.length)setStatus('O processamento terminou, mas não encontrei links de download válidos.',true);else{setStatus('✅ Música separada com sucesso! Baixe as faixas ou abra Masterizar para ajustar cada uma.');results.scrollIntoView({behavior:'smooth',block:'start'})}}
async function checkStatus(hash){try{const r=await fetch('/api/status/'+encodeURIComponent(hash)),data=await r.json();if(!r.ok||data.error)throw new Error(data.error||'Não foi possível consultar o processamento.');if(data.status==='done'){clearInterval(pollingTimer);pollingTimer=null;submitButton.disabled=false;submitButton.textContent='✨ Separar outra música';progressTrack.style.display='none';renderTracks(data.files||[])}else if(data.status==='error'){clearInterval(pollingTimer);pollingTimer=null;submitButton.disabled=false;submitButton.textContent='✨ Tentar novamente';progressTrack.style.display='none';setStatus(data.message||'O processamento falhou. Tente novamente.',true)}else setStatus(data.message||'Estamos separando sua música. Isso pode levar alguns minutos.')}catch(err){clearInterval(pollingTimer);pollingTimer=null;submitButton.disabled=false;submitButton.textContent='✨ Tentar novamente';progressTrack.style.display='none';setStatus(err.message||'Erro ao consultar o processamento.',true)}}
form.addEventListener('submit',async e=>{e.preventDefault();const file=audioFile.files[0];if(!file){setStatus('Selecione um arquivo de áudio primeiro.',true);return}if(pollingTimer){clearInterval(pollingTimer);pollingTimer=null}originalBaseName=file.name.replace(/\.[^.]+$/,'').trim()||'Audio';results.style.display='none';trackList.innerHTML='';submitButton.disabled=true;submitButton.textContent='⏳ Enviando música...';progressTrack.style.display='block';setStatus('Enviando seu arquivo. Aguarde...');try{const fd=new FormData();fd.append('audiofile',file);const r=await fetch('/api/separar',{method:'POST',body:fd}),data=await r.json();if(!r.ok||data.error)throw new Error(data.error||'Não foi possível iniciar a separação.');const hash=data.hash||data.job_hash||data.id;if(!hash)throw new Error('O serviço não retornou o identificador do processamento.');submitButton.textContent='🎧 Separando...';setStatus('Arquivo recebido! A separação pode levar alguns minutos.');pollingTimer=setInterval(()=>checkStatus(hash),4000);await checkStatus(hash)}catch(err){submitButton.disabled=false;submitButton.textContent='✨ Tentar novamente';progressTrack.style.display='none';setStatus(err.message||'Ocorreu um erro ao enviar a música.',true)}});
</script></body></html>
"""


def allowed_file(filename):
    return bool(filename) and "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def extract_hash(data):
    if not isinstance(data, dict):
        return None
    for key in ("hash", "job_hash", "id"):
        value = data.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    nested = data.get("data")
    if isinstance(nested, dict):
        return extract_hash(nested)
    return None


def extract_status(data):
    if not isinstance(data, dict):
        return "processing", None, []
    nested = data.get("data")
    if isinstance(nested, dict):
        merged = dict(data)
        merged.update(nested)
        data = merged
    status_text = str(data.get("status", data.get("state", "processing"))).lower()
    possible_files = data.get("files") or data.get("results") or data.get("output_files") or data.get("stems") or []
    if isinstance(possible_files, dict):
        possible_files = [{"name": key, "url": value} for key, value in possible_files.items()]
    files = []
    if isinstance(possible_files, list):
        for item in possible_files:
            if isinstance(item, str):
                files.append({"url": item})
            elif isinstance(item, dict):
                url = item.get("url") or item.get("download_url") or item.get("file_url") or item.get("link")
                if url:
                    files.append({"url": url, "name": item.get("name") or item.get("title") or ""})
    if not files:
        for key in ("result", "result_files", "output", "download_links"):
            value = data.get(key)
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, str):
                        files.append({"url": item})
                    elif isinstance(item, dict):
                        url = item.get("url") or item.get("download_url") or item.get("link")
                        if url:
                            files.append({"url": url, "name": item.get("name", "")})
    if files:
        return "done", data.get("message"), files
    if any(word in status_text for word in ("error", "fail", "failed")):
        return "error", data.get("message") or data.get("error"), []
    if any(word in status_text for word in ("done", "complete", "success", "finished")):
        return "done", data.get("message"), []
    return "processing", data.get("message"), []


@app.route("/", methods=["GET"])
def index():
    return render_template_string(HTML)


@app.route("/api/separar", methods=["POST"])
def separar():
    if not API_KEY:
        return jsonify(error="A chave da API não está configurada no servidor."), 500
    if "audiofile" not in request.files:
        return jsonify(error="Selecione um arquivo de áudio."), 400
    audio = request.files["audiofile"]
    if not audio.filename:
        return jsonify(error="O nome do arquivo está vazio."), 400
    if not allowed_file(audio.filename):
        return jsonify(error="Formato de áudio não permitido."), 400
    try:
        response = requests.post(
            f"{API_BASE}/separation/create",
            data={"api_token": API_KEY, "sep_type": "20", "output_format": "0"},
            files={"audiofile": (secure_filename(audio.filename), audio.stream, audio.mimetype or "application/octet-stream")},
            timeout=120,
        )
        response.raise_for_status()
        data = response.json()
        job_hash = extract_hash(data)
        if not job_hash:
            message = data.get("message") or data.get("error") or "O serviço não retornou o identificador do processamento." if isinstance(data, dict) else "Resposta inválida do serviço."
            app.logger.error("Resposta inesperada ao criar separação: %s", data)
            return jsonify(error=str(message)), 502
        return jsonify(hash=job_hash)
    except requests.RequestException:
        app.logger.exception("Erro ao enviar áudio para o serviço de separação.")
        return jsonify(error="Não foi possível conectar ao serviço de separação. Tente novamente."), 502
    except ValueError:
        return jsonify(error="O serviço retornou uma resposta inválida."), 502


@app.route("/api/status/<job_hash>", methods=["GET"])
def status(job_hash):
    if not job_hash or len(job_hash) > 200:
        return jsonify(error="Identificador inválido."), 400
    if not API_KEY:
        return jsonify(error="A chave da API não está configurada no servidor."), 500
    try:
        response = requests.get(f"{API_BASE}/separation/get", params={"hash": job_hash, "api_token": API_KEY}, timeout=30)
        response.raise_for_status()
        state, message, files = extract_status(response.json())
        return jsonify(status=state, message=message, files=files)
    except requests.RequestException:
        app.logger.exception("Erro ao consultar o status da separação.")
        return jsonify(error="Não foi possível consultar o processamento."), 502
    except ValueError:
        return jsonify(error="O serviço retornou uma resposta inválida."), 502


@app.route("/api/baixar", methods=["GET"])
def baixar():
    source_url = request.args.get("url", "")
    requested_name = request.args.get("name", "Audio - Faixa.mp3")
    parsed = urlparse(source_url)
    hostname = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or not (hostname == "mvsep.com" or hostname.endswith(".mvsep.com")) or parsed.username or parsed.password:
        return jsonify(error="Endereço de download inválido."), 400
    requested_name = unquote(requested_name).replace("\\", "/").split("/")[-1]
    requested_name = re.sub(r"[\r\n\x00-\x1f]", "", requested_name)
    requested_name = secure_filename(requested_name.replace(" ", "_")) or "Audio_-_Faixa.mp3"
    try:
        upstream = requests.get(source_url, stream=True, timeout=(15, 120), allow_redirects=False)
        if upstream.is_redirect:
            upstream.close()
            return jsonify(error="O serviço redirecionou o download. Tente novamente mais tarde."), 502
        if upstream.status_code != 200:
            upstream.close()
            return jsonify(error="Não foi possível baixar o arquivo neste momento."), 502
        content_type = upstream.headers.get("Content-Type", "application/octet-stream")
        content_length = upstream.headers.get("Content-Length")
        def stream_file():
            try:
                for chunk in upstream.iter_content(chunk_size=64 * 1024):
                    if chunk:
                        yield chunk
            finally:
                upstream.close()
        headers = {"Content-Disposition": f'attachment; filename="{requested_name}"', "X-Content-Type-Options": "nosniff", "Cache-Control": "no-store"}
        if content_length:
            headers["Content-Length"] = content_length
        return Response(stream_file(), content_type=content_type, headers=headers)
    except requests.RequestException:
        app.logger.exception("Erro ao preparar o download.")
        return jsonify(error="Falha ao preparar o download. Tente novamente."), 502


@app.errorhandler(413)
def file_too_large(_error):
    return jsonify(error="O arquivo ultrapassa o limite de 100 MB."), 413


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=False)
