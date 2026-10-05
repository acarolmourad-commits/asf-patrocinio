"""ASF — Monitor de respostas de parceria (via Composio API).

Usa a conexão Gmail já existente no Composio (asf.surffeminino@gmail.com) —
não precisa de OAuth próprio no Google Cloud.

Fluxo a cada execução:
1. GMAIL_FETCH_EMAILS: busca respostas dos 32 leads (desde 05/10/2026);
2. Classifica intenção: positiva / reuniao / duvida / negativa;
3. Gera resposta personalizada;
4. GMAIL_CREATE_EMAIL_DRAFT na thread (padrão) ou GMAIL_SEND_EMAIL
   se a variable AUTO_SEND=true.

Configuração no repo:
  Secret:   COMPOSIO_API_KEY
  Variable: COMPOSIO_USER_ID (ex.: e-mail ou ID do usuário Composio; padrão 'default')
  Variable: AUTO_SEND ('true' para envio automático)
"""
import json, os, requests

API = 'https://backend.composio.dev/api/v3'
KEY = os.environ['COMPOSIO_API_KEY']
USER = os.environ.get('COMPOSIO_USER_ID', 'default')
AUTO_SEND = os.environ.get('AUTO_SEND', '').lower() == 'true'
CC = 'asf.surffeminino@gmail.com'
SINCE = '2026/10/05'

H = {'x-api-key': KEY, 'Content-Type': 'application/json'}

with open('data/leads.json') as f:
    LEADS = json.load(f)

POS = ['parceria', 'topamos', 'vamos conversar', 'interesse', 'adorei', 'adoramos', 'podemos']
MEET = ['call', 'reunião', 'reuniao', 'agendar', 'horário', 'horario', 'whatsapp']
NEG = ['não temos interesse', 'no momento não', 'infelizmente não', 'desculpa']

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
    if any(k in t for k in MEET): return 'reuniao'
    if any(k in t for k in POS): return 'positiva'
    return 'duvida'

def reply_body(nome, intent):
    if intent == 'positiva':
        return (f"Olá, equipe {nome}!\n\nQue ótimo! Ficamos muito felizes com o interesse. "
                "Como próximo passo, sugerimos uma call rápida (15–20 min) para alinharmos "
                "formato da parceria, benefícios para associadas ASF e cronograma. "
                "Qual dia/horário funciona para vocês esta semana?\n\nAbraços,\nEquipe ASF")
    if intent == 'reuniao':
        return (f"Olá, equipe {nome}!\n\nPerfeito! Temos disponibilidade nos próximos dias. "
                "Podem indicar 2–3 horários? Em seguida enviamos o convite com o link da call.\n\nAbraços,\nEquipe ASF")
    if intent == 'duvida':
        return (f"Olá, equipe {nome}!\n\nObrigada pelo retorno! A ASF é a Associação de Surf Feminino — "
                "reunimos associadas em todo o Brasil e buscamos parcerias com benefícios mútuos: "
                "divulgação da marca para nossa comunidade, presença em eventos e condições "
                "exclusivas para associadas. Ficamos à disposição para uma call rápida.\n\nAbraços,\nEquipe ASF")
    return (f"Olá, equipe {nome}!\n\nAgradecemos muito o retorno e a sinceridade. "
            "Se fizer sentido no futuro, estamos à disposição. Sucesso!\n\nAbraços,\nEquipe ASF")

report = []
for lead in LEADS:
    res = composio('GMAIL_FETCH_EMAILS', {
        'query': f"from:{lead['email']} after:{SINCE}",
        'max_results': 10, 'verbose': True})
    msgs = (res.get('data') or {}).get('messages') or []
    for m in msgs:
        # ignora mensagens enviadas por nós
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
        report.append({'lead': lead['nome'], 'intent': intent, 'acao': acao})

print(json.dumps(report, ensure_ascii=False, indent=2))
if not report:
    print('Nenhuma resposta nova dos leads.')
