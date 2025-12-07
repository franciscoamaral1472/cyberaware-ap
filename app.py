from flask import Flask, request, jsonify

app = Flask(__name__)


# ============================================================
#  SINGLETON: AnalyticsRepository
#  Este componente mantém um repositório centralizado de analytics,
#  garantindo que toda a aplicação utiliza a mesma instância.
# ============================================================

class AnalyticsRepository:
    _instance = None

    def __init__(self):
        # Estrutura interna:
        # { activityID: { inveniraStdID: { analytics_dict } } }
        self._data = {}

    @classmethod
    def get_instance(cls):
        # Acede à instância única do repositório, criando-a caso ainda não exista.
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register_activity(self, activity_id: str) -> None:
        # Garante que existe uma estrutura para armazenar dados desta atividade.
        if activity_id not in self._data:
            self._data[activity_id] = {}

    def register_student_event(self, activity_id: str, invenira_std_id: str, event_data: dict) -> None:
        # Regista eventos associados a um estudante numa atividade.
        self.register_activity(activity_id)

        # Cria ou obtém o registo existente do estudante.
        student_analytics = self._data[activity_id].get(
            invenira_std_id,
            {
                "inveniraStdID": invenira_std_id,
                "quantAnalytics": [],
                "qualAnalytics": []
            }
        )

        # Atualiza a métrica "Acedeu à atividade".
        quant_list = [
            qa for qa in student_analytics["quantAnalytics"]
            if qa["name"] != "Acedeu à atividade"
        ]

        quant_list.append({
            "name": "Acedeu à atividade",
            "value": True
        })

        student_analytics["quantAnalytics"] = quant_list

        # Atualiza o progresso caso esse valor esteja presente nos dados recebidos.
        if "progresso" in event_data:
            quant_list = [
                qa for qa in student_analytics["quantAnalytics"]
                if qa["name"] != "Progresso (%)"
            ]

            quant_list.append({
                "name": "Progresso (%)",
                "value": event_data["progresso"]
            })

            student_analytics["quantAnalytics"] = quant_list

        # Guarda o registo atualizado no repositório.
        self._data[activity_id][invenira_std_id] = student_analytics

    def get_activity_analytics(self, activity_id: str):
        # Devolve a lista de analytics referentes à atividade indicada.
        if activity_id not in self._data:
            return []
        return list(self._data[activity_id].values())


# ============================================================
#  ENDPOINTS DA INVEN!RA
# ============================================================

@app.get("/")
def root():
    # Endpoint simples para verificar se o Activity Provider está ativo.
    return "CyberAware Activity Provider – Flask is running!"


@app.get("/config")
def config():
    # Página HTML de configuração fornecida à Inven!RA.
    html = (
        "<!DOCTYPE html><html lang='pt'><head>"
        "<meta charset='UTF-8' />"
        "<title>CyberAware – Configuração</title>"
        "</head><body>"
        "<h2>Configuração da atividade CyberAware</h2>"
        "<label>Duração (minutos): "
        "<input type='number' name='duracao' value='15'></label><br><br>"
        "<label>Nível de dificuldade:"
        "<select name='dificuldade'>"
        "<option value='easy'>Fácil</option>"
        "<option value='medium' selected>Médio</option>"
        "<option value='hard'>Difícil</option>"
        "</select></label><br><br>"
        "<label>Instruções para o aluno:<br>"
        "<textarea name='instrucoes' rows='4' cols='50'>Introdução à atividade CyberAware.</textarea>"
        "</label>"
        "</body></html>"
    )
    return html


@app.get("/json-params")
def json_params():
    # Lista dos parâmetros que a Inven!RA deve recolher da página de configuração.
    params = [
        {"name": "duracao", "type": "integer"},
        {"name": "dificuldade", "type": "text/plain"},
        {"name": "instrucoes", "type": "text/plain"},
    ]
    return jsonify(params)


@app.get("/deploy")
def deploy():
    # Regista a instância da atividade e devolve o URL que será usado para iniciar a experiência.
    activity_id = request.args.get("activityID", "")

    repo = AnalyticsRepository.get_instance()
    repo.register_activity(activity_id)

    # URL que a Inven!RA irá usar posteriormente para o "Provide activity".
    deploy_url = f"https://cyberaware-ap.onrender.com/play?activityID={activity_id}"

    # A especificação aceita que o resultado seja uma string com o URL.
    return deploy_url


@app.get("/analytics-list")
def analytics_list():
    # Lista de analytics disponíveis que podem ser associados aos objetivos do IAP.
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


@app.post("/analytics")
def analytics():
    # Devolve os analytics recolhidos para todos os estudantes de uma instância da atividade.
    body = request.get_json(silent=True) or {}
    activity_id = body.get("activityID", "")

    repo = AnalyticsRepository.get_instance()
    analytics_list = repo.get_activity_analytics(activity_id)

    return jsonify(analytics_list)


# ============================================================
#  ENDPOINT EXTRA (simulação do acesso do estudante)
#  Útil para alimentar o repositório com dados reais durante testes.
# ============================================================

@app.get("/play")
def play():
    activity_id = request.args.get("activityID", "unknown")
    user_id = request.args.get("user", "1001")

    repo = AnalyticsRepository.get_instance()
    repo.register_student_event(activity_id, user_id, {"accessed": True})

    return f"Aluno {user_id} iniciou a atividade {activity_id}."


# ============================================================
#  MAIN (apenas para execução local)
# ============================================================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
