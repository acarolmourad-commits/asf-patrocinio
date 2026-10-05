"""ASF — Monitor de respostas de parceria (via Composio API).

PLAYBOOK DE NEGOCIAÇÃO (100% por e-mail — NUNCA sugerir WhatsApp):
1. Resposta do lead → classifica intenção (positiva/reuniao/duvida/negativa);
2. Positiva/dúvida → envia proposta completa (app ASF, logo no app, redes
   sociais, período de 6 meses) + pede dados empresariais;
3. Aceite → agradece, confirma benefício acordado e solicita dados para
   contrato (razão social, CNPJ, responsável, endereço, e-mail/telefone);
4. Dados recebidos → marcar lead como 'contrato_pendente' no relatório
   (a geração do contrato usa o modelo no Notion CRM).

Configuração no repo:
  Secret:   COMPOSIO_API_KEY
  Variable: COMPOSIO_USER_ID (padrão 'default')
  Variable: AUTO_SEND ('true' = envio automático; padrão = rascunho)
"""
import json, os, re, requests

API = 'https://backend.composio.dev/api/v3'
KEY = os.environ['COMPOSIO_API_KEY']
USER = os.environ.get('COMPOSIO_USER_ID', 'default')
AUTO_SEND = os.environ.get('AUTO_SEND', '').lower() == 'true'
CC = 'asf.surffeminino@gmail.com'
SINCE = '2026/10/05'

H = {'x-api-key': KEY, 'Content-Type': 'application/json'}

with open('data/leads.json') as f:
    LEADS = json.load(f)

POS = ['parceria', 'topamos', 'vamos conversar', 'interesse', 'adorei', 'adoramos', 'podemos', 'informações', 'informacoes']
MEET = ['call', 'reunião', 'reuniao', 'agendar', 'horário', 'horario']
ACCEPT = ['aceito', 'aceitamos', 'fechado', 'concordo', 'concordamos', 'vamos fechar', 'assinamos', 'segue os dados', 'seguem os dados']
NEG = ['não temos interesse', 'no momento não', 'infelizmente não', 'desculpa']
CNPJ = re.compile(r'\d{2}[.]?\d{3}[.]?\d{3}[/]?\d{4}[-]?\d{2}')

def composio(tool, args):
    r = requests.post(f'{API}/tools/execute/{tool}',
                      headers=H,
                      json={'user_id': USER, 'arguments': args},
                      timeout=60)
    r.raise_for_status()
    return r.json()

def classify(text):
    t = (text or '').lower()
    if any(k in t for k in NEG): return 'negativa'
    if CNPJ.search(t) or any(k in t for k in ACCEPT): return 'aceite'
    if any(k in t for k in MEET): return 'reuniao'
    if any(k in t for k in POS): return 'positiva'
    return 'duvida'

APP_TXT = ("A ASF — Associação Surf Feminino (asf.surf) é a rede digital das mulheres que surfam no "
           "Brasil. Nosso app próprio reúne guia de praias, previsão de ondas, checklist de surf, "
           "diário de sessões, ranking da comunidade e a seção Parceiras & Benefícios, onde a logo "
           "da sua marca fica exposta de forma permanente para toda a base de associadas.")

def proposta(nome):
    return (f"Olá, equipe {nome}!\n\n{APP_TXT}\n\n"
            "**PROPOSTA DE PARCERIA**\n\nO que a ASF oferece:\n"
            "1. Logo da marca em destaque na seção Parceiras & Benefícios do app ASF;\n"
            "2. Divulgação nas nossas redes sociais (post de lançamento + menções mensais);\n"
            "3. Indicação ativa à comunidade de associadas (app, e-mail e eventos).\n\n"
            "O que pedimos em contrapartida:\n"
            "1. Benefício exclusivo para associadas ASF (desconto/condição especial);\n"
            "2. Divulgação da ASF nos canais da marca;\n"
            "3. Ação ou conteúdo conjunto mensal (formato a combinar).\n\n"
            "PERÍODO: 6 meses, renovável automaticamente; rescisão com 30 dias de aviso, sem multa.\n\n"
            "Se concordarem, o próximo passo é o contrato simples. Para isso, pedimos:\n"
            "- Razão social e CNPJ\n- Nome do responsável legal\n- Endereço comercial\n"
            "- E-mail e telefone oficiais\n\nPreferimos seguir por e-mail para manter tudo documentado.\n\n"
            "Abraços,\nCarol — ASF\nasf.surffeminino@gmail.com | asf.surf")

def aceite(nome):
    return (f"Olá, equipe {nome}!\n\nQue notícia ótima — parceria aceita! 🎉\n\n"
            "Para formalizarmos, seguiremos com um contrato simples de parceria (vigência de 6 meses, "
            "renovável, sem multa rescisória). Por favor, confirmem os dados empresariais:\n"
            "- Razão social e CNPJ\n- Nome do responsável legal\n- Endereço comercial\n"
            "- E-mail e telefone oficiais\n"
            "- Benefício acordado para associadas ASF (ex.: % de desconto, cupom, condição)\n\n"
            "Assim que recebermos, enviamos o contrato para assinatura e já preparamos o post de "
            "lançamento da parceria nas nossas redes + a inclusão da logo no app.\n\n"
            "Abraços,\nCarol — ASF")

def reply_body(nome, intent):
    if intent == 'aceite': return aceite(nome)
    if intent in ('positiva', 'reuniao', 'duvida'): return proposta(nome)
    return (f"Olá, equipe {nome}!\n\nAgradecemos muito o retorno e a sinceridade. "
            "Se fizer sentido no futuro, estamos à disposição. Sucesso!\n\nAbraços,\nEquipe ASF")

report = []
for lead in LEADS:
    res = composio('GMAIL_FETCH_EMAILS', {
        'query': f"from:{lead['email']} after:{SINCE}",
        'max_results': 10, 'verbose': True})
    msgs = (res.get('data') or {}).get('messages') or []
    for m in msgs:
        if CC in (m.get('sender') or ''):
            continue
        intent = classify(m.get('messageText') or m.get('snippet'))
        subject = m.get('subject') or f"Parceria ASF x {lead['nome']}"
        if not subject.lower().startswith('re:'):
            subject = 'Re: ' + subject
        args = {'recipient_email': lead['email'], 'cc': [CC],
                'body': reply_body(lead['nome'], intent),
                'thread_id': m.get('threadId')}
        if AUTO_SEND:
            args['subject'] = subject
            composio('GMAIL_SEND_EMAIL', args)
            acao = 'ENVIADO'
        else:
            composio('GMAIL_CREATE_EMAIL_DRAFT', args)
            acao = 'RASCUNHO'
        report.append({'lead': lead['nome'], 'intent': intent, 'acao': acao,
                       'proximo': 'gerar_contrato' if intent == 'aceite' else 'aguardar'})

print(json.dumps(report, ensure_ascii=False, indent=2))
if not report:
    print('Nenhuma resposta nova dos leads.')
