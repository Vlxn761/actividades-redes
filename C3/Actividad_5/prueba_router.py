import sys
import socket
from utils import parse_packet, create_packet, Headers

if __name__ == "__main__":
  headers = sys.argv[1]
  IP_final, puerto_final, TTL = headers.split(";")
  router_address = (sys.argv[2], int(sys.argv[3]))

  router_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

  with open("archivo.txt", "r") as file:
      for line in file:
        data = line.encode()
        msg = Headers(
          IP=IP_final,
          port=puerto_final,
          TTL=TTL,
          data=data
        )
        msg = create_packet(msg)
        router_socket.sendto(msg, router_address)