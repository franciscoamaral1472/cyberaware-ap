from flask import Flask, request, jsonify

app = Flask(__name__)

# 1) Página de configuração
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

  <label>Instruções:<br/>
    <textarea name="instrucoes" rows="4" cols="50">Introdução à atividade CyberAware.</textarea>
  </label>
</body>
</html>"""
    return html


# 2) json_params_url
@app.get("/json-params")
def json_params():
    return jsonify([
        {"name": "duracao", "type": "integer"},
        {"name": "dificuldade", "type": "text/plain"},
        {"name": "instrucoes", "type": "text/plain"},
    ])


# 3) Deploy (user_url)
@app.get("/deploy")
def deploy():
    activity_id = request.args.get("activityID", "")
    return f"https://cyberaware-ap.onrender.com/play?activityID={activity_id}"


# 4) Lista de analytics
@app.get("/analytics-list")
def analytics_list():
    return jsonify({
        "qualAnalytics": [
            {"name": "Student activity profile", "type": "URL"}
        ],
        "quantAnalytics": [
            {"name": "Acedeu à atividade", "type": "boolean"},
            {"name": "Progresso (%)", "type": "integer"}
        ]
    })


# 5) Analytics de atividade
@app.post("/analytics")
def analytics():
    body = request.get_json(silent=True) or {}
    activity_id = body.get("activityID", "")

    return jsonify([
        {
            "inveniraStdID": "1001",
            "quantAnalytics": [
                {"name": "Acedeu à atividade", "value": True},
                {"name": "Progresso (%)", "value": 40},
            ],
            "qualAnalytics": [
                {
                    "Student activity profile":
                        f"https://cyberaware-ap.onrender.com/analytics/profile?activityID={activity_id}&user=1001"
                }

