import socket
import dnslib
from dnslib import QTYPE, DNSRecord
from utils import resolver
IP_VM = "172.30.153.212"
buff_size = 4096

resolver_address = (IP_VM, 8000)
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client_socket.bind(resolver_address)

while True:
  message, address = client_socket.recvfrom(buff_size)
  answer = resolver(message, debug=True)

  if answer:
    client_socket.sendto(answer, address)

