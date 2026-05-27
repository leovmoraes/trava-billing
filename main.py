import base64
import json
import os
import functions_framework
from googleapiclient import discovery

@functions_framework.cloud_event
def disable_billing(cloud_event):
    try:
        # 1. Parsing dos dados do CloudEvent
        pubsub_message = cloud_event.data["message"]
        pubsub_data = base64.b64decode(pubsub_message["data"]).decode("utf-8")
        data = json.loads(pubsub_data)
        
        # 2. Captura Robusta do Project ID
        # Tenta: Variável de ambiente Gen2, depois Gen1, depois extrai do tópico Pub/Sub
        project_id = os.environ.get('PROJECT_ID') or os.environ.get('GOOGLE_CLOUD_PROJECT')
        
        if not project_id:
            # Se as variáveis falharem, extrai do 'source' do evento
            # formato: //pubsub.googleapis.com/projects/ID_DO_PROJETO/topics/TOPICO
            topic_path = cloud_event.get("source", "")
            if "projects/" in topic_path:
                project_id = topic_path.split("projects/")[1].split("/")[0]

        print(f"📊 Monitoramento: {project_id} | Gasto: {data.get('costAmount')}")

        if not project_id or project_id == "None":
            raise ValueError("Não foi possível identificar o ID do projeto.")

        if data.get('costAmount', 0) >= data.get('budgetAmount', 0):
            if os.environ.get("SIMULATE_DEACTIVATION", "true").lower() == "true":
                print(f"⚠️ MODO SIMULAÇÃO: {project_id} não desligado.")
                return "OK"

            # API DISCOVERY (Mesma lógica do gcloud que funcionou)
            service = discovery.build('cloudbilling', 'v1', cache_discovery=False)
            name = f'projects/{project_id}'
            body = {'billingAccountName': ''} 

            print(f"🚨 Desconectando faturamento de {name}...")
            service.projects().updateBillingInfo(name=name, body=body).execute()
            print(f"✅ SUCESSO: Projeto {project_id} desconectado.")
        
    except Exception as e:
        print(f"❌ Erro fatal: {str(e)}")
        return f"Erro: {str(e)}", 500

    return "OK", 200
