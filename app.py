
import os
import re
import time
from urllib.parse import urlparse, unquote

import requests
from flask import Flask, request, jsonify, render_template_string, Response
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024

API_BASE = "https://mvsep.com/api"
API_KEY = os.environ.get("MVSEP_API_KEY", "")

ALLOWED_EXTENSIONS = {
    "mp3", "wav", "flac", "m4a", "ogg", "aac", "aiff", "wma"
}

HTML = r"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MFSTUDIO | Separador de Áudio</title>
<style>
:root {
    --bg: #090916;
    --panel: #131329;
    --panel2: #1a1a35;
    --text: #f7f7ff;
    --muted: #aaaac8;
    --purple: #9b5cff;
    --pink: #ff3eaa;
    --cyan: #22e6ff;
    --lime: #b8ff4b;
    --orange: #ffad42;
}
* { box-sizing: border-box; }
body {
    margin: 0;
    min-height: 100vh;
    background:
        radial-gradient(ellipse at 8% 0%, #44208055, transparent 35%),
        radial-gradient(ellipse at 100% 20%, #005e7950, transparent 32%),
        var(--bg);
    color: var(--text);
    font-family: Inter, system-ui, -apple-system, "Segoe UI", sans-serif;
}
.container {
    width: min(960px, 92%);
    margin: 0 auto;
    padding: 32px 0 60px;
}
header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    margin-bottom: 48px;
}
.brand {
    display: flex;
    align-items: center;
    gap: 12px;
    font-weight: 900;
    letter-spacing: 1px;
    font-size: 22px;
}
.brand-mark {
    width: 44px;
    height: 44px;
    border-radius: 14px;
    display: grid;
    place-items: center;
    font-size: 23px;
    background: linear-gradient(135deg, var(--purple), var(--pink));
    box-shadow: 0 0 30px #9b5cff55;
}
.pill {
    border: 1px solid #ffffff20;
    border-radius: 999px;
    padding: 8px 13px;
    color: var(--cyan);
    font-size: 12px;
    font-weight: 800;
    letter-spacing: 1px;
}
.hero { text-align: center; margin-bottom: 32px; }
.eyebrow {
    color: var(--cyan);
    font-size: 12px;
    font-weight: 900;
    letter-spacing: 3px;
    text-transform: uppercase;
}
h1 {
    font-size: clamp(36px, 7vw, 62px);
    line-height: 1.05;
    margin: 15px 0;
    letter-spacing: -2px;
}
.gradient-text {
    background: linear-gradient(90deg, var(--cyan), #b38aff, var(--pink));
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
}
.subtitle {
    max-width: 590px;
    margin: 0 auto;
    color: var(--muted);
    line-height: 1.7;
    font-size: 15px;
}
.panel {
    background: linear-gradient(145deg, #17172fef, #101020f5);
    border: 1px solid #ffffff18;
    border-radius: 26px;
    padding: clamp(18px, 4vw, 32px);
    box-shadow: 0 24px 70px #00000040;
    margin-bottom: 22px;
}
.upload-area {
    border: 2px dashed #8c63ff88;
    background: linear-gradient(135deg, #9b5cff0d, #22e6ff08);
    border-radius: 20px;
    padding: 36px 16px;
    text-align: center;
    transition: .2s ease;
}
.upload-area.dragover {
    border-color: var(--cyan);
    background: #22e6ff12;
    transform: scale(1.01);
}
.upload-icon {
    width: 68px;
    height: 68px;
    margin: 0 auto 15px;
    display: grid;
    place-items: center;
    font-size: 32px;
    border-radius: 22px;
    background: linear-gradient(135deg, #9b5cff30, #ff3eaa25);
}
.upload-area h2 { font-size: 20px; margin: 8px 0; }
.upload-area p { color: var(--muted); font-size: 13px; }
.file-name {
    display: none;
    margin-top: 14px;
    color: var(--lime);
    font-size: 13px;
    overflow-wrap: anywhere;
}
input[type=file] { display: none; }
button, .choose-button {
    border: 0;
    cursor: pointer;
    color: white;
    font-weight: 800;
    font-size: 14px;
    border-radius: 13px;
    padding: 14px 20px;
    transition: transform .15s, filter .15s;
}
button:hover, .choose-button:hover { transform: translateY(-2px); filter: brightness(1.1); }
button:disabled { opacity: .45; cursor: not-allowed; transform: none; }
.choose-button {
    display: inline-block;
    background: #282849;
    border: 1px solid #ffffff20;
    margin-top: 10px;
}
.primary {
    width: 100%;
    margin-top: 20px;
    padding: 17px;
    background: linear-gradient(90deg, #853dff, #ff3eaa);
    box-shadow: 0 10px 28px #a23dff35;
    font-size: 15px;
}
.status {
    display: none;
    margin-top: 20px;
    border-radius: 14px;
    padding: 14px 16px;
    background: #22e6ff0c;
    border: 1px solid #22e6ff35;
    color: var(--cyan);
    font-size: 13px;
    line-height: 1.6;
    overflow-wrap: anywhere;
}
.status.error {
    color: #ff819f;
    border-color: #ff3eaa66;
    background: #ff3eaa0c;
}
.progress-track {
    display: none;
    height: 7px;
    border-radius: 99px;
    background: #ffffff12;
    margin-top: 13px;
    overflow: hidden;
}
.progress-bar {
    height: 100%;
    width: 35%;
    border-radius: 99px;
    background: linear-gradient(90deg, var(--cyan), var(--purple), var(--pink));
    animation: progress 1.5s ease-in-out infinite alternate;
}
@keyframes progress {
    from { transform: translateX(-15%); }
    to { transform: translateX(190%); }
}
.section-title {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
    margin-bottom: 20px;
}
.section-title h2 { margin: 0; font-size: 21px; }
.section-title span { color: var(--muted); font-size: 12px; }
.results { display: none; }
.track-list { display: grid; gap: 12px; }
.track {
    --accent: var(--purple);
    display: flex;
    align-items: center;
    gap: 14px;
    border: 1px solid #ffffff15;
    background: #ffffff06;
    border-radius: 17px;
    padding: 15px;
    min-width: 0;
}
.track-icon {
    flex: 0 0 48px;
    height: 48px;
    border-radius: 15px;
    display: grid;
    place-items: center;
    font-size: 25px;
    background: color-mix(in srgb, var(--accent) 15%, transparent);
    border: 1px solid color-mix(in srgb, var(--accent) 40%, transparent);
}
.track-info { flex: 1; min-width: 0; }
.track-info strong { display: block; font-size: 14px; overflow-wrap: anywhere; }
.track-info small { display: block; color: var(--muted); font-size: 12px; margin-top: 5px; }
.download {
    flex: 0 0 auto;
    background: var(--accent);
    color: #090916;
    padding: 12px 14px;
    border-radius: 12px;
    font-size: 12px;
}
.track:nth-child(1) { --accent: var(--orange); }
.track:nth-child(2) { --accent: var(--cyan); }
.track:nth-child(3) { --accent: var(--lime); }
.track:nth-child(4) { --accent: var(--pink); }
.track:nth-child(5) { --accent: var(--purple); }
footer {
    text-align: center;
    color: #777797;
    font-size: 12px;
    padding-top: 15px;
}
@media(max-width: 560px) {
    header { margin-bottom: 35px; }
    .pill { display: none; }
    .track { gap: 10px; padding: 11px; }
    .track-icon { flex-basis: 42px; height: 42px; font-size: 22px; }
    .download { padding: 11px 10px; }
    .track-info strong { font-size: 13px; }
}
</style>
</head>
<body>
<div class="container">
    <header>
        <div class="brand">
            <div class="brand-mark">♫</div>
            <span>MF<span class="gradient-text">STUDIO</span></span>
        </div>
        <div class="pill">AUDIO LAB · ONLINE</div>
    </header>

    <section class="hero">
        <div class="eyebrow">Seu som. Do seu jeito.</div>
        <h1>Separe sua música<br><span class="gradient-text">em segundos.</span></h1>
        <p class="subtitle">
            Extraia voz, bateria, baixo e outros instrumentos.
            Envie sua música e baixe cada faixa separadamente.
        </p>
    </section>

    <section class="panel">
        <form id="uploadForm">
            <div class="upload-area" id="dropArea">
                <div class="upload-icon">🎧</div>
                <h2>Escolha sua música</h2>
                <p>Arraste o arquivo para cá ou selecione no seu dispositivo.</p>
                <label class="choose-button" for="audioFile">📂 Selecionar arquivo</label>
                <input id="audioFile" name="audiofile" type="file"
                    accept=".mp3,.wav,.flac,.m4a,.ogg,.aac,.aiff,.wma" required>
                <div class="file-name" id="fileName"></div>
            </div>
            <button class="primary" id="submitButton" type="submit">
                ✨ Separar minha música
            </button>
        </form>
        <div class="status" id="status"></div>
        <div class="progress-track" id="progressTrack">
            <div class="progress-bar"></div>
        </div>
    </section>

    <section class="panel results" id="results">
        <div class="section-title">
            <h2>🎵 Suas faixas</h2>
            <span id="trackCount"></span>
        </div>
        <div class="track-list" id="trackList"></div>
    </section>

    <footer>MFSTUDIO · Ferramentas para quem ama música</footer>
</div>

<script>
const form = document.getElementById("uploadForm");
const audioFile = document.getElementById("audioFile");
const fileName = document.getElementById("fileName");
const dropArea = document.getElementById("dropArea");
const statusBox = document.getElementById("status");
const submitButton = document.getElementById("submitButton");
const progressTrack = document.getElementById("progressTrack");
const results = document.getElementById("results");
const trackList = document.getElementById("trackList");
const trackCount = document.getElementById("trackCount");

let originalBaseName = "Audio";
let pollingTimer = null;

audioFile.addEventListener("change", () => {
    showSelectedFile(audioFile.files[0]);
});

function showSelectedFile(file) {
    if (!file) return;
    fileName.textContent = "✓ " + file.name;
    fileName.style.display = "block";
    originalBaseName = file.name.replace(/\.[^.]+$/, "").trim() || "Audio";
}

["dragenter", "dragover"].forEach(eventName => {
    dropArea.addEventListener(eventName, event => {
        event.preventDefault();
        dropArea.classList.add("dragover");
    });
});
["dragleave", "drop"].forEach(eventName => {
    dropArea.addEventListener(eventName, event => {
        event.preventDefault();
        dropArea.classList.remove("dragover");
    });
});
dropArea.addEventListener("drop", event => {
    const files = event.dataTransfer.files;
    if (!files.length) return;
    const transfer = new DataTransfer();
    transfer.items.add(files[0]);
    audioFile.files = transfer.files;
    showSelectedFile(files[0]);
});

function setStatus(message, isError = false) {
    statusBox.textContent = message;
    statusBox.style.display = "block";
    statusBox.classList.toggle("error", isError);
}

function getTrackInfo(url, fallbackName) {
    const raw = (url || "") + " " + (fallbackName || "");
    const text = raw.toLowerCase();

    if (text.includes("instrumental")) {
        return { label: "Instrumental", emoji: "🎼" };
    }
    if (text.includes("vocal") || text.includes("voice")) {
        return { label: "Voz isolada", emoji: "🎤" };
    }
    if (text.includes("drum")) {
        return { label: "Bateria", emoji: "🥁" };
    }
    if (text.includes("bass")) {
        return { label: "Baixo", emoji: "🎸" };
    }
    if (text.includes("other")) {
        return { label: "Outros instrumentos", emoji: "🎹" };
    }
    if (text.includes("guitar")) {
        return { label: "Guitarra", emoji: "🎸" };
    }
    if (text.includes("piano")) {
        return { label: "Piano", emoji: "🎹" };
    }
    if (text.includes("strings")) {
        return { label: "Cordas", emoji: "🎻" };
    }
    if (text.includes("woodwind")) {
        return { label: "Sopros", emoji: "🎷" };
    }
    if (text.includes("brass")) {
        return { label: "Metais", emoji: "🎺" };
    }
    return { label: fallbackName || "Faixa separada", emoji: "🎵" };
}

function getExtension(url) {
    try {
        const pathname = new URL(url, window.location.origin).pathname;
        const match = pathname.match(/\.([a-z0-9]{2,5})$/i);
        return match ? match[1].toLowerCase() : "mp3";
    } catch {
        return "mp3";
    }
}

function safeFilenamePart(name) {
    return name
        .replace(/[<>:"/\\|?*\x00-\x1F]/g, "_")
        .replace(/\s+/g, " ")
        .trim()
        .replace(/[. ]+$/, "") || "Audio";
}

function renderTracks(files) {
    trackList.innerHTML = "";
    results.style.display = "block";
    trackCount.textContent = files.length + (files.length === 1 ? " faixa" : " faixas");

    files.forEach((file, index) => {
        const url = file.url || file.download_url || file.file || "";
        if (!url) return;

        const info = getTrackInfo(url, file.name || file.title || "");
        const extension = getExtension(url);
        const base = safeFilenamePart(originalBaseName);
        const downloadName = `${base} - ${info.label}.${extension}`;

        const row = document.createElement("div");
        row.className = "track";

        const icon = document.createElement("div");
        icon.className = "track-icon";
        icon.textContent = info.emoji;
        icon.setAttribute("aria-hidden", "true");

        const details = document.createElement("div");
        details.className = "track-info";

        const title = document.createElement("strong");
        title.textContent = `${info.emoji} ${base} - ${info.label}`;

        const subtitle = document.createElement("small");
        subtitle.textContent = "Arquivo ." + extension.toUpperCase() + " · Pronto para baixar";

        const button = document.createElement("button");
        button.className = "download";
        button.type = "button";
        button.textContent = "⬇ Baixar";
        button.addEventListener("click", () => {
            const downloadUrl = "/api/baixar?url=" +
                encodeURIComponent(url) +
                "&name=" + encodeURIComponent(downloadName);
            window.location.href = downloadUrl;
        });

        details.appendChild(title);
        details.appendChild(subtitle);
        row.appendChild(icon);
        row.appendChild(details);
        row.appendChild(button);
        trackList.appendChild(row);
    });

    if (!trackList.children.length) {
        setStatus("O processamento terminou, mas não encontrei links de download válidos.", true);
    } else {
        results.scrollIntoView({ behavior: "smooth", block: "start" });
    }
}

async function checkStatus(hash) {
    try {
        const response = await fetch("/api/status/" + encodeURIComponent(hash));
        const data = await response.json();

        if (!response.ok || data.error) {
            throw new Error(data.error || "Não foi possível consultar o processamento.");
        }

        if (data.status === "done" || data.status === "completed" || data.status === "success") {
            clearInterval(pollingTimer);
            pollingTimer = null;
            submitButton.disabled = false;
            submitButton.textContent = "✨ Separar outra música";
            progressTrack.style.display = "none";
            renderTracks(data.files || []);
            if (!trackList.children.length) {
                setStatus("A separação terminou, mas o serviço não retornou faixas para baixar.", true);
            } else {
                setStatus("✅ Música separada com sucesso! Escolha suas faixas abaixo.");
            }
        } else if (data.status === "error" || data.status === "failed") {
            clearInterval(pollingTimer);
            pollingTimer = null;
            submitButton.disabled = false;
            submitButton.textContent = "✨ Tentar novamente";
            progressTrack.style.display = "none";
            setStatus(data.message || "O processamento falhou. Tente novamente.", true);
        } else {
            setStatus(data.message || "Estamos separando sua música. Isso pode levar alguns minutos.");
        }
    } catch (error) {
        clearInterval(pollingTimer);
        pollingTimer = null;
        submitButton.disabled = false;
        submitButton.textContent = "✨ Tentar novamente";
        progressTrack.style.display = "none";
        setStatus(error.message || "Erro ao consultar o processamento.", true);
    }
}

form.addEventListener("submit", async event => {
    event.preventDefault();

    const file = audioFile.files[0];
    if (!file) {
        setStatus("Selecione um arquivo de áudio primeiro.", true);
        return;
    }

    if (pollingTimer) {
        clearInterval(pollingTimer);
        pollingTimer = null;
    }

    originalBaseName = file.name.replace(/\.[^.]+$/, "").trim() || "Audio";
    results.style.display = "none";
    trackList.innerHTML = "";
    submitButton.disabled = true;
    submitButton.textContent = "⏳ Enviando música...";
    progressTrack.style.display = "block";
    setStatus("Enviando seu arquivo. Aguarde...");

    try {
        const formData = new FormData();
        formData.append("audiofile", file);

        const response = await fetch("/api/separar", {
            method: "POST",
            body: formData
        });
        const data = await response.json();

        if (!response.ok || data.error) {
            throw new Error(data.error || "Não foi possível iniciar a separação.");
        }

        const hash = data.hash || data.job_hash || data.id;
        if (!hash) throw new Error("O serviço não retornou o identificador do processamento.");

        submitButton.textContent = "🎧 Separando...";
        setStatus("Arquivo recebido! A separação pode levar alguns minutos.");

        pollingTimer = setInterval(() => checkStatus(hash), 4000);
        await checkStatus(hash);
    } catch (error) {
        submitButton.disabled = false;
        submitButton.textContent = "✨ Tentar novamente";
        progressTrack.style.display = "none";
        setStatus(error.message || "Ocorreu um erro ao enviar a música.", true);
    }
});
</script>
</body>
</html>
"""


def allowed_file(filename):
    return (
        bool(filename)
        and "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


def extract_hash(data):
    if not isinstance(data, dict):
        return None
    for key in ("hash", "job_hash", "id"):
        value = data.get(key)
        if value:
            return str(value)
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

    status_value = data.get("status", data.get("state", "processing"))
    status_text = str(status_value).lower()

    files = []
    possible_files = (
        data.get("files")
        or data.get("results")
        or data.get("output_files")
        or data.get("stems")
        or []
    )

    if isinstance(possible_files, dict):
        possible_files = [
            {"name": key, "url": value}
            for key, value in possible_files.items()
        ]

    if isinstance(possible_files, list):
        for item in possible_files:
            if isinstance(item, str):
                files.append({"url": item})
            elif isinstance(item, dict):
                url = (
                    item.get("url")
                    or item.get("download_url")
                    or item.get("file_url")
                    or item.get("link")
                )
                if url:
                    files.append({
                        "url": url,
                        "name": item.get("name") or item.get("title") or ""
                    })

    # Algumas respostas da API usam um campo de resultado diferente.
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
            data={
                "api_token": API_KEY,
                "sep_type": "20",
                "output_format": "0",
            },
            files={
                "audiofile": (
                    secure_filename(audio.filename),
                    audio.stream,
                    audio.mimetype or "application/octet-stream",
                )
            },
            timeout=120,
        )
        response.raise_for_status()
        data = response.json()

        job_hash = extract_hash(data)
        if not job_hash:
            message = (
                data.get("message")
                or data.get("error")
                or "O serviço não retornou o identificador do processamento."
            ) if isinstance(data, dict) else "Resposta inválida do serviço."

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

    if not re.fullmatch(r"[A-Za-z0-9_-]+", job_hash):
        return jsonify(error="Identificador inválido."), 400

    if not API_KEY:
        return jsonify(error="A chave da API não está configurada no servidor."), 500

    try:
        response = requests.get(
            f"{API_BASE}/separation/get",
            params={"hash": job_hash, "api_token": API_KEY},
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()

        state, message, files = extract_status(data)

        return jsonify(
            status=state,
            message=message,
            files=files,
        )

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

    # Aceita apenas arquivos hospedados no domínio do serviço de separação.
    if (
        parsed.scheme != "https"
        or not (hostname == "mvsep.com" or hostname.endswith(".mvsep.com"))
        or parsed.username
        or parsed.password
    ):
        return jsonify(error="Endereço de download inválido."), 400

    # Evita que o nome fornecido pelo navegador injete cabeçalhos.
    requested_name = unquote(requested_name).replace("\\", "/").split("/")[-1]
    requested_name = re.sub(r"[\r\n\x00-\x1f]", "", requested_name)
    requested_name = secure_filename(requested_name.replace(" ", "_"))

    if not requested_name:
        requested_name = "Audio_-_Faixa.mp3"

    try:
        upstream = requests.get(
            source_url,
            stream=True,
            timeout=(15, 120),
            allow_redirects=False,
        )

        if upstream.is_redirect:
            upstream.close()
            return jsonify(error="O serviço de arquivos redirecionou o download. Tente novamente mais tarde."), 502

        if upstream.status_code != 200:
            upstream.close()
            return jsonify(error="Não foi possível baixar o arquivo neste momento."), 502

        content_type = upstream.headers.get(
            "Content-Type", "application/octet-stream"
        )

        def stream_file():
            try:
                for chunk in upstream.iter_content(chunk_size=64 * 1024):
                    if chunk:
                        yield chunk
            finally:
                upstream.close()

        response = Response(
            stream_file(),
            content_type=content_type,
            headers={
                "Content-Disposition": f'attachment; filename="{requested_name}"',
                "X-Content-Type-Options": "nosniff",
                "Cache-Control": "no-store",
            },
        )

        content_length = upstream.headers.get("Content-Length")
        if content_length:
            response.headers["Content-Length"] = content_length

        return response

    except requests.RequestException:
        app.logger.exception("Erro ao buscar o arquivo para download.")
        return jsonify(error="Falha ao preparar o download. Tente novamente."), 502


@app.errorhandler(413)
def file_too_large(_error):
    return jsonify(error="O arquivo ultrapassa o limite de 100 MB."), 413


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "5000")),
        debug=False,
    )
