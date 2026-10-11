
from flask import Flask, request, render_template_string, jsonify, Response
import os
import requests
from urllib.parse import urlparse
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024

API_BASE = "https://mvsep.com/api"

ALLOWED_EXTENSIONS = {
    "mp3", "wav", "flac", "m4a", "ogg",
    "aac", "aiff", "wma"
}

HTML = r"""
<!doctype html>
<html lang="pt-br">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#10131b">
<title>MFSTUDIO | Separador de Áudio</title>

<style>
* { box-sizing: border-box; }

body {
    margin: 0;
    padding: 24px;
    min-height: 100vh;
    display: grid;
    place-items: center;
    font-family: Arial, sans-serif;
    background: #10131b;
    color: #fff;
}

main {
    width: 100%;
    max-width: 680px;
    padding: 30px;
    border-radius: 24px;
    background: #1b2030;
    border: 1px solid #343b50;
    box-shadow: 0 20px 70px #0005;
}

.brand {
    display: flex;
    align-items: center;
    gap: 14px;
}

.logo {
    width: 54px;
    height: 54px;
    border-radius: 16px;
    display: grid;
    place-items: center;
    background: #7c5cff;
    font-size: 28px;
}

.brand-name {
    font-size: 23px;
    font-weight: 800;
    letter-spacing: 2px;
}

.brand-sub {
    margin-top: 5px;
    color: #c5b8ff;
    font-size: 11px;
    letter-spacing: 2px;
}

h1 {
    font-size: clamp(27px, 6vw, 38px);
    margin: 30px 0 10px;
}

p {
    color: #c2c8d8;
    line-height: 1.65;
}

.upload-box {
    margin-top: 24px;
    padding: 20px;
    border: 1px dashed #606982;
    border-radius: 16px;
    background: #111522;
}

input[type=file] {
    display: block;
    width: 100%;
    margin-top: 14px;
    color: #dce1ef;
    font-size: 14px;
}

button, .download {
    display: block;
    width: 100%;
    padding: 15px;
    margin-top: 14px;
    border: 0;
    border-radius: 12px;
    background: #7c5cff;
    color: #fff;
    font-size: 16px;
    font-weight: 700;
    text-align: center;
    text-decoration: none;
    cursor: pointer;
    overflow-wrap: anywhere;
}

button:disabled {
    opacity: .6;
    cursor: wait;
}

.status {
    display: none;
    margin-top: 20px;
    padding: 16px;
    background: #111522;
    border: 1px solid #343b50;
    border-radius: 14px;
    overflow-wrap: anywhere;
}

.download {
    background: #252c40;
    border: 1px solid #414b67;
    text-align: left;
}

.download:hover {
    background: #343c55;
}

.features {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px;
    margin-top: 24px;
}

.feature {
    padding: 14px;
    border-radius: 12px;
    background: #252c40;
    color: #e4e8f5;
    font-size: 14px;
}

.note {
    font-size: 12px;
    color: #9da7bf;
    margin-top: 22px;
}

footer {
    text-align: center;
    margin-top: 26px;
    color: #818ba5;
    font-size: 12px;
    letter-spacing: 1px;
}

@media (max-width: 480px) {
    main { padding: 22px; }
    .features { grid-template-columns: 1fr; }
}
</style>
</head>

<body>
<main>
    <div class="brand">
        <div class="logo">≋</div>
        <div>
            <div class="brand-name">MFSTUDIO</div>
            <div class="brand-sub">SEPARADOR DE ÁUDIO</div>
        </div>
    </div>

    <h1>Sua música. Suas faixas.</h1>
    <p>
        Separe sua música em voz, bateria, baixo e outros instrumentos.
        Baixe cada faixa individualmente.
    </p>

    <form id="uploadForm">
        <div class="upload-box">
            <strong>Escolha sua música</strong>
            <input
                id="audio"
                name="audio"
                type="file"
                accept="audio/*,.mp3,.wav,.flac,.m4a,.ogg,.aac,.aiff,.wma"
                required
            >
        </div>
        <button id="submitBtn" type="submit">
            Separar música
        </button>
    </form>

    <div id="status" class="status" role="status"></div>

    <div class="features">
        <div class="feature">🎤 Voz isolada</div>
        <div class="feature">🥁 Bateria</div>
        <div class="feature">🎸 Baixo</div>
        <div class="feature">🎹 Outros instrumentos</div>
    </div>

    <p class="note">
        Arquivos de áudio de até 100 MB. O tempo de processamento
        depende do tamanho do arquivo e da fila de tarefas.
    </p>

    <footer>MFSTUDIO · FERRAMENTAS DE ÁUDIO</footer>
</main>

<script>
const form = document.getElementById("uploadForm");
const audioInput = document.getElementById("audio");
const button = document.getElementById("submitBtn");
const statusBox = document.getElementById("status");

function showStatus(message) {
    statusBox.style.display = "block";
    statusBox.textContent = message;
}

function findFiles(payload) {
    const data = payload && payload.data ? payload.data : payload;
    const files = data && data.files;

    if (!files) return [];

    const list = Array.isArray(files)
        ? files
        : Object.entries(files).map(([key, value]) => {
            if (value && typeof value === "object") {
                return {label: key, ...value};
            }
            return {label: key, url: value};
        });

    return list.map((f, i) => {
        if (typeof f === "string") {
            return {label: "Faixa " + (i + 1), url: f};
        }

        const url =
            f.url || f.link || f.download_url ||
            f.file_url || f.href;

        const original = [
            f.name, f.filename, f.file_name, f.title,
            f.label, url
        ].filter(Boolean).join(" ").toLowerCase();

        let label = f.name || f.filename || ("Faixa " + (i + 1));

        if (original.includes("vocals") || original.includes("vocal")) {
            label = "Voz isolada";
        } else if (original.includes("drums") || original.includes("drum")) {
            label = "Bateria";
        } else if (original.includes("bass")) {
            label = "Baixo";
        } else if (original.includes("other")) {
            label = "Outros instrumentos";
        } else if (original.includes("instrumental")) {
            label = "Instrumental (sem voz)";
        }

        return {label, url};
    }).filter(f =>
        typeof f.url === "string" &&
        /^https:\/\//i.test(f.url)
    );
}

function showDownloadLinks(files) {
    statusBox.replaceChildren();

    const heading = document.createElement("p");
    heading.textContent = "Separação concluída! Baixe suas faixas:";
    statusBox.appendChild(heading);

    files.forEach(file => {
        const link = document.createElement("a");
        link.className = "download";
        link.href = "/api/baixar?url=" + encodeURIComponent(file.url);
        link.textContent = "⬇ Baixar " + file.label;
        statusBox.appendChild(link);
    });

    if (!files.length) {
        const message = document.createElement("p");
        message.textContent =
            "O processamento terminou, mas não foram encontrados links para download.";
        statusBox.appendChild(message);
    }
}

form.addEventListener("submit", async event => {
    event.preventDefault();

    const file = audioInput.files && audioInput.files[0];

    if (!file) {
        showStatus("Selecione um arquivo de áudio.");
        return;
    }

    if (file.size > 100 * 1024 * 1024) {
        showStatus("O arquivo excede o limite de 100 MB.");
        return;
    }

    button.disabled = true;
    showStatus("Enviando sua música...");

    try {
        const formData = new FormData();
        formData.append("audio", file);

        const response = await fetch("/api/separar", {
            method: "POST",
            body: formData
        });

        const result = await response.json();

        if (!response.ok || !result.success) {
            throw new Error(result.error || "Não foi possível enviar o arquivo.");
        }

        if (!result.hash) {
            throw new Error("O serviço não retornou o identificador da tarefa.");
        }

        showStatus("Música enviada! Aguardando o processamento...");

        let finished = false;

        for (let attempt = 0; attempt < 360 && !finished; attempt++) {
            await new Promise(resolve => setTimeout(resolve, 5000));

            const statusResponse = await fetch(
                "/api/status/" + encodeURIComponent(result.hash)
            );

            const payload = await statusResponse.json();

            if (!statusResponse.ok || payload.error) {
                throw new Error(payload.error || "Erro ao consultar o processamento.");
            }

            if (payload.status === "done") {
                showDownloadLinks(findFiles(payload.result));
                finished = true;
            } else if (
                payload.status === "failed" ||
                payload.status === "not_found"
            ) {
                throw new Error(payload.message || "Não foi possível separar a música.");
            } else {
                const messages = {
                    waiting: "Aguardando na fila...",
                    processing: "Separando as faixas...",
                    distributing: "Preparando o processamento...",
                    merging: "Finalizando os arquivos..."
                };

                showStatus(messages[payload.status] || "Processamento em andamento...");
            }
        }

        if (!finished) {
            throw new Error("O processamento está demorando. Tente novamente mais tarde.");
        }
    } catch (error) {
        showStatus("Não foi possível concluir: " + error.message);
    } finally {
        button.disabled = false;
    }
});
</script>
</body>
</html>
"""


@app.get("/")
def home():
    return render_template_string(HTML)


@app.post("/api/separar")
def separar():
    token = os.environ.get("MVSEP_API_KEY")

    if not token:
        return jsonify(
            success=False,
            error="A configuração do processamento está incompleta."
        ), 500

    audio = request.files.get("audio")

    if not audio or not audio.filename:
        return jsonify(
            success=False,
            error="Selecione um arquivo de áudio."
        ), 400

    filename = secure_filename(audio.filename)

    if (
        "." not in filename or
        filename.rsplit(".", 1)[1].lower() not in ALLOWED_EXTENSIONS
    ):
        return jsonify(
            success=False,
            error="Formato não suportado. Envie MP3, WAV, FLAC, M4A ou OGG."
        ), 400

    try:
        response = requests.post(
            f"{API_BASE}/separation/create",
            data={
                "api_token": token,
                "sep_type": "20",
                "output_format": "0"
            },
            files={
                "audiofile": (
                    filename,
                    audio.stream,
                    audio.mimetype or "application/octet-stream"
                )
            },
            timeout=90
        )
        payload = response.json()

    except requests.RequestException:
        return jsonify(
            success=False,
            error="Não foi possível enviar a música para processamento."
        ), 502

    except ValueError:
        return jsonify(
            success=False,
            error="Resposta inesperada do serviço de processamento."
        ), 502

    if response.status_code >= 400 or not payload.get("success"):
        message = (
            (payload.get("data") or {}).get("message") or
            "O processamento não foi aceito. Tente novamente."
        )
        return jsonify(success=False, error=message), 400

    data = payload.get("data") or {}
    job_hash = data.get("hash")

    if not job_hash:
        return jsonify(
            success=False,
            error="Não foi recebido o identificador do processamento."
        ), 502

    return jsonify(success=True, hash=str(job_hash)), 202


@app.get("/api/status/<job_hash>")
def status(job_hash):
    if not job_hash or len(job_hash) > 200:
        return jsonify(error="Identificador inválido."), 400

    try:
        response = requests.get(
            f"{API_BASE}/separation/get",
            params={"hash": job_hash},
            timeout=30
        )
        payload = response.json()

    except requests.RequestException:
        return jsonify(
            error="Não foi possível consultar o andamento."
        ), 502

    except ValueError:
        return jsonify(
            error="Resposta inesperada durante a consulta."
        ), 502

    if response.status_code >= 400 or not payload.get("success"):
        message = (
            (payload.get("data") or {}).get("message") or
            "Não foi possível consultar essa tarefa."
        )
        return jsonify(error=message), 502

    data = payload.get("data") or {}

    return jsonify(
        status=payload.get("status", "unknown"),
        message=data.get("message", ""),
        result=payload
    )


@app.get("/api/baixar")
def baixar():
    url = request.args.get("url", "")
    parsed = urlparse(url)
    hostname = (parsed.hostname or "").lower()

    if (
        parsed.scheme != "https" or
        not (hostname == "mvsep.com" or hostname.endswith(".mvsep.com")) or
        parsed.username or parsed.password
    ):
        return jsonify(error="Link de download inválido."), 400

    try:
        upstream = requests.get(
            url,
            stream=True,
            timeout=(15, 120),
            allow_redirects=False
        )

        if upstream.status_code in (301, 302, 303, 307, 308):
            upstream.close()
            return jsonify(
                error="Não foi possível iniciar o download. Tente novamente."
            ), 502

        upstream.raise_for_status()

        filename = secure_filename(os.path.basename(parsed.path)) or "faixa.mp3"

        def stream_file():
            try:
                for chunk in upstream.iter_content(chunk_size=64 * 1024):
                    if chunk:
                        yield chunk
            finally:
                upstream.close()

        headers = {
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Content-Type-Options": "nosniff"
        }

        length = upstream.headers.get("Content-Length")
        if length and length.isdigit():
            headers["Content-Length"] = length

        return Response(
            stream_file(),
            content_type=upstream.headers.get(
                "Content-Type", "application/octet-stream"
            ),
            headers=headers
        )

    except requests.RequestException:
        return jsonify(
            error="Não foi possível baixar a faixa. Tente novamente."
        ), 502


@app.errorhandler(413)
def too_large(_error):
    return jsonify(
        success=False,
        error="O arquivo excede o limite de 100 MB."
    ), 413


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
