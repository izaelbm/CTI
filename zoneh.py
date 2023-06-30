import imaplib
import email
import json
from datetime import datetime
import socket

def make(data):
    json_data = data

    # Acesso aos dados do arquivo JSON
    subject = json_data['Subject']
    time_string = json_data['Date']

    input_format = '%a, %d %b %Y %H:%M:%S %z (%Z)'
    output_format = '%Y-%m-%d'

    # Analisar a string de data para obter um objeto de data e hora
    time_object = datetime.strptime(time_string, input_format)

    # Formatar a data e hora conforme desejado
    formatted_time = time_object.strftime(output_format)

    body = json_data['Body']
    lines = body.splitlines()

    # Cria um novo objeto JSON
    dados = {
        "log": []
    }
    
    for i in range(0, len(lines), 1):
        cont = i + 1

        if lines[i].startswith("http"):
            
            array = lines[i].split(" ")

            #Adiciona um novo item ao JSON
            novo_item = {
                'source': 'zone-h',
                'date': formatted_time,
                'subject': subject,
                'author':str(array[3].strip()),
                'target':str(array[0].strip()),
                'evidence':str(array[4]).strip()
            }

            sendLog(novo_item)
            
            #dados['log'].append(novo_item)

       
    return 'OK'

def sendLog(data):

    host="127.0.0.1"
    port=9999

    #Testando a Conexao  ao coletor do Rapid7 - UDP
    sc = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    rs = sc.connect_ex((host,port))

    if (rs == 0):
            print("Conectou")
    else:
            print("Erro ao Conectar")

    #Tratando os logs
    #data = data.decode("utf-8")

    byte_message=bytes (f"{data}", "utf-8")

    #enviando os dados
    try:
            #sc.sendto(data.encode('utf-8'), (host, port))
            sc.sendto(byte_message,(host,port))

            return "Log Enviado"
    finally:
            sc.close()

# Informações de conexão
imap_server = 'imap.server.com'
username = 'mail@colect.com'
password = 'password'

# Estabelece a conexão SSL
imap = imaplib.IMAP4_SSL(imap_server)

# Faz o login
imap.login(username, password)

# Seleciona a caixa de entrada
imap.select('INBOX')

# Procura por mensagens não lidas
status, response = imap.search(None, '(UNSEEN SUBJECT "Zone-H")')
if status == 'OK':
    unread_msgs = response[0].split()
    if unread_msgs:
        # Obtém o número da primeira mensagem não lida
        msg_num = unread_msgs[0]

        # Obtém os dados da mensagem
        status, response = imap.fetch(msg_num, '(RFC822)')
        if status == 'OK':
            raw_email = response[0][1]  # Obtém o conteúdo da mensagem

            # Analisa o conteúdo da mensagem
            msg = email.message_from_bytes(raw_email)

            # Extrai informações relevantes
            message_data = {
                'Subject': msg['Subject'],
                'From': msg['From'],
                'To': msg['To'],
                'Date': msg['Date'],
                'Body': ''
            }

            if msg.is_multipart():
                # Lida com mensagens multipart (texto e anexos)
                for part in msg.get_payload():
                    if part.get_content_type() == 'text/plain':
                        message_data['Body'] = part.get_payload(decode=True).decode('utf-8')
                        break
            else:
                # Lida com mensagens de texto simples
                message_data['Body'] = msg.get_payload(decode=True).decode('utf-8')

            jsonData = make(message_data)
            
            print(sendLog(jsonData))

# Desconecta do servidor
imap.logout()
