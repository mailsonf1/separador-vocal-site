
from pathlib import Path
from threading import Thread
import subprocess
import uuid
import os

from flask import Flask, request, render_template_string, send_from_directory, redirect, url_for

BASE = Path(__file__).resolve().parent
UPLOADS = BASE / "uploads"
OUTPUTS = BASE / "site_outputs"

UPLOADS.mkdir(exist_ok=True)
OUTPUTS.mkdir(exist_ok=True)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024

JOBS = {}

HTML = """
<!doctype html>
<html lang="pt-br">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Separador Vocal</title>
<style>
body{font-family:Arial;background:#10131b;color:#fff;margin:0;padding:30px}
main{max-width:650px;margin:30px auto;background:#1b2030;padding:28px;border-radius:18px}
h1{margin-top:0}p{color:#c2c8d8}
input,button{box-sizing:border-box;width:100%;padding:14px;margin:9px 0;border-radius:9px}
input{background:#10131b;color:white;border:1px solid #414a60}
button{background:#7c5cff;color:white;border:0;font-weight:bold;cursor:pointer}
a{color:#b9aaff}.result{padding:12px;background:#10131b;border-radius:10px;margin-top:12px}
</style>
</head>
<body><main>
<h1>🎵 Separador Vocal</h1>
<p>Separe uma música em voz e instrumental.</p>
<form action="/separar" method="post" enctype="multipart/form-data">
<label>Enviar arquivo MP3 ou WAV</label>
<input type="file" name="audio" accept=".mp3,.wav" required>
<button type="submit">Separar música</button>
</form>
{% if message %}<p>{{ message }}</p>{% endif %}
{% if job %}
<div class="result">
<strong>Status:</strong> {{ job.status }}
{% if job.error %}<p>{{ job.error }}</p>{% endif %}
{% if job.files %}
<h3>Arquivos prontos</h3>
{% for file in job.files %}
<p><a href="/arquivos/{{ file }}">Baixar {{ file }}</a></p>
{% endfor %}
{% endif %}
{% if job.status == "Processando" %}
<p>Atualize esta página daqui a pouco para conferir.</p>
{% endif %}
</div>
{% endif %}
<p>Versão de teste local.</p>
</main></body></html>
"""

def process_audio(job_id, source):
    try:
        JOBS[job_id]["status"] = "Processando"
        destination = OUTPUTS / job_id
        destination.mkdir(exist_ok=True)

        command = [
            "uv", "run", "melband-roformer-infer",
            "--input_folder", str(source.parent),
            "--store_dir", str(destination),
            "--device", "cpu",
        ]

        result = subprocess.run(
            command,
            cwd=BASE,
            capture_output=True,
            text=True,
            errors="replace",
        )

        if result.returncode != 0:
            JOBS[job_id]["status"] = "Erro"
            JOBS[job_id]["error"] = (result.stderr or result.stdout or "Falha no processamento")[-1800:]
            return

        files = [
            str(p.relative_to(OUTPUTS)).replace("\\", "/")
            for p in destination.rglob("*")
            if p.is_file() and p.suffix.lower() in (".wav", ".mp3", ".flac")
        ]

        if not files:
            JOBS[job_id]["status"] = "Erro"
            JOBS[job_id]["error"] = "O programa terminou, mas não encontramos os arquivos gerados."
        else:
            JOBS[job_id]["status"] = "Concluído"
            JOBS[job_id]["files"] = files

    except Exception as exc:
        JOBS[job_id]["status"] = "Erro"
        JOBS[job_id]["error"] = str(exc)

@app.get("/")
def home():
    return render_template_string(HTML)

@app.post("/separar")
def separate():
    file = request.files.get("audio")
    if not file or not file.filename:
        return render_template_string(HTML, message="Escolha um arquivo.")

    extension = Path(file.filename).suffix.lower()
    if extension not in (".mp3", ".wav"):
        return render_template_string(HTML, message="Envie um arquivo MP3 ou WAV.")

    job_id = uuid.uuid4().hex[:10]
    job_folder = UPLOADS / job_id
    job_folder.mkdir(exist_ok=True)
    source = job_folder / ("audio" + extension)
    file.save(source)

    JOBS[job_id] = {"status": "Na fila", "files": [], "error": ""}
    Thread(target=process_audio, args=(job_id, source), daemon=True).start()
    return redirect(url_for("status", job_id=job_id))

@app.get("/status/<job_id>")
def status(job_id):
    job = JOBS.get(job_id)
    if not job:
        return redirect(url_for("home"))
    return render_template_string(HTML, job=job)

@app.get("/arquivos/<path:filename>")
def download(filename):
    return send_from_directory(OUTPUTS, filename, as_attachment=True)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
