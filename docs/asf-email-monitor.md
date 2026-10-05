# ASF — Monitor de Respostas de Parceria

GitHub Action que roda a cada 6h (ou manualmente via **Actions → Run workflow**) usando a **conexão Gmail já existente no Composio** — sem precisar criar credenciais no Google Cloud.

1. Busca no Gmail (asf.surffeminino@gmail.com) respostas dos 32 leads prospectados (desde 05/10/2026);
2. Classifica a intenção: **positiva**, **reunião**, **dúvida** ou **negativa**;
3. Gera resposta personalizada por lead e cria um **rascunho na thread** para revisão humana;
4. Se a variable `AUTO_SEND=true`, envia automaticamente (modo autônomo até fechar a parceria).

## Configuração (Settings → Secrets and variables → Actions)

| Nome | Tipo | Valor |
|---|---|---|
| `COMPOSIO_API_KEY` | Secret | Sua API key do Composio (dashboard.composio.dev) |
| `COMPOSIO_USER_ID` | Variable | ID/e-mail do usuário Composio dono da conexão Gmail (padrão: `default`) |
| `AUTO_SEND` | Variable | `false` = rascunhos para revisão; `true` = envio automático |

## Arquivos
- `.github/workflows/asf-email-monitor.yml` — workflow agendado (a cada 6h)
- `scripts/monitor_respostas.py` — monitoramento + classificação + resposta via Composio API
- `data/leads.json` — base dos 32 leads contactados em 05/10/2026

> Padrão seguro: respostas viram **rascunhos** — a equipe revisa e envia. Ative `AUTO_SEND` quando o fluxo estiver validado.
