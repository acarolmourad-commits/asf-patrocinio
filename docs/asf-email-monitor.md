# ASF — Monitor de Respostas de Parceria

GitHub Action que roda a cada 6h usando a **conexão Gmail já existente no Composio** — sem credenciais no Google Cloud.

## Playbook de negociação (100% por e-mail — nunca WhatsApp)
1. **Resposta do lead** → classificação: positiva / reunião / dúvida / aceite (CNPJ ou "aceitamos") / negativa;
2. **Positiva/dúvida/reunião** → envia proposta completa: explicação do app ASF, logo na seção Parceiras & Benefícios, divulgação em redes sociais, período de 6 meses + pedido de dados empresariais;
3. **Aceite** → confirma, detalha o contrato simples e solicita dados empresariais (razão social, CNPJ, responsável, endereço, contatos, benefício acordado);
4. **Dados recebidos** → marca como `gerar_contrato` no relatório (modelo de contrato no Notion: CRM → "📄 Modelo — Contrato Simples de Parceria ASF");
5. **Negativa** → agradecimento elegante, porta aberta.

## Configuração (Settings → Secrets and variables → Actions)
| Nome | Tipo | Valor |
|---|---|---|
| `COMPOSIO_API_KEY` | Secret | API key do Composio |
| `COMPOSIO_USER_ID` | Variable | `default` ou ID do usuário Composio |
| `AUTO_SEND` | Variable | `false` = rascunhos p/ revisão; `true` = envio automático |

## Arquivos
- `.github/workflows/asf-email-monitor.yml` — workflow (a cada 6h)
- `scripts/monitor_respostas.py` — playbook completo via Composio API
- `data/leads.json` — 32 leads contactados em 05/10/2026
