import socket
import ssl
import base64
import json

def criar_conexao_mailserver():
    PORT = 465
    SMTP = "smtp.gmail.com"
    SERVIDOR_EMAIL = (SMTP, PORT)
    cliente_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    cliente_socket.connect(SERVIDOR_EMAIL)
    contexto_ssl = ssl.create_default_context()
    cliente_socket = contexto_ssl.wrap_socket(cliente_socket, server_hostname=SMTP)
    return cliente_socket

# Função para enviar o comando EHLO
def enviar_helo(cliente_socket):
    comando_helo = 'EHLO Cliente\r\n'
    cliente_socket.send(comando_helo.encode())
    resposta = cliente_socket.recv(1024).decode()
    if "220" in resposta:
        print("Comando EHLO aceito.")
    else:
        print("Falha ao enviar EHLO.")
    print("Resposta do servidor ao EHLO:")
    print(resposta)

# Função para autentica 
def autenticar(cliente_socket, usuario, senha):
    credenciais = f"\000{usuario}\000{senha}".encode()
    credenciais_b64 = base64.b64encode(credenciais).decode()
    comando_auth = f"AUTH PLAIN {credenciais_b64}\r\n"
    cliente_socket.send(comando_auth.encode())
    
    resposta_auth = cliente_socket.recv(1024).decode()
    if "250" in resposta_auth:
        print("Autenticação bem-sucedida.")
    else:
        print("Falha na autenticação.")
    print("Resposta do servidor à autenticação:")
    print(resposta_auth)

# Função para enviar o remetente
def enviar_remetente(cliente_socket, remetente):
    comando_remetente = f"MAIL FROM: <{remetente}>\r\n"
    cliente_socket.send(comando_remetente.encode())
    resposta_remetente = cliente_socket.recv(1024).decode()
    if "235" in resposta_remetente:
        print(f"Remetente <{remetente}> aceito.")
    else:
        print("Falha ao enviar remetente.")
    print("Resposta do servidor ao comando MAIL FROM:")
    print(resposta_remetente)

# Função para enviar o destinatário
def enviar_destinatario(cliente_socket, destinatario):
    comando_destinatario = f"RCPT TO: <{destinatario}>\r\n"
    cliente_socket.send(comando_destinatario.encode())
    resposta_destinatario = cliente_socket.recv(1024).decode()
    if "250" in resposta_destinatario:
        print(f"Destinatário <{destinatario}> aceito.")
    else:
        print("Falha ao enviar destinatário.")
    print("Resposta do servidor ao comando RCPT TO:")
    print(resposta_destinatario)

# Função para enviar a mensagem
def enviar_mensagem(cliente_socket, assunto, corpo_mensagem):
    comando_data = "DATA\r\n"
    cliente_socket.send(comando_data.encode())
    resposta_data = cliente_socket.recv(1024).decode()
    if "250" in resposta_data:
        print("Servidor pronto para receber a mensagem.")
    else:
        print("Falha ao iniciar envio da mensagem.")
    print("Resposta do servidor ao comando DATA:")
    print(resposta_data)
    
    mensagem_email = f"Subject: {assunto}\r\n\r\n{corpo_mensagem}\r\n"
    cliente_socket.send(mensagem_email.encode())
    cliente_socket.send("\r\n.\r\n".encode())
    resposta_mensagem = cliente_socket.recv(1024).decode()
    if "354" in resposta_mensagem:
        print("Mensagem enviada com sucesso.")
    else:
        print("Falha ao enviar a mensagem.")
    print("Resposta do servidor ao envio da mensagem:")
    print(resposta_mensagem)

# Função para encerrar
def encerrar_conexao(cliente_socket):
    comando_quit = "QUIT\r\n"
    cliente_socket.send(comando_quit.encode())
    resposta_quit = cliente_socket.recv(1024).decode()
    if "250" in resposta_quit:
        print("Conexão encerrada com sucesso.")
    else:
        print("Falha ao encerrar a conexão.")
    print("Resposta do servidor ao comando QUIT:")
    print(resposta_quit)
    cliente_socket.close()

# Função para ler as credenciais de um arquivo
def ler_credenciais_arquivo(arquivo):
    with open(arquivo, 'r') as f:
        dados = json.load(f)
    usuario = dados.get('usuario')
    token = dados.get('token')
    return usuario, token

# ler os dados do JSON
def ler_email_info_arquivo(arquivo):
    with open(arquivo, 'r') as f:
        dados_email = json.load(f)
    return dados_email['destinatario'], dados_email['assunto'], dados_email['mensagem']


def main():
    usuario, token = ler_credenciais_arquivo('email_info.json')
    destinatario, assunto, mensagem = ler_email_info_arquivo('email_info.json')
    
    cliente_socket = criar_conexao_mailserver()
    enviar_helo(cliente_socket) 
    autenticar(cliente_socket, usuario, token)
    remetente = f"{usuario}@gmail.com"
    enviar_remetente(cliente_socket, remetente)
    enviar_destinatario(cliente_socket, destinatario)
    enviar_mensagem(cliente_socket, assunto, mensagem)
    encerrar_conexao(cliente_socket)

if __name__ == "__main__":
    main()
