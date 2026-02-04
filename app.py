from flask import Flask, request, jsonify
from abc import ABC, abstractmethod

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
#  STRATEGY: Analytics update behaviors
# ============================================================

class AnalyticsUpdateStrategy(ABC):
    @abstractmethod
    def update(self, repo: AnalyticsRepository, activity_id: str, user_id: str, args) -> None:
        """Atualiza analytics para um evento de acesso/execução."""
        raise NotImplementedError


class SimpleAccessStrategy(AnalyticsUpdateStrategy):
    """Registo mínimo: apenas assinala que o aluno acedeu à atividade."""
    def update(self, repo: AnalyticsRepository, activity_id: str, user_id: str, args) -> None:
        repo.register_student_event(activity_id, user_id, {"accessed": True})


class ProgressAccessStrategy(AnalyticsUpdateStrategy):
    """Registo com progresso: assinala acesso e atualiza Progresso (%), se possível."""
    def update(self, repo: AnalyticsRepository, activity_id: str, user_id: str, args) -> None:
        progresso_raw = args.get("progresso")
        if progresso_raw is None or progresso_raw == "":
            repo.register_student_event(activity_id, user_id, {"accessed": True})
            return

        try:
            progresso = int(progresso_raw)
        except (ValueError, TypeError):
            repo.register_student_event(activity_id, user_id, {"accessed": True})
            return

        # clamp 0..100
        if progresso < 0:
            progresso = 0
        if progresso > 100:
            progresso = 100

        repo.register_student_event(activity_id, user_id, {"accessed": True, "progresso": progresso})


# ============================================================
#  EXTRAÇÃO (refatorização Blob): serviços dedicados
# ============================================================

class ActivityConfigService:
    """Responsável apenas por configuração e parâmetros (retira carga da Facade)."""

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


class AnalyticsCatalogService:
    """Responsável apenas pelo catálogo/lista de analytics (retira carga da Facade)."""

    def get_analytics_catalog(self):
        return {
            "qualAnalytics": [{"name": "Student activity profile", "type": "URL"}],
            "quantAnalytics": [
                {"name": "Acedeu à atividade", "type": "boolean"},
                {"name": "Progresso (%)", "type": "integer"},
            ],
        }


# ============================================================
#  FACADE: CyberAwareFacade
#  (agora mais leve: delega config e catálogo)
# ============================================================

class CyberAwareFacade:
    def __init__(self, base_url: str, config_service: ActivityConfigService, catalog_service: AnalyticsCatalogService):
        self.base_url = base_url
        self.repo = AnalyticsRepository.get_instance()

        self.config_service = config_service
        self.catalog_service = catalog_service

        self._strategies = {
            "simple": SimpleAccessStrategy(),
            "progress": ProgressAccessStrategy(),
        }

    def get_root_message(self) -> str:
        return "CyberAware Activity Provider – Flask is running!"

    # Delegações (retira responsabilidade da Facade)
    def get_config_html(self) -> str:
        return self.config_service.get_config_html()

    def get_json_params(self):
        return self.config_service.get_json_params()

    def get_analytics_catalog(self):
        return self.catalog_service.get_analytics_catalog()

    def prepare_deploy(self, activity_id: str) -> str:
        self.repo.register_activity(activity_id)
        return f"{self.base_url}/play?activityID={activity_id}"

    def _select_strategy(self, mode: str, args) -> AnalyticsUpdateStrategy:
        mode_norm = (mode or "").strip().lower()
        if mode_norm in self._strategies:
            return self._strategies[mode_norm]

        if args.get("progresso") not in (None, ""):
            return self._strategies["progress"]

        return self._strategies["simple"]

    def record_student_access(self, activity_id: str, user_id: str, mode: str, args) -> str:
        strategy = self._select_strategy(mode, args)
        strategy.update(self.repo, activity_id, user_id, args)

        mode_norm = (mode or "").strip().lower()
        if mode_norm not in ("simple", "progress"):
            mode_norm = "progress" if args.get("progresso") not in (None, "") else "simple"

        return f"Aluno {user_id} iniciou a atividade {activity_id} (mode={mode_norm})."

    def get_analytics(self, activity_id: str):
        return self.repo.get_activity_analytics(activity_id)


# ============================================================
#  Instâncias (injeção simples)
# ============================================================

CONFIG_SERVICE = ActivityConfigService()
CATALOG_SERVICE = AnalyticsCatalogService()

FACADE = CyberAwareFacade(
    base_url="https://cyberaware-ap.onrender.com",
    config_service=CONFIG_SERVICE,
    catalog_service=CATALOG_SERVICE,
)


# ============================================================
#  ENDPOINTS (finos)
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


@app.get("/play")
def play():
    activity_id = request.args.get("activityID", "unknown")
    user_id = request.args.get("user", "1001")
    mode = request.args.get("mode", "simple")
    return FACADE.record_student_access(activity_id, user_id, mode, request.args)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
