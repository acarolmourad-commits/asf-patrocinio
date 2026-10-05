# ASF — Monitor de Respostas de Parceria

GitHub Action que roda a cada 6h (ou manualmente via **Actions → Run workflow**) e:

1. Busca no Gmail (asf.surffeminino@gmail.com) respostas dos 32 leads prospectados (desde 05/10/2026);
2. Classifica a intenção da resposta: **positiva**, **reunião**, **dúvida** ou **negativa**;
3. Gera uma resposta personalizada por lead e cria um **rascunho na thread** para revisão humana;
4. Se a variable `AUTO_SEND=true` estiver definida no repo, envia a resposta automaticamente.

## Configuração (Secrets do repositório)
Crie um OAuth Client no Google Cloud (Gmail API, escopo `gmail.modify`) e gere um refresh token para asf.surffeminino@gmail.com. Depois adicione em **Settings → Secrets and variables → Actions**:

| Nome | Tipo |
|---|---|
| `GMAIL_CLIENT_ID` | Secret |
| `GMAIL_CLIENT_SECRET` | Secret |
| `GMAIL_REFRESH_TOKEN` | Secret |
| `AUTO_SEND` (`true`/`false`) | Variable |

## Arquivos
- `.github/workflows/asf-email-monitor.yml` — workflow agendado
- `scripts/monitor_respostas.py` — lógica de monitoramento, classificação e resposta
- `data/leads.json` — base de leads do funil (32 contatados em 05/10/2026)

> Padrão seguro: respostas viram **rascunhos** — a equipe revisa e envia. Ative `AUTO_SEND` apenas quando o fluxo estiver validado.
