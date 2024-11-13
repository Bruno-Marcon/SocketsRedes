import os
import socket
import struct
import select
import time
import errno

class Ping:
    ICMP_ECHO_REQUEST = 8

    def __init__(self, timeout=2, count=4):
        self.timeout = timeout
        self.count = count
        self.default_timer = time.time

    def checksum(self, string):
        # Calcula o checksum para verificar a integridade do pacote ICMP
        csum = 0
        countTo = (len(string) // 2) * 2
        count = 0
        while count < countTo:
            thisVal = (string[count+1] << 8) + string[count]
            csum = csum + thisVal
            csum = csum & 0xffffffff
            count = count + 2
        if countTo < len(string):
            csum = csum + string[len(string) - 1]
            csum = csum & 0xffffffff
        csum = (csum >> 16) + (csum & 0xffff)
        csum = csum + (csum >> 16)
        answer = ~csum
        answer = answer & 0xffff
        answer = answer >> 8 | (answer << 8 & 0xff00)
        return answer

    def receive_one_ping(self, my_socket, pid):
        # Recebe a resposta ICMP e calcula o RTT
        time_left = self.timeout
        while True:
            start_select = self.default_timer()
            ready_to_read = select.select([my_socket], [], [], time_left)
            time_in_select = (self.default_timer() - start_select)
            if ready_to_read[0] == []:  # Timeout
                return None

            time_received = self.default_timer()
            packet_received, address = my_socket.recvfrom(1024)
            icmp_header = packet_received[20:28]
            type, code, checksum, packet_id, sequence = struct.unpack("bbHHh", icmp_header)

            if type != 8 and packet_id == pid:
                double_bytes = struct.calcsize("d")
                time_sent = struct.unpack("d", packet_received[28:28 + double_bytes])[0]
                if code == 0:
                    return time_received - time_sent
                return None

            time_left = time_left - time_in_select
            if time_left <= 0:
                return None

    def send_one_ping(self, my_socket, destination_address, pid):
        # Envia um pacote ICMP para o destino
        destination_address = socket.gethostbyname(destination_address)
        my_checksum = 0
        header = struct.pack("bbHHh", self.ICMP_ECHO_REQUEST, 0, my_checksum, pid, 1)
        double_bytes = struct.calcsize("d")
        data = (192 - double_bytes) * "Q"
        data = struct.pack("d", self.default_timer()) + data.encode('utf-8')

        my_checksum = self.checksum(header + data)
        header = struct.pack("bbHHh", self.ICMP_ECHO_REQUEST, 0, socket.htons(my_checksum), pid, 1)
        packet = header + data
        my_socket.sendto(packet, (destination_address, 1))

    def do_one_ping(self, destination_address):
        # Realiza um ping para o destino
        icmp = socket.getprotobyname("icmp")
        try:
            my_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp)
        except socket.error as e:
            if e.errno == errno.EPERM:
                raise socket.error(e.strerror + " - Apenas processos com privilégios de administrador podem enviar pacotes ICMP.")
            raise

        my_pid = os.getpid() & 0xFFFF
        self.send_one_ping(my_socket, destination_address, my_pid)
        delay = self.receive_one_ping(my_socket, my_pid)
        my_socket.close()
        return delay

    def verbose_ping(self, destination_address):
        # Realiza múltiplos pings e exibe estatísticas
        min_rtt = float('inf')
        max_rtt = 0
        total_rtt = 0
        lost_count = 0
        
        print(f"\nFazendo ping em {destination_address}...")
        
        for i in range(self.count):
            try:
                delay = self.do_one_ping(destination_address)
            except socket.gaierror as e:
                print(f"Erro: {e.strerror}. Não foi possível resolver o host.")
                break

            if delay is None:
                print(f"Tempo esgotado após {self.timeout} segundos.")
                lost_count += 1
            else:
                delay = delay * 1000
                total_rtt += delay
                min_rtt = min(min_rtt, delay)
                max_rtt = max(max_rtt, delay)
        
        if self.count - lost_count > 0:
            avg_rtt = total_rtt / (self.count - lost_count)
            packet_loss = (lost_count / self.count) * 100

            print("\nEstatísticas de ping:")
            print(f"  Pacotes Enviados  = {self.count}")
            print(f"  Pacotes Recebidos = {self.count - lost_count}")
            print(f"  Pacotes Perdidos  = {lost_count} ({packet_loss:.2f}% de perda)")
            print(f"  Min RTT           = {min_rtt:0.4f} ms")
            print(f"  Max RTT           = {max_rtt:0.4f} ms")
            print(f"  Média RTT         = {avg_rtt:0.4f} ms")
        else:
            print("\nEstatísticas de ping: Todos os pacotes foram perdidos")

        print("\nTeste de ping concluído")

# Executa o script para testar os pings
if __name__ == '__main__':
    ping_tool = Ping(timeout=2, count=4)
    ping_tool.verbose_ping("8.8.8.8")
    ping_tool.verbose_ping("1.1.1.1")
    ping_tool.verbose_ping("facebook.com")
    ping_tool.verbose_ping("google.com")
