# 🛡️ Trava Billing Deployer

O **Trava Billing Deployer** é uma solução de automação FinOps para Google Cloud Platform (GCP). Ele implementa um "Killswitch" automático que desativa o faturamento de um projeto específico caso um limite de orçamento pré-definido seja atingido.

## 🚀 Funcionalidades

* **Deploy Agnóstico**: O script identifica o projeto ativo ou permite a escolha de um novo ID.
* **Fail-Fast**: Validação rigorosa de permissões de IAM e Billing antes de iniciar qualquer alteração.
* **Idempotência**: Detecta recursos existentes (Service Accounts, Tópicos, Funções e Orçamentos) para evitar duplicidade ou erros.
* **Segurança**: Inclui um disclaimer obrigatório e modo de simulação por padrão.
* **Arquitetura Moderna**: Utiliza Cloud Functions Gen2 e Eventarc para uma resposta rápida e escalável.

## 🏗️ Arquitetura

O sistema é composto por:
1.  **Cloud Billing Budget**: Monitora os custos em tempo real.
2.  **Pub/Sub**: Canal de comunicação que recebe o alerta de estouro.
3.  **Cloud Function (Python)**: Lógica de execução que remove o vínculo de faturamento do projeto.



## 📋 Pré-requisitos

* Google Cloud SDK (`gcloud`) instalado e autenticado.
* Permissões de `Owner` ou `Editor` no projeto alvo.
* Acesso de `Billing Account Administrator` na conta de faturamento vinculada.

## 💻 Como usar

1. Clone o repositório:
   ```bash
   git clone https://github.com/leovmoraes/trava-billing.git
   cd trava-billing
   ```

2. Execute o script de deploy:

```bash
python3 deploy_trava.py
```
3. Siga as instruções no terminal:

* Leia e aceite o disclaimer de segurança.

* Informe o ID do projeto (ou use o ativo).

* Defina o limite de gastos em Reais (BRL).

## ⚠️ Aviso de Segurança

Este script é uma ferramenta poderosa. Ao desativar o faturamento, todos os recursos do projeto (VMs, Bancos de Dados, Clusters) são interrompidos imediatamente. Isso pode causar perda de dados efêmeros e indisponibilidade total dos serviços. Use com cautela e preferencialmente em ambientes de Sandbox ou Lab.

## 🛠️ Reativação
Caso a trava seja acionada, para reativar o projeto:

* Corrija a causa do gasto excessivo.

* Vincule novamente uma conta de faturamento:

```Bash
gcloud billing projects link ID_DO_PROJETO --billing-account=ID_DA_CONTA
```
* Reinicie os serviços manualmente, se necessário.
