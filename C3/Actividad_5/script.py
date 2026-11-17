import socket
from utils import parse_packet, create_packet, Headers

if __name__ == "__main__":
  IP_final, puerto_final = input("Dirección final: IP puerto ").split()
  IP_envio, puerto_envio = input("Dirección de envío: IP puerto ").split()
  dir_envio = (IP_envio, int(puerto_envio))
  data = input("Mensaje: ").encode()
  
  msg = Headers(
    IP=IP_final,
    port=int(puerto_final),
    data=data
  )

  msg = create_packet(msg)

  router_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  router_socket.sendto(msg, dir_envio)