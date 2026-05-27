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
3.  **Cloud Functions 2ª Geração**, rodando sobre o Google Cloud Run.
4.  **Segurança**: Uso de Service Accounts com escopo restrito e permissões explícitas de faturamento.
5.  **Protocolo REST**: Comunicação via API Discovery para maior resiliência no desvínculo de billing.

## 📋 Pré-requisitos

* **Google Cloud SDK** (`gcloud`) instalado e autenticado ou rodar no **CloudShell**.
* **Permissões de IAM**: O usuário que executa o deploy precisa ser `Owner` do projeto E `Billing Account Administrator` na conta pai.
* **Service Account**: O script cria automaticamente a `trava-billing-sa` e atribui:
    - No Projeto: `roles/billing.projectManager`
    - Na Billing Account: `roles/billing.user`

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

 a) Leia e aceite o disclaimer de segurança.

 b) Informe o ID do projeto (ou use o ativo).

 d) Defina o limite de gastos em Reais (BRL).

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

## 📚 Referências e Créditos

Este projeto foi inspirado e baseado nos conceitos apresentados no artigo:
* **Automated GCP Killswitch: How to Avoid an Unexpected Google Cloud Bill** por Dazbo (Darren Lester) no Medium.
* https://medium.com/google-cloud/how-to-avoid-a-massive-cloud-bill-41a76251caba

Agradecimento ao autor por compartilhar o conhecimento base sobre automação de Billing no GCP.
