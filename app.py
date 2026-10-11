
from flask import Flask, request, render_template_string, jsonify
import os
import requests
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024

MVSEP_API = "https://mvsep.com/api"

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
<title>Separador Vocal</title>

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
    max-width: 650px;
    padding: 32px;
    border-radius: 20px;
    background: #1b2030;
    border: 1px solid #343b50;
}

h1 { margin: 12px 0; }

p {
    color: #c2c8d8;
    line-height: 1.6;
}

.tag {
    display: inline-block;
    padding: 7px 12px;
    background: #292344;
    color: #c5b8ff;
    border-radius: 20px;
    font-size: 13px;
}

input[type=file] {
    display: block;
    width: 100%;
    padding: 14px;
    margin: 18px 0;
    background: #111522;
    border: 1px dashed #606982;
    border-radius: 10px;
    color: #dce1ef;
}

button, .download {
    display: block;
    width: 100%;
    padding: 14px;
    margin-top: 12px;
    border: 0;
    border-radius: 10px;
    background: #7c5cff;
    color: white;
    font-size: 16px;
    font-weight: bold;
    text-align: center;
    text-decoration: none;
    cursor: pointer;
    overflow-wrap: anywhere;
}

button:disabled {
    opacity: .55;
    cursor: wait;
}

.status {
    margin-top: 18px;
    padding: 14px;
    background: #111522;
    border-radius: 10px;
    display: none;
    overflow-wrap: anywhere;
}

.file-link { background: #252c40; }

.small {
    font-size: 13px;
    color: #9da7bf;
}
</style>
</head>

<body>
<main>
    <span class="tag">PROCESSAMENTO POR MVSEP</span>
    <h1>🎵 Separador Vocal</h1>

    <p>
        Envie uma música e receba as faixas separadas:
        voz, bateria, baixo e outros instrumentos.
    </p>

    <form id="uploadForm">
        <input
            id="audio"
            name="audio"
            type="file"
            accept="audio/*,.mp3,.wav,.flac,.m4a,.ogg,.aac,.aiff,.wma"
            required
        >
        <button id="submitBtn" type="submit">
            Separar música
        </button>
    </form>

    <div id="status" class="status" role="status"></div>

    <p class="small">
        Arquivos de áudio de até 100 MB.
        O tempo depende da fila do serviço de processamento.
    </p>
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
            if (typeof value === "object" && value !== null) {
                return {label: key, ...value};
            }
            return {label: key, url: value};
        });

    return list.map((f, i) => {
        if (typeof f === "string") {
            return {
                label: "Faixa " + (i + 1),
                url: f
            };
        }

        const url =
            f.url ||
            f.link ||
            f.download_url ||
            f.file_url ||
            f.href;

        const originalName =
            f.name ||
            f.filename ||
            f.file_name ||
            f.title ||
            f.label ||
            "";

        const hint = (
            String(originalName) + " " + String(url || "")
        ).toLowerCase();

        let label = originalName || ("Faixa " + (i + 1));

        if (hint.includes("vocals") || hint.includes("vocal")) {
            label = "Voz (vocal isolado)";
        } else if (
            hint.includes("drums") ||
            hint.includes("drum")
        ) {
            label = "Bateria";
        } else if (hint.includes("bass")) {
            label = "Baixo";
        } else if (
            hint.includes("other") ||
            hint.includes("others")
        ) {
            label = "Outros instrumentos";
        } else if (hint.includes("instrumental")) {
            label = "Instrumental (sem voz)";
        }

        return {label, url};
    }).filter(f =>
        typeof f.url === "string" &&
        /^https?:\/\//i.test(f.url)
    );
}

function showDownloadLinks(files, fallbackUrl) {
    statusBox.textContent = "Separação concluída! Baixe suas faixas:";

    files.forEach(file => {
        const link = document.createElement("a");
        link.className = "download file-link";
        link.href = file.url;
        link.target = "_blank";
        link.rel = "noopener";
        link.download = "";
        link.textContent = "⬇ Baixar " + file.label;
        statusBox.appendChild(link);
    });

    if (files.length === 0 && fallbackUrl &&
        /^https?:\/\//i.test(fallbackUrl)) {
        const link = document.createElement("a");
        link.className = "download file-link";
        link.href = fallbackUrl;
        link.target = "_blank";
        link.rel = "noopener";
        link.textContent = "Abrir resultado no MVSEP";
        statusBox.appendChild(link);
    }

    if (files.length === 0 && !fallbackUrl) {
        const message = document.createElement("p");
        message.textContent =
            "O processamento terminou, mas não encontrei os links das faixas.";
        statusBox.appendChild(message);
    }
}

form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const file = audioInput.files && audioInput.files[0];

    if (!file) {
        showStatus("Selecione novamente um arquivo de áudio.");
        return;
    }

    if (file.size > 100 * 1024 * 1024) {
        showStatus("O arquivo excede o limite de 100 MB.");
        return;
    }

    button.disabled = true;
    showStatus("Enviando sua música ao MVSEP...");

    try {
        const formData = new FormData();
        formData.append("audio", file);

        const response = await fetch("/api/separar", {
            method: "POST",
            body: formData
        });

        const result = await response.json();

        if (!response.ok || !result.success) {
            throw new Error(
                result.error || "Não foi possível enviar a música."
            );
        }

        const hash = result.hash;

        if (!hash) {
            throw new Error(
                "O MVSEP não retornou o identificador da tarefa."
            );
        }

        showStatus("Música enviada! Aguardando na fila do MVSEP...");

        let finished = false;
        let attempts = 0;
        const maxAttempts = 360;

        while (!finished && attempts < maxAttempts) {
            await new Promise(resolve => setTimeout(resolve, 5000));
            attempts++;

            const statusResponse = await fetch(
                "/api/status/" + encodeURIComponent(hash)
            );

            const payload = await statusResponse.json();

            if (!statusResponse.ok || payload.error) {
                throw new Error(
                    payload.error ||
                    "Erro ao consultar o processamento."
                );
            }

            if (payload.status === "done") {
                showDownloadLinks(
                    findFiles(payload.result),
                    payload.link ||
                    (payload.result &&
                     payload.result.data &&
                     payload.result.data.link)
                );
                finished = true;
            } else if (
                payload.status === "failed" ||
                payload.status === "not_found"
            ) {
                throw new Error(
                    payload.message ||
                    "O processamento falhou no MVSEP."
                );
            } else {
                const messages = {
                    waiting: "Aguardando na fila...",
                    processing: "Separando as faixas da música...",
                    distributing: "Preparando o processamento...",
                    merging: "Finalizando os arquivos..."
                };

                showStatus(
                    messages[payload.status] ||
                    "Processamento em andamento..."
                );
            }
        }

        if (!finished) {
            throw new Error(
                "O processamento está demorando. Tente consultar novamente mais tarde."
            );
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
            error="A chave MVSEP_API_KEY não está configurada no servidor."
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
            f"{MVSEP_API}/separation/create",
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
            error="Não consegui conectar ao MVSEP. Tente novamente."
        ), 502

    except ValueError:
        return jsonify(
            success=False,
            error="O MVSEP retornou uma resposta inesperada."
        ), 502

    if response.status_code >= 400 or not payload.get("success"):
        message = (
            (payload.get("data") or {}).get("message") or
            "O MVSEP recusou a solicitação. Verifique sua conta e tente novamente."
        )

        return jsonify(success=False, error=message), 400

    data = payload.get("data") or {}
    job_hash = data.get("hash")

    if not job_hash:
        return jsonify(
            success=False,
            error="O MVSEP não retornou o identificador da tarefa."
        ), 502

    return jsonify(
        success=True,
        hash=str(job_hash),
        message="Tarefa criada."
    ), 202


@app.get("/api/status/<job_hash>")
def status(job_hash):
    if not job_hash or len(job_hash) > 200:
        return jsonify(error="Identificador inválido."), 400

    try:
        response = requests.get(
            f"{MVSEP_API}/separation/get",
            params={"hash": job_hash},
            timeout=30
        )

        payload = response.json()

    except requests.RequestException:
        return jsonify(
            error="Não consegui consultar o MVSEP. Tente novamente."
        ), 502

    except ValueError:
        return jsonify(
            error="O MVSEP retornou uma resposta inesperada."
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
        result=payload,
        link=data.get("link")
    )


@app.errorhandler(413)
def too_large(_error):
    return jsonify(
        success=False,
        error="O arquivo excede o limite de 100 MB."
    ), 413


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
