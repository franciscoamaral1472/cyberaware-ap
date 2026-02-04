# Arquitetura e Padrões de Software 2025
# CyberAware-AP
# Francisco Amaral - 1802876


from flask import Flask, request, jsonify
from abc import ABC, abstractmethod

# Flask app: este é o “ponto de entrada” do serviço REST do Activity Provider.
app = Flask(__name__)


# ============================================================
#  SINGLETON: AnalyticsRepository
# ============================================================
# Objetivo: guardar (em memória) os analytics por activityID e por aluno.
# Padrão Singleton: garante que toda a aplicação usa o MESMO repositório,
# evitando inconsistências (ex.: cada endpoint criar “um repositório diferente”).
class AnalyticsRepository:
    _instance = None

    def __init__(self):
        # Estrutura em memória:
        # { activityID: { inveniraStdID: { inveniraStdID, quantAnalytics, qualAnalytics } } }
        self._data = {}

    @classmethod
    def get_instance(cls):
        # Cria a instância uma única vez e reutiliza-a para todos os pedidos.
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register_activity(self, activity_id: str) -> None:
        # Garante que existe uma “zona” para a atividade antes de registar eventos.
        if activity_id and activity_id not in self._data:
            self._data[activity_id] = {}

    def register_student_event(self, activity_id: str, invenira_std_id: str, event_data: dict) -> None:
        # Primeiro, garante-se que a atividade está registada.
        self.register_activity(activity_id)

        # Se o aluno ainda não tiver registo, cria a estrutura base esperada pela Inven!RA.
        student_analytics = self._data[activity_id].get(
            invenira_std_id,
            {"inveniraStdID": invenira_std_id, "quantAnalytics": [], "qualAnalytics": []}
        )

        # Atualiza/insere o indicador “Acedeu à atividade”
        # (mantém-se apenas uma entrada com este nome, evitando duplicados).
        quant_list = [qa for qa in student_analytics["quantAnalytics"] if qa["name"] != "Acedeu à atividade"]
        quant_list.append({"name": "Acedeu à atividade", "value": True})
        student_analytics["quantAnalytics"] = quant_list

        # Se houver progresso, atualiza também a métrica “Progresso (%)”.
        if "progresso" in event_data:
            quant_list = [qa for qa in student_analytics["quantAnalytics"] if qa["name"] != "Progresso (%)"]
            quant_list.append({"name": "Progresso (%)", "value": int(event_data["progresso"])})
            student_analytics["quantAnalytics"] = quant_list

        # Guarda (ou sobrescreve) o estado do aluno na atividade.
        self._data[activity_id][invenira_std_id] = student_analytics

    def get_activity_analytics(self, activity_id: str):
        # Devolve a lista de alunos (cada item já no formato esperado pela Inven!RA).
        if activity_id not in self._data:
            return []
        return list(self._data[activity_id].values())


# ============================================================
#  STRATEGY: Analytics update behaviors
# ============================================================
# Objetivo: encapsular comportamentos diferentes de registo de analytics.
# Em vez de encher a Facade de “ifs”, cada comportamento fica isolado numa Strategy.
class AnalyticsUpdateStrategy(ABC):
    @abstractmethod
    def update(self, repo: AnalyticsRepository, activity_id: str, user_id: str, args) -> None:
        """Contrato comum: atualizar analytics para um evento de acesso/execução."""
        raise NotImplementedError


class SimpleAccessStrategy(AnalyticsUpdateStrategy):
    """Registo mínimo: apenas assinala que o aluno acedeu à atividade."""
    def update(self, repo: AnalyticsRepository, activity_id: str, user_id: str, args) -> None:
        repo.register_student_event(activity_id, user_id, {"accessed": True})


class ProgressAccessStrategy(AnalyticsUpdateStrategy):
    """Registo com progresso: assinala acesso e atualiza Progresso (%), se possível."""
    def update(self, repo: AnalyticsRepository, activity_id: str, user_id: str, args) -> None:
        # O parâmetro “progresso” pode vir (ou não) no pedido.
        progresso_raw = args.get("progresso")
        if progresso_raw is None or progresso_raw == "":
            # Sem progresso fornecido: não falha, apenas regista acesso simples.
            repo.register_student_event(activity_id, user_id, {"accessed": True})
            return

        # Se o progresso vier inválido, volta ao registo simples (resiliência).
        try:
            progresso = int(progresso_raw)
        except (ValueError, TypeError):
            repo.register_student_event(activity_id, user_id, {"accessed": True})
            return

        # Normaliza o progresso para a faixa 0..100 (evita valores absurdos).
        if progresso < 0:
            progresso = 0
        if progresso > 100:
            progresso = 100

        repo.register_student_event(activity_id, user_id, {"accessed": True, "progresso": progresso})


# ============================================================
#  EXTRAÇÃO (refatorização Blob): serviços dedicados
# ============================================================
# Aqui está a refatorização do antipadrão Blob:
# a Facade tinha “demasiadas responsabilidades” e parte delas foi extraída
# para serviços específicos e coesos.

class ActivityConfigService:
    """Responsável apenas por configuração e parâmetros (alivia a Facade)."""

    def get_config_html(self) -> str:
        # HTML simples de configuração: a Inven!RA carrega esta página na UI.
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
        # Lista de parâmetros configuráveis (formato esperado pela Inven!RA).
        return [
            {"name": "duracao", "type": "integer"},
            {"name": "dificuldade", "type": "text/plain"},
            {"name": "instrucoes", "type": "text/plain"},
        ]


class AnalyticsCatalogService:
    """Responsável apenas pelo catálogo/lista de analytics (alivia a Facade)."""

    def get_analytics_catalog(self):
        # Define o “catálogo” (o que a plataforma pode esperar receber depois).
        return {
            "qualAnalytics": [{"name": "Student activity profile", "type": "URL"}],
            "quantAnalytics": [
                {"name": "Acedeu à atividade", "type": "boolean"},
                {"name": "Progresso (%)", "type": "integer"},
            ],
        }


# ============================================================
#  FACADE: CyberAwareFacade
# ============================================================
# A Facade é o “ponto de coordenação”: endpoints finos delegam nela.
# Após a refatorização do Blob, a Facade deixa de “fazer tudo” e passa a delegar
# a configuração e o catálogo de analytics em serviços dedicados (mais coesão).
# Além disso, a Facade atua como Context do Strategy.
class CyberAwareFacade:
    def __init__(self, base_url: str, config_service: ActivityConfigService, catalog_service: AnalyticsCatalogService):
        self.base_url = base_url

        # Repositório partilhado (Singleton).
        self.repo = AnalyticsRepository.get_instance()

        # Serviços extraídos (refatorização do Blob).
        self.config_service = config_service
        self.catalog_service = catalog_service

        # Estratégias disponíveis (extensível no futuro).
        self._strategies = {
            "simple": SimpleAccessStrategy(),
            "progress": ProgressAccessStrategy(),
        }

    def get_root_message(self) -> str:
        return "CyberAware Activity Provider – Flask is running!"

    # Delegação clara: a Facade não gera o HTML nem a lista de params; o serviço faz isso.
    def get_config_html(self) -> str:
        return self.config_service.get_config_html()

    def get_json_params(self):
        return self.config_service.get_json_params()

    # Delegação clara: o catálogo de analytics fica num componente dedicado.
    def get_analytics_catalog(self):
        return self.catalog_service.get_analytics_catalog()

    def prepare_deploy(self, activity_id: str) -> str:
        # “Deploy” aqui significa preparar a estrutura para a atividade e devolver URL de execução.
        self.repo.register_activity(activity_id)
        return f"{self.base_url}/play?activityID={activity_id}"

    def _select_strategy(self, mode: str, args) -> AnalyticsUpdateStrategy:
        # Seleção da Strategy:
        # 1) Se o modo for válido (“simple”/“progress”), respeita-o.
        # 2) Caso contrário, se houver progresso, escolhe “progress”.
        # 3) Default: “simple”.
        mode_norm = (mode or "").strip().lower()
        if mode_norm in self._strategies:
            return self._strategies[mode_norm]

        if args.get("progresso") not in (None, ""):
            return self._strategies["progress"]

        return self._strategies["simple"]

    def record_student_access(self, activity_id: str, user_id: str, mode: str, args) -> str:
        # Aplica a Strategy escolhida para registar analytics de acordo com o contexto do pedido.
        strategy = self._select_strategy(mode, args)
        strategy.update(self.repo, activity_id, user_id, args)

        # Mensagem simples: útil para confirmar rapidamente o comportamento durante testes.
        mode_norm = (mode or "").strip().lower()
        if mode_norm not in ("simple", "progress"):
            mode_norm = "progress" if args.get("progresso") not in (None, "") else "simple"

        return f"Aluno {user_id} iniciou a atividade {activity_id} (mode={mode_norm})."

    def get_analytics(self, activity_id: str):
        # Devolve os analytics de uma atividade no formato esperado pela Inven!RA.
        return self.repo.get_activity_analytics(activity_id)


# ============================================================
#  Instâncias (injeção simples)
# ============================================================
# Instâncias “singletons” ao nível do módulo (não é o mesmo que o Singleton do repositório):
# isto é apenas uma forma simples de wiring/injeção para o projeto.
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
# Endpoints finos: recolhem inputs do request e delegam na Facade.
# Isto mantém a API layer simples e a lógica arquitetural concentrada no núcleo.

@app.get("/")
def root():
    # Health check simples.
    return FACADE.get_root_message()


@app.get("/config")
def config():
    # Página de configuração (HTML).
    return FACADE.get_config_html()


@app.get("/json-params")
def json_params():
    # Parâmetros configuráveis (JSON).
    return jsonify(FACADE.get_json_params())


@app.get("/deploy")
def deploy():
    # “Deploy” lógico: prepara a atividade e devolve o URL de execução.
    activity_id = request.args.get("activityID", "")
    return FACADE.prepare_deploy(activity_id)


@app.get("/analytics-list")
def analytics_list():
    # Catálogo de métricas suportadas (quant/qual).
    return jsonify(FACADE.get_analytics_catalog())


@app.post("/analytics")
def analytics():
    # A Inven!RA envia activityID via JSON e espera receber os analytics agregados.
    body = request.get_json(silent=True) or {}
    activity_id = body.get("activityID", "")
    return jsonify(FACADE.get_analytics(activity_id))


@app.get("/play")
def play():
    # Endpoint de execução/teste: simula o acesso do aluno e gera analytics.
    activity_id = request.args.get("activityID", "unknown")
    user_id = request.args.get("user", "1001")

    # mode define a Strategy (simple/progress). Se progresso existir, pode influenciar seleção.
    mode = request.args.get("mode", "simple")

    return FACADE.record_student_access(activity_id, user_id, mode, request.args)


if __name__ == "__main__":
    # Execução local (em produção, o Render/WSGI geralmente arranca a app).
    app.run(host="0.0.0.0", port=5000)
