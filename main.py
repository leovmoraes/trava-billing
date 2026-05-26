import base64
import json
import os
import functions_framework
from google.cloud import billing_v1

# Inicializa o cliente de Billing globalmente
client = billing_v1.CloudBillingClient()

@functions_framework.cloud_event
def disable_billing(cloud_event):
    """Acionada via Pub/Sub para desativar o faturamento."""
    
    try:
        # Decodifica o payload do Pub/Sub (Padrão CloudEvent/Gen2)
        pubsub_data = base64.b64decode(cloud_event.data["message"]["data"]).decode("utf-8")
        data = json.loads(pubsub_data)
        
        cost = data.get('costAmount', 0)
        budget = data.get('budgetAmount', 0)
        budget_display_name = data.get('budgetDisplayName', "")
        
        # Extrai o ID do projeto removendo o prefixo padronizado
        if budget_display_name.startswith("trava-billing-"):
            project_id = budget_display_name.replace("trava-billing-", "")
        else:
            project_id = budget_display_name

        print(f"📊 Monitoramento: Projeto {project_id} | Gasto: {cost} | Limite: {budget}")

        if cost >= budget:
            # Verifica se está em modo simulação (Default: true)
            simulate = os.environ.get("SIMULATE_DEACTIVATION", "true").lower() == "true"
            
            if simulate:
                print(f"⚠️ MODO SIMULAÇÃO: O faturamento de '{project_id}' SERIA desativado.")
                return "Simulação: Nenhuma ação tomada."

            # Ação Real: Desvincular Billing
            print(f"🚨 LIMITE EXCEDIDO: Removendo billing de {project_id}...")
            project_name = f"projects/{project_id}"
            client.update_project_billing_info(name=project_name, project_billing_info={"billing_account_name": ""})
            print(f"✅ Projeto {project_id} desconectado com sucesso.")
        
        else:
            print(f"✅ Gasto em {cost} dentro do limite de {budget}.")

    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        return f"Erro: {str(e)}", 500

    return "OK", 200
