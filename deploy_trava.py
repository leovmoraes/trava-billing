import subprocess
import sys
import json
import os
import time

def run_cmd(cmd, desc="", ignore_exists=True):
    if desc: print(f"⚙️  {desc}...")
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if res.returncode != 0:
        error_msg = res.stderr.lower()
        # Se for erro de "Já existe", apenas ignoramos se ignore_exists for True
        if ignore_exists and ("already exists" in error_msg or "conflict" in error_msg):
            if desc: print(f"➡️  Já configurado. Pulando...")
            return "ALREADY_EXISTS"
        
        # Para qualquer outro erro, PARA TUDO e mostra o erro real
        print(f"\n❌ ERRO FATAL EM: {desc}")
        print(f"DETALHE TÉCNICO: {res.stderr}")
        print("\n🛡️ O deploy foi interrompido por segurança. O projeto NÃO está protegido.")
        sys.exit(1)
        
    return res.stdout.strip()

def main():
    print("\n" + "="*75)
    print("🛡️  TRAVA BILLING DEPLOYER - AVISO DE SEGURANÇA CRÍTICO")
    print("="*75)
    print("ESSE DEPLOY NÃO É RECOMENDADO PARA AMBIENTES DE PRODUÇÃO CRÍTICOS,")
    print("POIS ELE DESABILITA TODOS OS RECURSOS E PODE ACARRETAR EM:")
    print("1. PERDA DE DADOS (DISCOS RÍGIDOS E MEMÓRIA EFÊMERA)")
    print("2. IMPACTOS FINANCEIROS POR INDISPONIBILIDADE")
    print("3. PARADA TOTAL DAS APLICAÇÕES E SERVIÇOS")
    print("\nSE VOCÊ ESTÁ DE ACORDO E CIENTE DOS RISCOS,")
    print("DIGITE 'ESTOU DE ACORDO' PARA CONTINUAR.")
    print("="*75)
    
    if input("\nConfirmação: ") != "ESTOU DE ACORDO":
        print("🛑 Execução cancelada pelo usuário."); sys.exit(1)

    # --- FASE 1: IDENTIFICAÇÃO ---
    curr = run_cmd("gcloud config get-value project", "Detectando projeto ativo")
    project_id = input(f"\nID do projeto [{curr}] (Enter para confirmar): ").strip() or curr

    # --- FASE 2: HABILITAÇÃO DE APIs (Check Automático) ---
    # Ativamos as APIs antes de validar faturamento para evitar que o script trave
    print("\n🚀 Preparando o terreno (Habilitando APIs necessárias)...")
    apis = (
        "cloudbilling.googleapis.com billingbudgets.googleapis.com "
        "pubsub.googleapis.com eventarc.googleapis.com run.googleapis.com "
        "cloudfunctions.googleapis.com cloudbuild.googleapis.com iam.googleapis.com"
    )
    run_cmd(f"gcloud services enable {apis} --project={project_id}", "Habilitando APIs (Billing, Run, Eventarc, etc)")
    
    print("⏳ Aguardando propagação das APIs...")
    time.sleep(5) 

    # --- FASE 3: VALIDAÇÃO DE PERMISSÕES (FAIL-FAST) ---
    print("\n🔍 Validando permissões de administrador...")
    run_cmd(f"gcloud projects get-iam-policy {project_id}", "Validando acesso ao projeto", ignore_exists=False)
    
    billing_res = run_cmd(f"gcloud beta billing projects describe {project_id} --format='value(billingAccountName)'", "Checando conta de faturamento")
    if not billing_res or billing_res == "None":
        print(f"❌ ERRO: O projeto {project_id} não possui uma conta de faturamento vinculada.")
        sys.exit(1)
    
    billing_id = billing_res.split('/')[-1]
    run_cmd(f"gcloud billing budgets list --billing-account={billing_id} --limit=1", "Validando acesso ao faturamento")
        
    print("✅ Permissões validadas! Iniciando infraestrutura...")
    limit = input("\nQual o limite de gastos desejado (R$)? ")

    # --- FASE 4: IDENTIDADE E ACESSO ---
    sa_email = f"trava-billing-sa@{project_id}.iam.gserviceaccount.com"
    run_cmd(f"gcloud iam service-accounts create trava-billing-sa --project={project_id}", "Criando Service Account")
    
    run_cmd(f"gcloud projects add-iam-policy-binding {project_id} --member='serviceAccount:{sa_email}' --role='roles/billing.projectManager'", "Atribuindo Billing Manager")
    
    # IMPORTANTE: Binding de Billing User na Conta Pai para funcionamento da Gen2
    run_cmd(f"gcloud billing accounts add-iam-policy-binding {billing_id} --member='serviceAccount:{sa_email}' --role='roles/billing.user'", "Atribuindo Billing User na Conta Pai")

    run_cmd(f"gcloud pubsub topics create trava-billing-topic --project={project_id}", "Criando Tópico Pub/Sub")

    # --- FASE 5: CLOUD FUNCTION (COM CORREÇÃO PARA 404) ---
    print("⚙️  Verificando se a função já existe...")
    check_func_res = subprocess.run(
        f"gcloud functions describe trava-billing-function --region=us-central1 --project={project_id}",
        shell=True, capture_output=True, text=True
    )
    
    do_deploy = True
    if check_func_res.returncode == 0:
        if "ACTIVE" in check_func_res.stdout:
            if input("⚠️  A função já existe e está ATIVA. Deseja atualizar o código? (s/n): ").lower() != 's':
                do_deploy = False
                print("➡️  Mantendo versão atual.")
    else:
        # Se não encontrou (404), apenas avisa e segue para o deploy
        if "not found" in check_func_res.stderr.lower():
            print("➡️  Função não detectada. Iniciando instalação virgem...")
        else:
            print(f"❌ Erro inesperado ao verificar função: {check_func_res.stderr}")
            sys.exit(1)

    if do_deploy:
        print("🚀 Iniciando deploy da Cloud Function Gen2 (Aprox. 2 min)...")
        deploy_cmd = (
            f"gcloud functions deploy trava-billing-function --gen2 --region=us-central1 "
            f"--runtime=python314 --source=. --entry-point=disable_billing "
            f"--trigger-topic=trava-billing-topic --service-account={sa_email} "
            f"--set-env-vars PROJECT_ID={project_id},SIMULATE_DEACTIVATION=false --project={project_id} --quiet"
        )
        run_cmd(deploy_cmd, "Executando deploy")
        run_cmd(f"gcloud run services add-iam-policy-binding trava-billing-function --region=us-central1 --member='allUsers' --role='roles/run.invoker' --project={project_id}", "Liberando Invocador")

    # --- FASE 6: ORÇAMENTO (BUDGET) ---
    budget_info = run_cmd(f"gcloud billing budgets list --billing-account={billing_id} --filter='displayName:trava-billing-{project_id}' --format='json'", "Buscando orçamentos")
    
    if budget_info and budget_info != "[]":
        budget_data = json.loads(budget_info)[0]
        curr_amt = float(budget_data.get('amount', {}).get('specifiedAmount', {}).get('units', 0))
        if curr_amt != float(limit):
            if input(f"⚠️  Orçamento de R$ {curr_amt} detectado. Atualizar para R$ {limit}? (s/n): ").lower() == 's':
                run_cmd(f"gcloud billing budgets update {budget_data['name']} --budget-amount={limit}", "Atualizando valor")
        else: print(f"➡️  Orçamento já está correto.")
    else:
        run_cmd(f"gcloud billing budgets create --billing-account={billing_id} --display-name='trava-billing-{project_id}' --budget-amount={limit} --filter-projects=projects/{project_id} --threshold-rule=percent=1.0,basis=current-spend --notifications-rule-pubsub-topic=projects/{project_id}/topics/trava-billing-topic", "Criando Orçamento Sniper")

    print(f"\n✅ SUCESSO ABSOLUTO! O projeto {project_id} está 100% blindado.\n")

if __name__ == "__main__":
    main()
