import base64
import json
import os
import functions_framework
from googleapiclient import discovery
from oauth2client.client import GoogleCredentials

@functions_framework.cloud_event
def disable_billing(cloud_event):
    # 1. Decodifica os dados do Pub/Sub
    try:
        pubsub_message = base64.b64decode(cloud_event.data["message"]["data"]).decode("utf-8")
        data = json.loads(pubsub_message)
    except Exception as e:
        print(f"❌ Erro ao decodificar mensagem: {e}")
        return

    # 2. Extrai valores (Gasto atual e Limite definido)
    cost_amount = data.get("costAmount", 0.0)
    budget_amount = data.get("budgetAmount", 0.0)
    
    # 3. Identifica o Projeto
    project_id = os.environ.get("PROJECT_ID")
    if not project_id:
        # Fallback para extrair do caminho do recurso se a env var falhar
        project_id = cloud_event.get("source", "").split("/")[-1]

    # LOG MELHORADO: O que você pediu
    print(f"📊 Monitoramento: {project_id} | Gasto: {cost_amount} / Limite: {budget_amount}")

    # 4. Lógica de Decisão
    if cost_amount <= budget_amount:
        print(f"✅ Gasto dentro do limite. Nenhuma ação necessária.")
        return

    # 5. Modo Matador ou Simulação
    if os.environ.get("SIMULATE_DEACTIVATION") == "false":
        print(f"🚨 Limite excedido! Desconectando faturamento de projects/{project_id}...")
        try:
            credentials = GoogleCredentials.get_application_default()
            billing = discovery.build("cloudbilling", "v1", credentials=credentials)
            billing.projects().updateBillingInfo(
                name=f"projects/{project_id}", 
                body={"billingAccountName": ""}
            ).execute()
            print(f"✅ SUCESSO: Projeto {project_id} desconectado.")
        except Exception as e:
            print(f"❌ ERRO ao tentar desconectar: {e}")
    else:
        print(f"⚠️ MODO SIMULAÇÃO: O projeto {project_id} seria desconectado agora.")
