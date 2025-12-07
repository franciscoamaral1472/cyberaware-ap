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
        quant_list = [qa for qa in student_analytics["quantAnalytics"]
                      if qa["name"] != "Acedeu à atividade"]

        quant_list.append({
            "name": "Acedeu à atividade",
            "value": True
        })

        student_analytics["quantAnalytics"] = quant_list

        # Atualiza o progresso caso esse valor esteja presente nos dados recebidos.
        if "progresso" in event_data:
            quant_list = [qa for qa in student_analytics["quantAnalytics"]
                          if qa["name"] != "Progresso (%)"]

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
