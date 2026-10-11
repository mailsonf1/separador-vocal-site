import os
import re
import io
import tempfile
from urllib.parse import urlparse, unquote

import numpy as np
import requests
import soundfile as sf
from scipy.ndimage import median_filter
from scipy.signal import stft, istft
from pedalboard import Pedalboard, HighpassFilter, LowShelfFilter, HighShelfFilter, Compressor, Limiter, Gain
from pedalboard.io import AudioFile
from flask import Flask, request, jsonify, render_template_string, Response, send_file
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024

API_BASE = "https://mvsep.com/api"
API_KEY = os.environ.get("MVSEP_API_KEY", "")
INSTRUMENTAL_PRESET_ID = os.environ.get("MVSEP_INSTRUMENTAL_PRESET_ID", "").strip()
ALLOWED_EXTENSIONS = {"mp3", "wav", "flac", "m4a", "ogg", "aac", "aiff", "wma"}

HTML = r"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MFSTUDIO | Instrumental sem Vocal</title>
<style>
:root{--bg:#090916;--panel:#131329;--text:#f7f7ff;--muted:#aaaac8;--purple:#9b5cff;--pink:#ff3eaa;--cyan:#22e6ff;--lime:#b8ff4b;--orange:#ffad42}
*{box-sizing:border-box}body{margin:0;min-height:100vh;background:radial-gradient(ellipse at 8% 0%,#44208055,transparent 35%),radial-gradient(ellipse at 100% 20%,#005e7950,transparent 32%),var(--bg);color:var(--text);font-family:Inter,system-ui,-apple-system,"Segoe UI",sans-serif}
.container{width:min(960px,92%);margin:0 auto;padding:32px 0 60px}header{display:flex;align-items:center;justify-content:space-between;gap:16px;margin-bottom:48px}.brand{display:flex;align-items:center;gap:12px;font-weight:900;letter-spacing:1px;font-size:22px}.brand-mark{width:44px;height:44px;border-radius:14px;display:grid;place-items:center;font-size:23px;background:linear-gradient(135deg,var(--purple),var(--pink));box-shadow:0 0 30px #9b5cff55}.pill{border:1px solid #ffffff20;border-radius:999px;padding:8px 13px;color:var(--cyan);font-size:12px;font-weight:800;letter-spacing:1px}.hero{text-align:center;margin-bottom:32px}.eyebrow{color:var(--cyan);font-size:12px;font-weight:900;letter-spacing:3px;text-transform:uppercase}h1{font-size:clamp(36px,7vw,62px);line-height:1.05;margin:15px 0;letter-spacing:-2px}.gradient-text{background:linear-gradient(90deg,var(--cyan),#b38aff,var(--pink));-webkit-background-clip:text;background-clip:text;color:transparent}.subtitle{max-width:590px;margin:0 auto;color:var(--muted);line-height:1.7;font-size:15px}.panel{background:linear-gradient(145deg,#17172fef,#101020f5);border:1px solid #ffffff18;border-radius:26px;padding:clamp(18px,4vw,32px);box-shadow:0 24px 70px #00000040;margin-bottom:22px}.upload-area{border:2px dashed #8c63ff88;background:linear-gradient(135deg,#9b5cff0d,#22e6ff08);border-radius:20px;padding:36px 16px;text-align:center;transition:.2s ease}.upload-area.dragover{border-color:var(--cyan);background:#22e6ff12;transform:scale(1.01)}.upload-icon{width:68px;height:68px;margin:0 auto 15px;display:grid;place-items:center;font-size:32px;border-radius:22px;background:linear-gradient(135deg,#9b5cff30,#ff3eaa25)}.upload-area h2{font-size:20px;margin:8px 0}.upload-area p{color:var(--muted);font-size:13px}.file-name{display:none;margin-top:14px;color:var(--lime);font-size:13px;overflow-wrap:anywhere}input[type=file]{display:none}button,.choose-button{border:0;cursor:pointer;color:white;font-weight:800;font-size:13px;border-radius:13px;padding:12px 15px;transition:transform .15s,filter .15s}button:hover,.choose-button:hover{transform:translateY(-2px);filter:brightness(1.1)}button:disabled{opacity:.45;cursor:not-allowed;transform:none}.choose-button{display:inline-block;background:#282849;border:1px solid #ffffff20;margin-top:10px}.primary{width:100%;margin-top:20px;padding:17px;background:linear-gradient(90deg,#853dff,#ff3eaa);box-shadow:0 10px 28px #a23dff35;font-size:15px}.status{display:none;margin-top:20px;border-radius:14px;padding:14px 16px;background:#22e6ff0c;border:1px solid #22e6ff35;color:var(--cyan);font-size:13px;line-height:1.6;overflow-wrap:anywhere}.status.error{color:#ff819f;border-color:#ff3eaa66;background:#ff3eaa0c}.progress-track{display:none;height:7px;border-radius:99px;background:#ffffff12;margin-top:13px;overflow:hidden}.progress-bar{height:100%;width:35%;border-radius:99px;background:linear-gradient(90deg,var(--cyan),var(--purple),var(--pink));animation:progress 1.5s ease-in-out infinite alternate}@keyframes progress{from{transform:translateX(-15%)}to{transform:translateX(190%)}}.section-title{display:flex;justify-content:space-between;align-items:center;gap:12px;margin-bottom:20px}.section-title h2{margin:0;font-size:21px}.section-title span{color:var(--muted);font-size:12px}.results{display:none}.track-list{display:grid;gap:12px}.track{--accent:var(--purple);border:1px solid #ffffff15;background:#ffffff06;border-radius:17px;padding:15px;min-width:0}.track-top{display:flex;align-items:center;gap:14px;min-width:0}.track-icon{flex:0 0 48px;height:48px;border-radius:15px;display:grid;place-items:center;font-size:25px;background:#ffffff10;border:1px solid #ffffff20}.track-info{flex:1;min-width:0}.track-info strong{display:block;font-size:14px;overflow-wrap:anywhere}.track-info small{display:block;color:var(--muted);font-size:12px;margin-top:5px}.track-actions{display:flex;flex-wrap:wrap;gap:8px;justify-content:flex-end}.download{background:var(--accent);color:#090916}.master-btn{background:#292344;border:1px solid #9b5cff66}.track:nth-child(1){--accent:var(--orange)}.track:nth-child(2){--accent:var(--cyan)}.track:nth-child(3){--accent:var(--lime)}.track:nth-child(4){--accent:var(--pink)}.track:nth-child(5){--accent:var(--purple)}.master-panel{display:none;margin-top:16px;padding:16px;border:1px solid #9b5cff44;border-radius:15px;background:#0b0b1b}.master-panel h3{margin:0 0 5px;font-size:16px}.master-help{font-size:12px;color:var(--muted);line-height:1.5;margin:0 0 15px}.controls{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}.control label{display:flex;justify-content:space-between;gap:10px;font-size:12px;color:#e8e6ff;margin-bottom:7px}.control output{color:var(--cyan);font-variant-numeric:tabular-nums}.control input[type=range]{width:100%;accent-color:var(--purple)}.master-actions{display:flex;gap:8px;flex-wrap:wrap;margin-top:15px}.process-btn{background:linear-gradient(90deg,#853dff,#ff3eaa)}.secondary{background:#282849;border:1px solid #ffffff20}.preview{width:100%;height:38px;margin-top:12px;display:none}.track-preview{display:block;width:100%;height:40px;margin-top:14px;border-radius:12px}.preview-note{font-size:11px;color:var(--muted);margin:7px 0 0}footer{text-align:center;color:#777797;font-size:12px;padding-top:15px}.fineprint{color:#8585a8;font-size:11px;line-height:1.5;margin-top:10px}@media(max-width:560px){header{margin-bottom:35px}.pill{display:none}.track-top{align-items:flex-start;gap:10px}.track-icon{flex-basis:42px;height:42px;font-size:22px}.track-actions{width:100%;justify-content:flex-start;margin-top:12px}.track-actions button{flex:1}.track-info strong{font-size:13px}.controls{grid-template-columns:1fr}}
</style>
</head>
<body><div class="container">
<header><div class="brand"><div class="brand-mark">♫</div><span>MF<span class="gradient-text">STUDIO</span></span></div><div class="pill">AUDIO LAB · ONLINE</div></header>
<section class="hero"><div class="eyebrow">Seu som. Do seu jeito.</div><h1>Instrumental<br><span class="gradient-text">sem vocal.</span></h1><p class="subtitle">Envie sua música, gere uma versão instrumental com inteligência artificial e ouça uma prévia gratuita de até 20 segundos antes de baixar.</p></section>
<section class="panel"><form id="uploadForm"><div class="upload-area" id="dropArea"><div class="upload-icon">🎧</div><h2>Escolha sua música</h2><p>Arraste o arquivo para cá ou selecione no seu dispositivo.</p><label class="choose-button" for="audioFile">📂 Selecionar arquivo</label><input id="audioFile" name="audiofile" type="file" accept=".mp3,.wav,.flac,.m4a,.ogg,.aac,.aiff,.wma" required><div class="file-name" id="fileName"></div></div><button class="primary" id="submitButton" type="submit">✨ Separar minha música</button></form><div class="status" id="status"></div><div class="progress-track" id="progressTrack"><div class="progress-bar"></div></div></section>
<section class="panel results" id="results"><div class="section-title"><h2>🎵 Suas faixas</h2><span id="trackCount"></span></div><div class="track-list" id="trackList"></div><div style="margin-top:18px"><button class="secondary" id="instrumentalButton" type="button">🎼 Gerar instrumental corrigida por fase</button><p class="fineprint">Usa o preset Phase-corrected salvo na sua conta MVSEP. A integração precisa do ID desse preset configurado no servidor.</p></div></section>
<footer>MFSTUDIO · Ferramentas para quem ama música<div class="fineprint">A masterização automática é processada no servidor. Ela reduz alguns artefatos e ajusta dinâmica e nível; o resultado depende da qualidade da faixa original e não garante reconstrução perfeita do áudio perdido.</div></footer></div>
<script>
const form=document.getElementById('uploadForm'),audioFile=document.getElementById('audioFile'),fileName=document.getElementById('fileName'),dropArea=document.getElementById('dropArea'),statusBox=document.getElementById('status'),submitButton=document.getElementById('submitButton'),progressTrack=document.getElementById('progressTrack'),results=document.getElementById('results'),trackList=document.getElementById('trackList'),trackCount=document.getElementById('trackCount'),instrumentalButton=document.getElementById('instrumentalButton');
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
function addMasterPanel(row,url,downloadName,trackTitle){
 const panel=document.createElement('div');panel.className='master-panel';
 const heading=document.createElement('h3');heading.textContent='✨ Masterização automática: '+trackTitle;
 const help=document.createElement('p');help.className='master-help';help.textContent='Um clique para reduzir parte dos artefatos metálicos/robóticos e ajustar automaticamente a dinâmica e o volume. O arquivo original permanece intacto. Compare o original com o resultado antes de decidir qual baixar.';
 const actions=document.createElement('div');actions.className='master-actions';
 const process=document.createElement('button');process.className='process-btn';process.textContent='✨ Masterizar automaticamente';
 const originalBtn=document.createElement('button');originalBtn.className='secondary';originalBtn.textContent='▶ Ouvir original';
 const originalAudio=document.createElement('audio');originalAudio.className='preview';originalAudio.controls=true;
 const resultLabel=document.createElement('p');resultLabel.className='master-help';resultLabel.textContent='Resultado masterizado';resultLabel.style.display='none';
 const processedAudio=document.createElement('audio');processedAudio.className='preview';processedAudio.controls=true;
 const download=document.createElement('button');download.className='download';download.textContent='⬇ Baixar masterizada';download.style.display='none';
 actions.append(process,originalBtn,download);panel.append(heading,help,actions,originalAudio,resultLabel,processedAudio);row.append(panel);
 let originalBlobUrl=null,processedBlobUrl=null;
 originalBtn.addEventListener('click',async()=>{try{originalBtn.disabled=true;originalBtn.textContent='⏳ Carregando original...';const r=await fetch(downloadUrl(url,downloadName));if(!r.ok)throw new Error('Não foi possível carregar a faixa original.');const blob=await r.blob();if(originalBlobUrl)URL.revokeObjectURL(originalBlobUrl);originalBlobUrl=URL.createObjectURL(blob);originalAudio.src=originalBlobUrl;originalAudio.style.display='block';await originalAudio.play();}catch(err){setStatus(err.message||'Falha ao abrir o original.',true)}finally{originalBtn.disabled=false;originalBtn.textContent='▶ Ouvir original'}});
 process.addEventListener('click',async()=>{process.disabled=true;process.textContent='⏳ Analisando e masterizando no servidor...';setStatus('A masterização automática de '+trackTitle+' começou. Aguarde enquanto o servidor processa o áudio...');try{const r=await fetch('/api/masterizar',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({url,name:downloadName})});if(!r.ok){let message='Não foi possível masterizar esta faixa.';try{const j=await r.json();message=j.error||message}catch{}throw new Error(message)}const blob=await r.blob();if(processedBlobUrl)URL.revokeObjectURL(processedBlobUrl);processedBlobUrl=URL.createObjectURL(blob);processedAudio.src=processedBlobUrl;processedAudio.style.display='block';resultLabel.style.display='block';download.style.display='inline-block';download.onclick=()=>{const a=document.createElement('a');a.href=processedBlobUrl;a.download=downloadName.replace(/\.[^.]+$/,'')+' - Masterizada.wav';document.body.append(a);a.click();a.remove()};setStatus('✅ Masterização concluída para '+trackTitle+'. Ouça o original e o resultado para comparar; a faixa original continua disponível.');panel.scrollIntoView({behavior:'smooth',block:'nearest'});}catch(err){setStatus(err.message||'Não foi possível concluir a masterização.',true)}finally{process.disabled=false;process.textContent='✨ Masterizar automaticamente'}});
 return panel
}
function renderTracks(files,append=false){if(!append)trackList.innerHTML='';results.style.display='block';const valid=files.filter(f=>f&&(f.url||f.download_url||f.file));valid.forEach(file=>{const url=file.url||file.download_url||file.file,info=getTrackInfo(url,file.name||file.title||''),ext=getExtension(url),base=safeFilenamePart(originalBaseName),name=base+' - '+info.label+'.'+ext,row=document.createElement('div');row.className='track';const top=document.createElement('div');top.className='track-top';const icon=document.createElement('div');icon.className='track-icon';icon.textContent=info.emoji;const details=document.createElement('div');details.className='track-info';const title=document.createElement('strong');title.textContent=info.emoji+' '+base+' - '+info.label;const subtitle=document.createElement('small');subtitle.textContent='Arquivo .'+ext.toUpperCase()+' · Pronto para baixar';details.append(title,subtitle);const actions=document.createElement('div');actions.className='track-actions';const dl=document.createElement('button');dl.className='download';dl.type='button';dl.textContent='⬇ Baixar original';dl.addEventListener('click',()=>location.href=downloadUrl(url,name));const master=document.createElement('button');master.className='master-btn';master.type='button';master.textContent='🎚️ Masterizar';actions.append(dl,master);top.append(icon,details,actions);row.append(top);const previewLabel=document.createElement('p');previewLabel.className='preview-note';previewLabel.textContent='▶ Prévia gratuita de até 20 segundos';const preview=document.createElement('audio');preview.className='track-preview';preview.controls=true;preview.preload='metadata';preview.src=url;preview.addEventListener('play',()=>{if(preview.currentTime>=20)preview.currentTime=0});preview.addEventListener('timeupdate',()=>{if(preview.currentTime>=20){preview.pause();preview.currentTime=20}});preview.addEventListener('seeking',()=>{if(preview.currentTime>20)preview.currentTime=20});row.append(previewLabel,preview);const panel=addMasterPanel(row,url,name,info.label);master.addEventListener('click',()=>{const open=panel.style.display==='block';panel.style.display=open?'none':'block';master.textContent=open?'🎚️ Masterizar':'✕ Fechar masterização'});trackList.append(row)});const total=trackList.querySelectorAll('.track').length;trackCount.textContent=total+(total===1?' faixa':' faixas');if(!valid.length)setStatus('O processamento terminou, mas não encontrei links de download válidos.',true);else{setStatus(append?'✅ Instrumental corrigida adicionada às faixas!':'✅ Música separada com sucesso! Baixe as faixas ou abra Masterizar para ajustar cada uma.');results.scrollIntoView({behavior:'smooth',block:'start'})}}
async function checkStatus(hash,appendResults=false){try{const r=await fetch('/api/status/'+encodeURIComponent(hash)),data=await r.json();if(!r.ok||data.error)throw new Error(data.error||'Não foi possível consultar o processamento.');if(data.status==='done'){clearInterval(pollingTimer);pollingTimer=null;submitButton.disabled=false;submitButton.textContent='✨ Separar outra música';progressTrack.style.display='none';renderTracks(data.files||[],appendResults);if(appendResults){instrumentalButton.disabled=false;instrumentalButton.textContent='🎼 Gerar instrumental corrigida por fase'}}else if(data.status==='error'){clearInterval(pollingTimer);pollingTimer=null;submitButton.disabled=false;submitButton.textContent='✨ Tentar novamente';progressTrack.style.display='none';setStatus(data.message||'O processamento falhou. Tente novamente.',true);if(appendResults){instrumentalButton.disabled=false;instrumentalButton.textContent='🎼 Tentar instrumental novamente'}}else setStatus(data.message||'Estamos separando sua música. Isso pode levar alguns minutos.')}catch(err){clearInterval(pollingTimer);pollingTimer=null;submitButton.disabled=false;submitButton.textContent='✨ Tentar novamente';progressTrack.style.display='none';setStatus(err.message||'Erro ao consultar o processamento.',true);if(appendResults){instrumentalButton.disabled=false;instrumentalButton.textContent='🎼 Tentar instrumental novamente'}}}
instrumentalButton.addEventListener('click',async()=>{const file=audioFile.files[0];if(!file){setStatus('Selecione novamente o arquivo original para gerar a instrumental corrigida.',true);return}if(pollingTimer){clearInterval(pollingTimer);pollingTimer=null}instrumentalButton.disabled=true;instrumentalButton.textContent='⏳ Enviando para correção de fase...';progressTrack.style.display='block';setStatus('Enviando o áudio ao preset Phase-corrected da MVSEP. Aguarde...');try{const fd=new FormData();fd.append('audiofile',file);const r=await fetch('/api/instrumental',{method:'POST',body:fd});const data=await r.json();if(!r.ok||data.error)throw new Error(data.error||'Não foi possível iniciar a instrumental corrigida.');const hash=data.hash||data.job_hash||data.id;if(!hash)throw new Error('A MVSEP não retornou o identificador do processamento.');instrumentalButton.textContent='🎼 Processando instrumental...';setStatus('Preset recebido! A MVSEP está gerando a instrumental corrigida.');pollingTimer=setInterval(()=>checkStatus(hash,true),4000);await checkStatus(hash,true)}catch(err){instrumentalButton.disabled=false;instrumentalButton.textContent='🎼 Tentar instrumental novamente';progressTrack.style.display='none';setStatus(err.message||'Falha ao iniciar a instrumental corrigida.',true)}});
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
                    files.append({"url": url, "name": item.get("name") or item.get("title") or item.get("label") or ""})
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
                            files.append({"url": url, "name": item.get("name") or item.get("label") or ""})
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


@app.route("/api/instrumental", methods=["POST"])
def gerar_instrumental_corrigida():
    """Executa um preset Phase-corrected salvo na conta MVSEP do proprietário."""
    if not API_KEY:
        return jsonify(error="A chave da API da MVSEP não está configurada no servidor."), 500
    if not INSTRUMENTAL_PRESET_ID:
        return jsonify(error="Falta configurar MVSEP_INSTRUMENTAL_PRESET_ID no Render. Salve o fluxo Phase-corrected como preset na MVSEP e configure o ID dele nas variáveis de ambiente."), 503
    if "audiofile" not in request.files:
        return jsonify(error="Selecione o arquivo de áudio original."), 400
    audio = request.files["audiofile"]
    if not audio.filename or not allowed_file(audio.filename):
        return jsonify(error="Envie um arquivo de áudio válido."), 400
    try:
        response = requests.post(
            f"{API_BASE}/separation/create",
            data={"api_token": API_KEY, "preset_id": INSTRUMENTAL_PRESET_ID},
            files={"audiofile": (secure_filename(audio.filename), audio.stream, audio.mimetype or "application/octet-stream")},
            timeout=120,
        )
        response.raise_for_status()
        data = response.json()
        job_hash = extract_hash(data)
        if not job_hash:
            nested = data.get("data", {}) if isinstance(data, dict) else {}
            message = (nested.get("message") or data.get("message") or data.get("error") or "A MVSEP não retornou o identificador do preset.") if isinstance(nested, dict) and isinstance(data, dict) else "Resposta inválida da MVSEP."
            app.logger.error("Resposta inesperada ao criar preset instrumental: %s", data)
            return jsonify(error=str(message)), 502
        return jsonify(hash=job_hash)
    except requests.RequestException:
        app.logger.exception("Erro ao enviar áudio para o preset instrumental MVSEP.")
        return jsonify(error="Não foi possível conectar à MVSEP para gerar a instrumental corrigida."), 502
    except ValueError:
        return jsonify(error="A MVSEP retornou uma resposta inválida."), 502



def _validated_mvsep_url(source_url):
    parsed = urlparse(source_url or "")
    hostname = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or not (hostname == "mvsep.com" or hostname.endswith(".mvsep.com")) or parsed.username or parsed.password:
        raise ValueError("Endereço de áudio inválido.")
    return source_url


def _reduce_spectral_spikes(audio, strength=0.28, sample_rate=44100):
    """Redução conservadora de picos espectrais estreitos; não é restauração neural."""
    output = np.asarray(audio, dtype=np.float32).copy()
    longest = output.shape[1]
    desired = 2048 if sample_rate >= 32000 else 1024
    n_fft = min(desired, max(256, 2 ** int(np.floor(np.log2(max(256, longest))))))
    hop = n_fft // 4
    for channel in range(output.shape[0]):
        _, times, spectrum = stft(output[channel], fs=sample_rate, nperseg=n_fft,
                                  noverlap=n_fft-hop, boundary="zeros", padded=True)
        magnitude = np.abs(spectrum)
        local = median_filter(magnitude, size=(5, 1), mode="nearest")
        ratio = magnitude / (local + 1e-7)
        # Attenua apenas picos muito mais fortes que a vizinhança, de forma moderada.
        excess = np.clip((ratio - 2.8) / 5.0, 0.0, 0.55)
        mask = 1.0 - (strength * excess)
        cleaned_spectrum = spectrum * mask
        _, reconstructed = istft(cleaned_spectrum, fs=sample_rate, nperseg=n_fft,
                                 noverlap=n_fft-hop, input_onesided=True,
                                 boundary=True)
        if len(reconstructed) < output.shape[1]:
            reconstructed = np.pad(reconstructed, (0, output.shape[1]-len(reconstructed)))
        output[channel] = reconstructed[:output.shape[1]].astype(np.float32)
    return output


@app.route("/api/masterizar", methods=["POST"])
def masterizar():
    payload = request.get_json(silent=True) or {}
    try:
        source_url = _validated_mvsep_url(payload.get("url", ""))
    except ValueError as exc:
        return jsonify(error=str(exc)), 400

    requested_name = str(payload.get("name") or "Audio - Faixa.wav")
    requested_name = re.sub(r"[\\/\r\n\x00-\x1f]", "_", requested_name)[:180]
    parsed = urlparse(source_url)
    suffix = os.path.splitext(parsed.path)[1].lower()
    if suffix not in {".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac", ".aiff", ".wma"}:
        suffix = ".audio"

    try:
        with requests.get(source_url, stream=True, timeout=(15, 120), allow_redirects=False) as upstream:
            if upstream.is_redirect:
                return jsonify(error="O serviço de áudio redirecionou o download. Tente novamente."), 502
            if upstream.status_code != 200:
                return jsonify(error="Não foi possível obter a faixa para masterização."), 502
            chunks = []
            total = 0
            for chunk in upstream.iter_content(chunk_size=1024 * 256):
                if not chunk:
                    continue
                total += len(chunk)
                if total > 100 * 1024 * 1024:
                    return jsonify(error="Esta faixa ultrapassa o limite de 100 MB para masterização."), 413
                chunks.append(chunk)
        raw_audio = b"".join(chunks)
        with tempfile.TemporaryDirectory(prefix="mfstudio_") as temp_dir:
            input_path = os.path.join(temp_dir, "input" + suffix)
            output_path = os.path.join(temp_dir, "masterizada.wav")
            with open(input_path, "wb") as audio_file:
                audio_file.write(raw_audio)
            try:
                with AudioFile(input_path) as audio_file:
                    sample_rate = int(audio_file.samplerate)
                    frames = int(audio_file.frames)
                    channels = int(audio_file.num_channels)
                    if sample_rate < 8000 or sample_rate > 192000 or channels < 1 or channels > 2:
                        return jsonify(error="Formato de áudio não suportado para masterização."), 415
                    if frames / sample_rate > 600:
                        return jsonify(error="Para manter o serviço estável, a masterização automática está limitada a 10 minutos por faixa."), 413
                    audio = audio_file.read(frames).astype(np.float32)
            except Exception as exc:
                app.logger.info("Não foi possível decodificar a faixa: %s", exc)
                return jsonify(error="Não foi possível decodificar este formato de áudio. Tente baixar a faixa original em MP3 ou WAV e verificar se o arquivo está íntegro."), 415

            if audio.ndim == 1:
                audio = audio.reshape(1, -1)
            if audio.shape[0] != channels and audio.shape[1] == channels:
                audio = audio.T
            if audio.size == 0:
                return jsonify(error="A faixa de áudio está vazia."), 400

            # Limpeza conservadora, EQ suave, compressão leve e limitação de picos.
            cleaned = _reduce_spectral_spikes(audio, strength=0.30, sample_rate=sample_rate)
            board = Pedalboard([
                HighpassFilter(cutoff_frequency_hz=28.0),
                LowShelfFilter(cutoff_frequency_hz=120.0, gain_db=0.8),
                HighShelfFilter(cutoff_frequency_hz=min(10000.0, sample_rate * 0.42), gain_db=0.4),
                Compressor(threshold_db=-18.0, ratio=2.0, attack_ms=10.0, release_ms=120.0),
                Limiter(threshold_db=-1.0, release_ms=100.0),
            ])
            processed = board(cleaned, sample_rate)
            peak = float(np.max(np.abs(processed))) if processed.size else 0.0
            if peak > 1e-8:
                # Alvo de pico conservador, sem aumentar áudio silencioso de forma agressiva.
                target_peak = 10 ** (-1.0 / 20.0)
                gain = min(target_peak / peak, 10 ** (6.0 / 20.0))
                processed = processed * gain
            processed = np.clip(processed, -0.999, 0.999).astype(np.float32)
            with AudioFile(output_path, "w", sample_rate, processed.shape[0]) as out_file:
                out_file.write(processed)
            with open(output_path, "rb") as result_file:
                result_bytes = result_file.read()
            return send_file(io.BytesIO(result_bytes), mimetype="audio/wav", as_attachment=True,
                             download_name=(os.path.splitext(secure_filename(requested_name))[0] or "Audio") + " - Masterizada.wav",
                             max_age=0)
    except requests.RequestException:
        app.logger.exception("Falha ao obter faixa para masterização.")
        return jsonify(error="Não foi possível obter a faixa do serviço de separação. Tente novamente."), 502
    except Exception:
        app.logger.exception("Erro inesperado durante a masterização automática.")
        return jsonify(error="Ocorreu um erro durante a masterização automática. Tente novamente com uma faixa menor."), 500


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
