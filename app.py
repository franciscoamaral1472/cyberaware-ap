from flask import Flask, request, jsonify

app = Flask(__name__)


@app.get("/")
def root():
    return "CyberAware Activity Provider – Flask is running!"


# 1) Página de configuração (config_url)
@app.get("/config")
def config():
    html = (
        "<!DOCTYPE html>\n"
        "<html lang='pt'>\n"
        "<head>\n"
        "  <meta charset='UTF-8' />\n"
        "  <title>CyberAware – Configuração</title>\n"
        "</head>\n"
        "<body>\n"
        "  <h2>Configuração da atividade CyberAware</h2>\n"
        "  <label>Duração (minutos):\n"
        "    <input type='number' name='duracao' value='15' />\n"
        "  </label><br/><br/>\n"
        "  <label>Nível de dificuldade:\n"
        "    <select name='dificuldade'>\n"
        "      <option value='easy'>Fácil</option>\n"
        "      <option value='medium' selected>Médio</option>\n"
        "      <option value='hard'>Difícil</option>\n"
        "    </select>\n"
        "  </label><br/><br/>\n"
        "  <label>Instruções para o aluno:<br/>\n"
        "    <textarea name='instrucoes' rows='4' cols='50'>Introdução à atividade CyberAware.</textarea>\n"
        "  </label>\n"
        "</body>\n"
        "</html>\n"
    )
    return html


# 2) Lista de parâmetros de configuração (json_params_url)
@app.get("/json-params")
def json_params():
    params = [
        {"name": "duracao", "type": "integer"},
        {"name": "dificuldade", "type": "text/plain"},
        {"name": "instrucoes", "type": "text/plain"},
    ]
    return jsonify(params)


# 3) Deploy da atividade (user_url)
@app.get("/deploy")
def deploy():
    activity_id = request.args.get("activityID", "")
    deploy_url = f"https://cyberaware-ap.onrender.com/play?activityID={activity_id}"
    return deploy_url


# 4) Lista de analytics disponíveis (analytics_list_url)
@app.get("/analytics-list")
def analytics_list():
    data = {
        "qualAnalytics": [
            {"name": "Student activity profile", "type": "URL"}
        ],
        "quantAnalytics": [
            {"name": "Acedeu à atividade", "type": "boolean"},
            {"name": "Progresso (%)", "type": "integer"},
        ],
    }
    return jsonify(data)


# 5) Analytics de atividade (analytics_url)
@app.post("/analytics")
def analytics():
    body = request.get_json(silent=True) or {}
    activity_id = body.get("activityID", "")

    response = [
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
            ],
        }
    ]
    return jsonify(response)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
