import time
from socket import *

HOST = '127.0.0.1'
PORT = 12000
ENDERECOSERVIDOR = (HOST, PORT)
PACOTES = 10

def enviarPing(socketCliente, numeroPing):
    horarioEnvio = time.time()
    mensagem = f"Ping {numeroPing} Horario {horarioEnvio}"
    
    try:
        # Envia a mensagem
        socketCliente.sendto(mensagem.encode(), ENDERECOSERVIDOR)
        
        # Resposta do serverUdp
        resposta, _ = socketCliente.recvfrom(1024)
        
        tempoRtt = time.time() - horarioEnvio
        print(f"Resposta do servidor: {resposta.decode()} | RTT: {tempoRtt:.4f} segundos")
        
        return tempoRtt
    
    except timeout:
        # Não recebeu em 1s o pacote
        print("Request timed out")
        return None

def listarEstatisticas(listaRtt, pacotesEnviados, pacotesRecebidos):
    if listaRtt:
        rttMin = min(listaRtt)
        rttMax = max(listaRtt)
        rttMed = sum(listaRtt) / len(listaRtt)
    else:
        rttMin = rttMax = rttMed = 0

    taxaPerda = ((pacotesEnviados - pacotesRecebidos) / pacotesEnviados) * 100

    print("\n....:::: Estatísticas de Ping ::::....")
    print(f"..::Pacotes::..")
    print(f"Enviados = {pacotesEnviados}")
    print(f"Recebidos = {pacotesRecebidos})")
    print(f"Perdidos = {pacotesEnviados - pacotesRecebidos}")
    print(f"Taxa: ({taxaPerda:.2f}% de perda)")
    print(f"RTT (ms): Mínimo = {rttMin * 1000:.6f}, Máximo = {rttMax * 1000:.6f}, Médio = {rttMed * 1000:.6f}")

def main():
    
    socketCliente = socket(AF_INET, SOCK_DGRAM)
    socketCliente.settimeout(1)
    listaRtt = []
    pacotesRecebidos = 0

    # Envia os pacotes
    for numeroPing in range(1, PACOTES + 1):
        rtt = enviarPing(socketCliente, numeroPing)
        
        # ping com sucesso armazena
        if rtt is not None:
            listaRtt.append(rtt)
            pacotesRecebidos += 1

    socketCliente.close()
    
    listarEstatisticas(listaRtt, PACOTES, pacotesRecebidos)

if __name__ == "__main__":
    main()
