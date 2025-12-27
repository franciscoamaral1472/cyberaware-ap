from flask import Flask, request, jsonify

app = Flask(__name__)


# ============================================================
#  SINGLETON: AnalyticsRepository
# ============================================================

class AnalyticsRepository:
    _instance = None

    def __init__(self):
        self._data = {}  # { activityID: { inveniraStdID: analytics_dict } }

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register_activity(self, activity_id: str) -> None:
        if activity_id and activity_id not in self._data:
            self._data[activity_id] = {}

    def register_student_event(self, activity_id: str, invenira_std_id: str, event_data: dict) -> None:
        self.register_activity(activity_id)

        student_analytics = self._data[activity_id].get(
            invenira_std_id,
            {"inveniraStdID": invenira_std_id, "quantAnalytics": [], "qualAnalytics": []}
        )

        # Atualiza "Acedeu à atividade"
        quant_list = [qa for qa in student_analytics["quantAnalytics"] if qa["name"] != "Acedeu à atividade"]
        quant_list.append({"name": "Acedeu à atividade", "value": True})
        student_analytics["quantAnalytics"] = quant_list

        # Atualiza "Progresso (%)" se existir
        if "progresso" in event_data:
            quant_list = [qa for qa in student_analytics["quantAnalytics"] if qa["name"] != "Progresso (%)"]
            quant_list.append({"name": "Progresso (%)", "value": int(event_data["progresso"])})
            student_analytics["quantAnalytics"] = quant_list

        self._data[activity_id][invenira_std_id] = student_analytics

    def get_activity_analytics(self, activity_id: str):
        if activity_id not in self._data:
            return []
        return list(self._data[activity_id].values())


# ============================================================
#  FACADE: CyberAwareFacade
#  Encapsula operações principais do Activity Provider.
# ============================================================

class CyberAwareFacade:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.repo = AnalyticsRepository.get_instance()

    def get_root_message(self) -> str:
        return "CyberAware Activity Provider – Flask is running!"

    def get_config_html(self) -> str:
        return (
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

    def get_json_params(self):
        return [
            {"name": "duracao", "type": "integer"},
            {"name": "dificuldade", "type": "text/plain"},
            {"name": "instrucoes", "type": "text/plain"},
        ]

    def prepare_deploy(self, activity_id: str) -> str:
        # Garante estrutura para a atividade e devolve URL de execução
        self.repo.register_activity(activity_id)
        return f"{self.base_url}/play?activityID={activity_id}"

    def get_analytics_catalog(self):
        return {
            "qualAnalytics": [{"name": "Student activity profile", "type": "URL"}],
            "quantAnalytics": [
                {"name": "Acedeu à atividade", "type": "boolean"},
                {"name": "Progresso (%)", "type": "integer"},
            ],
        }

    def record_student_access(self, activity_id: str, user_id: str) -> str:
        # Demonstração: ao entrar, regista "acedeu"
        self.repo.register_student_event(activity_id, user_id, {"accessed": True})
        return f"Aluno {user_id} iniciou a atividade {activity_id}."

    def get_analytics(self, activity_id: str):
        # Devolve analytics no formato esperado pela Inven!RA
        return self.repo.get_activity_analytics(activity_id)


# Instância única da Facade (usada por todos os endpoints)
FACADE = CyberAwareFacade(base_url="https://cyberaware-ap.onrender.com")


# ============================================================
#  ENDPOINTS (agora finos: delegam na Facade)
# ============================================================

@app.get("/")
def root():
    return FACADE.get_root_message()


@app.get("/config")
def config():
    return FACADE.get_config_html()


@app.get("/json-params")
def json_params():
    return jsonify(FACADE.get_json_params())


@app.get("/deploy")
def deploy():
    activity_id = request.args.get("activityID", "")
    return FACADE.prepare_deploy(activity_id)


@app.get("/analytics-list")
def analytics_list():
    return jsonify(FACADE.get_analytics_catalog())


@app.post("/analytics")
def analytics():
    body = request.get_json(silent=True) or {}
    activity_id = body.get("activityID", "")
    return jsonify(FACADE.get_analytics(activity_id))


# Endpoint extra para teste local e para gerar analytics
@app.get("/play")
def play():
    activity_id = request.args.get("activityID", "unknown")
    user_id = request.args.get("user", "1001")
    return FACADE.record_student_access(activity_id, user_id)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
