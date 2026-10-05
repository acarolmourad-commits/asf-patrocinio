"""ASF — Monitor de respostas de parceria.

Verifica a caixa do Gmail (asf.surffeminino@gmail.com) por respostas dos leads
de prospecção, classifica a intenção (positiva / dúvida / reunião / negativa),
gera uma resposta personalizada e cria um RASCUNHO de resposta na thread.
Se a variável de repo AUTO_SEND=true, envia diretamente em vez de rascunho.

Secrets necessários (OAuth do Google Cloud com escopo gmail.modify):
  GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET, GMAIL_REFRESH_TOKEN
"""
import json, os, base64
from email.mime.text import MIMEText
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SINCE = '2026/10/05'
CC = 'asf.surffeminino@gmail.com'

with open('data/leads.json') as f:
    LEADS = json.load(f)  # [{"nome": ..., "email": ..., "segmento": ..., "status": "enviado"}]

creds = Credentials(None,
    refresh_token=os.environ['GMAIL_REFRESH_TOKEN'],
    client_id=os.environ['GMAIL_CLIENT_ID'],
    client_secret=os.environ['GMAIL_CLIENT_SECRET'],
    token_uri='https://oauth2.googleapis.com/token')
svc = build('gmail', 'v1', credentials=creds)

POS = ['parceria', 'topamos', 'vamos conversar', 'interesse', 'adorei', 'adoramos', 'sim', 'podemos']
MEET = ['call', 'reunião', 'agendar', 'conversa', 'horário', 'whatsapp']
NEG = ['não temos interesse', 'no momento não', 'desculpa', 'infelizmente não']

def classify(text):
    t = text.lower()
    if any(k in t for k in NEG): return 'negativa'
    if any(k in t for k in MEET): return 'reuniao'
    if any(k in t for k in POS): return 'positiva'
    return 'duvida'

def reply_body(lead, intent):
    n = lead['nome']
    if intent == 'positiva':
        return (f"Olá, equipe {n}!\n\nQue ótimo! Ficamos muito felizes com o interesse. "
                "Como próximo passo, sugerimos uma call rápida (15–20 min) para alinharmos "
                "formato da parceria, benefícios para associadas ASF e cronograma. "
                "Qual dia/horário funciona para vocês esta semana?\n\nAbraços,\nEquipe ASF")
    if intent == 'reuniao':
        return (f"Olá, equipe {n}!\n\nPerfeito! Temos disponibilidade nos próximos dias. "
                "Podem indicar 2–3 horários? Em seguida enviamos o convite com o link da call.\n\nAbraços,\nEquipe ASF")
    if intent == 'duvida':
        return (f"Olá, equipe {n}!\n\nObrigada pelo retorno! A ASF é a Associação de Surf Feminino — "
                "reunimos associadas em todo o Brasil e buscamos parcerias com benefícios mútuos: "
                "divulgação da marca para nossa comunidade, presença em eventos e condições exclusivas "
                "para associadas. Ficamos à disposição para detalhar em uma call rápida.\n\nAbraços,\nEquipe ASF")
    return (f"Olá, equipe {n}!\n\nAgradecemos muito o retorno e a sinceridade. "
            "Se fizer sentido no futuro, estamos à disposição. Sucesso!\n\nAbraços,\nEquipe ASF")

def make_msg(thread_id, to, subject, body, msg_id_header=None):
    m = MIMEText(body)
    m['to'], m['cc'], m['subject'] = to, CC, subject
    if msg_id_header:
        m['In-Reply-To'] = m['References'] = msg_id_header
    raw = base64.urlsafe_b64encode(m.as_bytes()).decode()
    return {'raw': raw, 'threadId': thread_id}

report = []
for lead in LEADS:
    q = f"from:{lead['email']} after:{SINCE}"
    res = svc.users().messages().list(userId='me', q=q).execute()
    for msg in res.get('messages', []):
        full = svc.users().messages().get(userId='me', id=msg['id'], format='full').execute()
        headers = {h['name'].lower(): h['value'] for h in full['payload']['headers']}
        snippet = full.get('snippet', '')
        intent = classify(snippet)
        subject = headers.get('subject', f"Parceria ASF x {lead['nome']}")
        if not subject.lower().startswith('re:'):
            subject = 'Re: ' + subject
        body = reply_body(lead, intent)
        payload = make_msg(full['threadId'], lead['email'], subject, body, headers.get('message-id'))
        if os.environ.get('AUTO_SEND', '').lower() == 'true':
            svc.users().messages().send(userId='me', body=payload).execute()
            action = 'ENVIADO'
        else:
            svc.users().drafts().create(userId='me', body={'message': payload}).execute()
            action = 'RASCUNHO'
        report.append({'lead': lead['nome'], 'intent': intent, 'acao': action})

print(json.dumps(report, ensure_ascii=False, indent=2))
if not report:
    print('Nenhuma resposta nova dos leads.')
