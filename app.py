from flask import Flask, request, jsonify

# criar a app Flask
app = Flask(__name__)


# 1) Página de configuração (config_url) – GET sem parâmetros
@app.get("/config")
def config():
    html = """<!DOCTYPE html>
<html lang="pt">
<head>
  <meta charset="UTF-8" />
  <title>CyberAware – Configuração</title>
</head>
<body>
  <h2>Configuração da atividade CyberAware</h2>

  <label>Duração (minutos):
    <input type="number" name="duracao" value="15" />
  </label>
  <br/><br/>

  <label>Nível de dificuldade:
    <select name="dificuldade">
      <option value="easy">Fácil</option>
      <option value="medium" selected>Médio</option>
      <option value="hard">Difícil</option>
    </select>
  </label>
  <br/><br/>

  <label>Instruções para o aluno:<br/>
    <textarea name="instrucoes" rows="4" cols="50">Introdução à atividade CyberAware.</textarea>
  </label>
</body>
</html>"""
    return html


# 2) Lista de parâmetros de configuração (json_params_url) – GET sem parâmetros
@app.get("/json-params")
def json_params():
    # Estes nomes têm de bater certo com os "name" dos campos na página /config
    params = [
        {"name": "duracao", "type": "integer"},
        {"name": "dificuldade", "type": "text/plain"},
        {"name": "instrucoes", "type": "text/plain"},
    ]
    return jsonify(params)


# 3) Deploy da atividade (user_url) – GET com activityID
@app.get("/deploy")
def deploy():
    activity_id = request.args.get("activityID", "")
    deploy_url = f"https://cyberaware-ap.onrender.com/play?activityID={activity_id}"
    return deploy_url


# 4) Lista de analytics disponíveis (analytics_list_url) – GET sem parâmetros
@app.get("/a
