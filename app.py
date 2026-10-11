
from flask import Flask, render_template_string
import os

app = Flask(__name__)

HTML = """
<!doctype html>
<html lang="pt-br">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Separador Vocal</title>
<style>
* { box-sizing: border-box; }
body {
  margin: 0; padding: 24px; min-height: 100vh;
  display: grid; place-items: center;
  font-family: Arial, sans-serif;
  background: #10131b; color: #fff;
}
main {
  width: 100%; max-width: 620px; padding: 32px;
  border-radius: 20px; background: #1b2030;
  border: 1px solid #343b50;
}
h1 { margin-top: 0; }
p { color: #c2c8d8; line-height: 1.6; }
.tag {
  display: inline-block; padding: 7px 12px;
  background: #292344; color: #c5b8ff;
  border-radius: 20px; font-size: 13px;
}
button {
  width: 100%; padding: 14px; margin-top: 12px;
  border: 0; border-radius: 10px;
  background: #7c5cff; color: white;
  font-size: 16px; font-weight: bold;
}
</style>
</head>
<body>
<main>
  <span class="tag">VERSÃO DE TESTE</span>
  <h1>🎵 Separador Vocal</h1>
  <p>Separe a voz e o instrumental das suas músicas em um só lugar.</p>
  <p>Estamos preparando o processamento de áudio. Em breve, você poderá enviar seu arquivo e baixar as faixas separadas.</p>
  <button type="button">Processamento em preparação</button>
</main>
</body>
</html>
"""

@app.get("/")
def home():
    return render_template_string(HTML)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
