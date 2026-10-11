
from pathlib import Path
from threading import Thread, Lock
import subprocess
import uuid
import shutil

import imageio_ffmpeg
from flask import (
    Flask,
    request,
    render_template_string,
    redirect,
    url_for,
    send_file,
    abort,
)

BASE = Path(__file__).resolve().parent
UPLOADS = BASE / "uploads"
OUTPUTS = BASE / "site_outputs"

UPLOADS.mkdir(parents=True, exist_ok=True)
OUTPUTS.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024

JOBS = {}
JOBS_LOCK = Lock()

HTML = """
<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
{% if job and job.status in ["Na fila", "Processando"] %}
<meta http-equiv="refresh" content="5">
{% endif %}
<title>MFSTUDIO | Instrumental</title>
<style>
*{box-sizing:border-box}
body{
    font-family:Arial,sans-serif;
    background:#10131b;
    color:#fff;
    margin:0;
    padding:24px;
}
main{
    max-width:620px;
    margin:35px auto;
    background:#1b2030;
    padding:28px;
    border-radius:18px;
}
h1{margin-top:0}
p{color:#c2c8d8;line-height:1.6}
input,button{
    width:100%;
    padding:14px;
    margin:12px 0;
    border-radius:9px;
}
input{
    background:#10131b;
    color:#fff;
    border:1px solid #414a60;
}
button{
    background:#7c5cff;
    color:white;
    border:0;
    font-weight:bold;
    cursor:pointer;
}
button:hover{background:#6847ed}
.result{
    padding:16px;
    background:#10131b;
    border-radius:10px;
    margin-top:18px;
}
.download{
    display:block;
    padding:14px;
    margin-top:12px;
    border-radius:9px;
    background:#7c5cff;
    color:#fff;
    text-decoration:none;
    text-align:center;
    font-weight:bold;
}
.note{font-size:13px;color:#9ca7bf}
</style>
</head>
<body>
<main>
<h1>MFSTUDIO</h1>
<p>Envie sua música e gere uma versão instrumental.</p>

<form action="/separar" method="post" enctype="multipart/form-data">
    <label for="audio">Selecione um arquivo MP3 ou WAV</label>
    <input
        id="audio"
        type="file"
        name="audio"
        accept=".mp3,.wav,audio/mpeg,audio/wav,audio/x-wav"
        required
    >
    <button type="submit">Gerar instrumental</button>
</form>

{% if message %}
<p>{{ message }}</p>
{% endif %}

{% if job %}
<div class="result">
    <strong>Status:</strong> {{ job.status }}

    {% if job.status == "Na fila" %}
        <p>A música está aguardando o processamento.</p>
    {% elif job.status == "Processando" %}
        <p>Estamos processando sua música. Esta página será atualizada automaticamente.</p>
        <p>O tempo depende da duração do áudio e da capacidade do servidor.</p>
    {% elif job.status == "Concluído" %}
        <p>Seu instrumental está pronto.</p>
        <a class="download" href="{{ url_for('download', job_id=job_id) }}">
            Baixar instrumental
        </a>
    {% elif job.status == "Erro" %}
        <p>{{ job.error }}</p>
    {% endif %}
</div>
{% endif %}

<p class="note">
Formatos aceitos: MP3 e WAV. O resultado disponibilizado é somente o instrumental.
</p>
</main>
</body>
</html>
"""


def update_job(job_id, **values):
    with JOBS_LOCK:
        if job_id in JOBS:
            JOBS[job_id].update(values)


def process_audio(job_id, source):
    job_folder = source.parent
    destination = OUTPUTS / job_id

    try:
        update_job(job_id, status="Processando", error="")

        # Converte MP3 ou WAV para WAV PCM estéreo, 44,1 kHz.
        # O modelo recebe sempre um WAV compatível com a configuração.
        input_folder = job_folder / "model_input"
        input_folder.mkdir(parents=True, exist_ok=True)

        converted = input_folder / "audio.wav"
        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()

        conversion_command = [
            ffmpeg,
            "-hide_banner",
            "-loglevel", "error",
            "-nostdin",
            "-y",
            "-i", str(source),
            "-vn",
            "-ac", "2",
            "-ar", "44100",
            "-c:a", "pcm_s16le",
            str(converted),
        ]

        conversion = subprocess.run(
            conversion_command,
            capture_output=True,
            text=True,
            errors="replace",
            timeout=300,
        )

        if conversion.returncode != 0 or not converted.exists():
            detail = (conversion.stderr or "Falha ao converter o áudio.")[-1200:]
            raise RuntimeError(detail)

        destination.mkdir(parents=True, exist_ok=True)

        # Executa o modelo de separação já configurado no repositório.
        command = [
            "uv", "run", "melband-roformer-infer",
            "--input_folder", str(input_folder),
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
            detail = (result.stderr or result.stdout or
                      "Falha durante a separação.")[-1800:]
            raise RuntimeError(detail)

        # Localiza somente o instrumental.
        instrumental_files = [
            path for path in destination.rglob("*")
            if path.is_file()
            and path.suffix.lower() == ".wav"
            and "instrumental" in path.stem.lower()
        ]

        if not instrumental_files:
            raise RuntimeError(
                "O processamento terminou, mas o instrumental não foi encontrado."
            )

        instrumental = instrumental_files[0]

        # Remove todas as outras saídas para não disponibilizar os vocais.
        for path in list(destination.rglob("*")):
            if path.is_file() and path != instrumental:
                path.unlink()

        relative_path = instrumental.relative_to(OUTPUTS).as_posix()

        update_job(
            job_id,
            status="Concluído",
            download_path=relative_path,
            error="",
        )

    except subprocess.TimeoutExpired:
        update_job(
            job_id,
            status="Erro",
            error="A conversão demorou demais. Tente um arquivo menor.",
        )
    except Exception as exc:
        update_job(
            job_id,
            status="Erro",
            error=str(exc)[:1800],
        )
    finally:
        # Apaga o upload original e o WAV temporário.
        shutil.rmtree(job_folder, ignore_errors=True)


@app.get("/")
def home():
    return render_template_string(HTML, job=None, job_id=None)


@app.post("/separar")
def separate():
    uploaded = request.files.get("audio")

    if not uploaded or not uploaded.filename:
        return render_template_string(
            HTML, job=None, job_id=None,
            message="Selecione um arquivo de áudio."
        )

    extension = Path(uploaded.filename).suffix.lower()

    if extension not in (".mp3", ".wav"):
        return render_template_string(
            HTML, job=None, job_id=None,
            message="Formato inválido. Envie MP3 ou WAV."
        )

    job_id = uuid.uuid4().hex[:12]
    job_folder = UPLOADS / job_id
    job_folder.mkdir(parents=True, exist_ok=True)

    source = job_folder / ("upload" + extension)

    try:
        uploaded.save(source)

        if not source.exists() or source.stat().st_size == 0:
            shutil.rmtree(job_folder, ignore_errors=True)
            return render_template_string(
                HTML, job=None, job_id=None,
                message="O arquivo enviado está vazio."
            )

        with JOBS_LOCK:
            JOBS[job_id] = {
                "status": "Na fila",
                "error": "",
                "download_path": None,
            }

        Thread(
            target=process_audio,
            args=(job_id, source),
            daemon=True,
        ).start()

        return redirect(url_for("status", job_id=job_id))

    except Exception as exc:
        shutil.rmtree(job_folder, ignore_errors=True)
        return render_template_string(
            HTML, job=None, job_id=None,
            message=f"Não foi possível receber o arquivo: {exc}"
        )


@app.get("/status/<job_id>")
def status(job_id):
    with JOBS_LOCK:
        job = JOBS.get(job_id)

    if not job:
        return redirect(url_for("home"))

    return render_template_string(HTML, job=job, job_id=job_id)


@app.get("/download/<job_id>")
def download(job_id):
    with JOBS_LOCK:
        job = JOBS.get(job_id)
        job = dict(job) if job else None

    if not job or job.get("status") != "Concluído":
        abort(404)

    relative_path = job.get("download_path")
    if not relative_path:
        abort(404)

    output_root = OUTPUTS.resolve()
    file_path = (OUTPUTS / relative_path).resolve()

    try:
        file_path.relative_to(output_root)
    except ValueError:
        abort(403)

    # Segunda verificação: somente arquivos de instrumental podem ser baixados.
    if (
        not file_path.is_file()
        or file_path.suffix.lower() != ".wav"
        or "instrumental" not in file_path.stem.lower()
    ):
        abort(404)

    return send_file(
        file_path,
        as_attachment=True,
        download_name="instrumental.wav",
        mimetype="audio/wav",
    )


@app.errorhandler(413)
def file_too_large(_error):
    return "Arquivo muito grande. O limite é 100 MB.", 413


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
