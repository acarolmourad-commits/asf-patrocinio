"""ASF — Monitor de respostas de parceria (via Composio API).

GARANTIAS DE DETECÇÃO E QUALIDADE:
- Detecta respostas por DOIS caminhos: busca 'from:<lead>' e leitura da
  thread original (cobre lead que responde de outro e-mail);
- DEDUPLICAÇÃO: message IDs processados ficam em data/state.json
  (commitado de volta pelo workflow) — nenhuma resposta é processada 2x;
- Ignora mensagens enviadas pela própria ASF;
- PLAYBOOK 100% por e-mail (nunca sugerir WhatsApp):
    positiva/duvida/reuniao -> Plano de Parceria completo
    aceite (CNPJ/"aceitamos") -> pede dados empresariais p/ contrato
    negativa -> agradecimento elegante

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
STATE_PATH = 'data/state.json'
state = json.load(open(STATE_PATH)) if os.path.exists(STATE_PATH) else {'processados': []}
processados = set(state['processados'])

POS = ['parceria', 'topamos', 'vamos conversar', 'interesse', 'adorei', 'adoramos', 'podemos', 'informações', 'informacoes', 'detalhes']
MEET = ['call', 'reunião', 'reuniao', 'agendar', 'horário', 'horario']
ACCEPT = ['aceito', 'aceitamos', 'fechado', 'concordo', 'concordamos', 'vamos fechar', 'assinamos', 'segue os dados', 'seguem os dados']
NEG = ['não temos interesse', 'no momento não', 'infelizmente não', 'desculpa']
CNPJ = re.compile(r'\d{2}[.]?\d{3}[.]?\d{3}[/]?\d{4}[-]?\d{2}')

def composio(tool, args):
    r = requests.post(f'{API}/tools/execute/{tool}', headers=H,
                      json={'user_id': USER, 'arguments': args}, timeout=60)
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
    return (f"Olá, equipe {nome}!\n\nObrigada pelo retorno! Segue nosso Plano de Parceria completo.\n\n"
            f"SOBRE A ASF\n{APP_TXT}\n\n"
            "O QUE A ASF OFERECE:\n"
            "1. Logo da marca em destaque na seção Parceiras & Benefícios do app ASF;\n"
            "2. Divulgação nas redes sociais (post de lançamento + menções mensais);\n"
            "3. Indicação ativa à comunidade de associadas (app, e-mail e eventos);\n"
            "4. 1 ação/conteúdo conjunto por mês;\n"
            "5. Relatório de resultados ao fim de cada período.\n\n"
            "O QUE PEDIMOS:\n"
            "1. Benefício exclusivo para associadas ASF (desconto/condição especial);\n"
            "2. Divulgação da ASF nos canais da marca;\n"
            "3. Participação na ação/conteúdo conjunto mensal.\n\n"
            "CONDIÇÕES GERAIS:\n"
            "- Vigência de 6 meses, renovação automática, rescisão com 30 dias de aviso (sem multa);\n"
            "- Parceria não exclusiva;\n"
            "- Formalização por contrato simples.\n\n"
            "Se concordarem, enviamos o contrato — para isso precisamos dos dados empresariais:\n"
            "- Razão social e CNPJ\n- Nome do responsável legal\n- Endereço comercial\n"
            "- E-mail e telefone oficiais\n- Benefício acordado para associadas\n\n"
            "Seguimos por e-mail para manter tudo documentado. Ficamos à disposição!\n\n"
            "Abraços,\nCarol — ASF\nasf.surffeminino@gmail.com | asf.surf")

def aceite(nome):
    return (f"Olá, equipe {nome}!\n\nQue notícia ótima — parceria aceita! 🎉\n\n"
            "Para formalizarmos com o contrato simples (6 meses, renovável, sem multa rescisória), "
            "confirmem por favor:\n"
            "- Razão social e CNPJ\n- Nome do responsável legal\n- Endereço comercial\n"
            "- E-mail e telefone oficiais\n- Benefício acordado para associadas ASF\n\n"
            "Recebidos os dados, enviamos o contrato para assinatura e, em até 7 dias, a logo entra "
            "no app ASF + post de lançamento da parceria nas nossas redes.\n\n"
            "Abraços,\nCarol — ASF")

def reply_body(nome, intent):
    if intent == 'aceite': return aceite(nome)
    if intent in ('positiva', 'reuniao', 'duvida'): return proposta(nome)
    return (f"Olá, equipe {nome}!\n\nAgradecemos muito o retorno e a sinceridade. "
            "Se fizer sentido no futuro, estamos à disposição. Sucesso!\n\nAbraços,\nEquipe ASF")

report = []
for lead in LEADS:
    candidatos = {}
    # Caminho 1: busca por remetente
    res = composio('GMAIL_FETCH_EMAILS', {'query': f"from:{lead['email']} after:{SINCE}",
                                          'max_results': 10, 'verbose': True})
    for m in (res.get('data') or {}).get('messages') or []:
        candidatos[m.get('messageId')] = m
    # Caminho 2: thread original (cobre resposta vinda de outro e-mail do parceiro)
    if lead.get('thread_id'):
        try:
            t = composio('GMAIL_FETCH_MESSAGE_BY_THREAD_ID', {'thread_id': lead['thread_id']})
            for m in (t.get('data') or {}).get('messages') or []:
                candidatos.setdefault(m.get('messageId'), m)
        except Exception:
            pass
    for m in candidatos.values():
        mid = m.get('messageId')
        if not mid or mid in processados:
            continue
        if CC in (m.get('sender') or ''):
            processados.add(mid)
            continue
        intent = classify(m.get('messageText') or m.get('snippet'))
        subject = m.get('subject') or f"Parceria ASF x {lead['nome']}"
        if not subject.lower().startswith('re:'):
            subject = 'Re: ' + subject
        args = {'recipient_email': lead['email'], 'cc': [CC],
                'body': reply_body(lead['nome'], intent),
                'thread_id': m.get('threadId') or lead.get('thread_id')}
        if AUTO_SEND:
            args['subject'] = subject
            composio('GMAIL_SEND_EMAIL', args)
            acao = 'ENVIADO'
        else:
            composio('GMAIL_CREATE_EMAIL_DRAFT', args)
            acao = 'RASCUNHO'
        processados.add(mid)
        report.append({'lead': lead['nome'], 'intent': intent, 'acao': acao,
                       'proximo': 'gerar_contrato' if intent == 'aceite' else 'aguardar'})

state['processados'] = sorted(processados)
json.dump(state, open(STATE_PATH, 'w'), ensure_ascii=False, indent=1)
json.dump({'ultima_execucao': True, 'eventos': report},
          open('data/relatorio.json', 'w'), ensure_ascii=False, indent=2)
print(json.dumps(report, ensure_ascii=False, indent=2))
if not report:
    print('Nenhuma resposta nova dos leads.')
