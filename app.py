import os
import re
import io
from urllib.parse import urlparse, unquote

import requests
import soundfile as sf
from flask import Flask, request, jsonify, render_template_string, Response, send_file
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
<section class="panel results" id="results"><div class="section-title"><h2>🎼 Sua instrumental</h2><span id="trackCount"></span></div><div class="track-list" id="trackList"></div></section>
<footer>MFSTUDIO · Sua música, sem vocal</footer></div>
<script>
const form=document.getElementById('uploadForm'),audioFile=document.getElementById('audioFile'),fileName=document.getElementById('fileName'),dropArea=document.getElementById('dropArea'),statusBox=document.getElementById('status'),submitButton=document.getElementById('submitButton'),progressTrack=document.getElementById('progressTrack'),results=document.getElementById('results'),trackList=document.getElementById('trackList'),trackCount=document.getElementById('trackCount');
let originalBaseName='Audio',pollingTimer=null;
audioFile.addEventListener('change',()=>showSelectedFile(audioFile.files[0]));
function showSelectedFile(file){if(!file)return;fileName.textContent='✓ '+file.name;fileName.style.display='block';originalBaseName=file.name.replace(/\.[^.]+$/,'').trim()||'Audio'}
['dragenter','dragover'].forEach(n=>dropArea.addEventListener(n,e=>{e.preventDefault();dropArea.classList.add('dragover')}));['dragleave','drop'].forEach(n=>dropArea.addEventListener(n,e=>{e.preventDefault();dropArea.classList.remove('dragover')}));
dropArea.addEventListener('drop',e=>{const files=e.dataTransfer.files;if(!files.length)return;const f=files[0];const dt=new DataTransfer();dt.items.add(f);audioFile.files=dt.files;showSelectedFile(f)});
function setStatus(message,isError=false){statusBox.textContent=message;statusBox.style.display='block';statusBox.classList.toggle('error',isError)}
function safeFilenamePart(n){return n.replace(/[<>:"/\\|?*\x00-\x1F]/g,'_').replace(/\s+/g,' ').trim().replace(/[. ]+$/,'')||'Audio'}
function renderInstrumental(file){trackList.innerHTML='';results.style.display='block';if(!file||!(file.url||file.download_url||file.file)){setStatus('A separação terminou, mas a MVSEP não retornou uma instrumental identificável. Nenhuma outra faixa será exibida.',true);return}const url=file.url||file.download_url||file.file;let ext='mp3';try{const path=new URL(url,location.origin).pathname,m=path.match(/\.([a-z0-9]{2,5})$/i);if(m)ext=m[1].toLowerCase()}catch{}const name=safeFilenamePart(originalBaseName)+' - Instrumental.'+ext;const row=document.createElement('div');row.className='track';const top=document.createElement('div');top.className='track-top';const icon=document.createElement('div');icon.className='track-icon';icon.textContent='🎼';const details=document.createElement('div');details.className='track-info';const title=document.createElement('strong');title.textContent=safeFilenamePart(originalBaseName)+' - Instrumental';const subtitle=document.createElement('small');subtitle.textContent='Arquivo .'+ext.toUpperCase()+' · Instrumental sem vocal';details.append(title,subtitle);const actions=document.createElement('div');actions.className='track-actions';const dl=document.createElement('button');dl.className='download';dl.type='button';dl.textContent='⬇ Baixar instrumental';dl.addEventListener('click',()=>{location.href='/api/baixar?url='+encodeURIComponent(url)+'&name='+encodeURIComponent(name)});actions.append(dl);top.append(icon,details,actions);row.append(top);const label=document.createElement('p');label.className='preview-note';label.textContent='▶ Prévia gratuita limitada a 20 segundos';const preview=document.createElement('audio');preview.className='track-preview';preview.controls=true;preview.preload='none';preview.src='/api/preview?url='+encodeURIComponent(url);row.append(label,preview);trackList.append(row);trackCount.textContent='1 instrumental';setStatus('✅ Instrumental pronta! Você pode ouvir a prévia e baixar a faixa completa.');results.scrollIntoView({behavior:'smooth',block:'start'})}
async function checkStatus(hash){try{const r=await fetch('/api/status/'+encodeURIComponent(hash)),data=await r.json();if(!r.ok||data.error)throw new Error(data.error||'Não foi possível consultar o processamento.');if(data.status==='done'){clearInterval(pollingTimer);pollingTimer=null;submitButton.disabled=false;submitButton.textContent='✨ Separar outra música';progressTrack.style.display='none';if(data.files&&data.files.length===1){renderInstrumental(data.files[0])}else{results.style.display='block';trackList.innerHTML='';setStatus(data.message||'O processamento terminou, mas não foi possível identificar com segurança o arquivo instrumental. Verifique o formato de saída da MVSEP.',true)}}else if(data.status==='error'){clearInterval(pollingTimer);pollingTimer=null;submitButton.disabled=false;submitButton.textContent='✨ Tentar novamente';progressTrack.style.display='none';setStatus(data.message||'O processamento falhou. Tente novamente.',true)}else setStatus(data.message||'Estamos separando sua música. Isso pode levar alguns minutos.')}catch(err){clearInterval(pollingTimer);pollingTimer=null;submitButton.disabled=false;submitButton.textContent='✨ Tentar novamente';progressTrack.style.display='none';setStatus(err.message||'Erro ao consultar o processamento.',true)}}
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


def select_instrumental(files):
    """Return only a confidently labelled instrumental/accompaniment result."""
    matches = []
    for item in files or []:
        if not isinstance(item, dict):
            continue
        url = str(item.get("url") or item.get("download_url") or item.get("file") or "")
        name = str(item.get("name") or item.get("title") or item.get("label") or "")
        label = (name + " " + urlparse(url).path).lower().replace("%20", " ")
        label = label.replace("_", " ").replace("-", " ")
        if any(word in label for word in ("instrumental", "no vocals", "no vocal", "accompaniment", "instrumental track")):
            if not any(word in label for word in ("vocals only", "vocal only", "isolated vocal", "voice only")):
                matches.append(item)
    # Ambiguous output names must not expose vocals or other stems.
    return matches if len(matches) == 1 else []


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
        if state == "done":
            instrumental = select_instrumental(files)
            if not instrumental:
                return jsonify(status="error", message="A MVSEP terminou, mas o nome do arquivo instrumental não pôde ser identificado com segurança. Nenhuma faixa foi liberada. Confira os nomes de saída da MVSEP."), 502
            files = instrumental
        return jsonify(status=state, message=message, files=files)
    except requests.RequestException:
        app.logger.exception("Erro ao consultar o status da separação.")
        return jsonify(error="Não foi possível consultar o processamento."), 502
    except ValueError:
        return jsonify(error="O serviço retornou uma resposta inválida."), 502


@app.route("/api/preview", methods=["GET"])
def preview():
    """Stream only the first 20 seconds, re-encoded as WAV on the server."""
    source_url = request.args.get("url", "")
    parsed = urlparse(source_url)
    hostname = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or not (hostname == "mvsep.com" or hostname.endswith(".mvsep.com")) or parsed.username or parsed.password:
        return jsonify(error="Endereço de prévia inválido."), 400
    try:
        with requests.get(source_url, stream=True, timeout=(15, 90), allow_redirects=False) as upstream:
            if upstream.is_redirect or upstream.status_code != 200:
                return jsonify(error="Não foi possível carregar a prévia. Tente novamente."), 502
            chunks, total = [], 0
            for chunk in upstream.iter_content(chunk_size=256 * 1024):
                if not chunk:
                    continue
                total += len(chunk)
                if total > 100 * 1024 * 1024:
                    return jsonify(error="O arquivo ultrapassa o limite para gerar a prévia."), 413
                chunks.append(chunk)
        raw = b"".join(chunks)
        try:
            audio, sample_rate = sf.read(io.BytesIO(raw), dtype="float32", always_2d=True)
        except Exception:
            app.logger.exception("Formato não suportado ao gerar prévia de áudio.")
            return jsonify(error="Não foi possível gerar a prévia deste formato de áudio. Tente uma saída MP3, WAV ou FLAC na MVSEP."), 415
        if sample_rate < 8000 or sample_rate > 192000 or audio.size == 0:
            return jsonify(error="O arquivo de áudio não é válido para prévia."), 415
        audio = audio[:int(sample_rate * 20)]
        output = io.BytesIO()
        sf.write(output, audio, sample_rate, format="WAV", subtype="PCM_16")
        output.seek(0)
        return send_file(output, mimetype="audio/wav", as_attachment=False, download_name="mfstudio-preview.wav", max_age=0)
    except requests.RequestException:
        app.logger.exception("Falha ao buscar áudio para prévia.")
        return jsonify(error="Não foi possível obter o áudio para a prévia."), 502


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
