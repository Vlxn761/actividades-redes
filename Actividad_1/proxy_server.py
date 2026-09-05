#Integrante: Alejandro Molina

import socket
import sys
import json
from utils import (
  parse_HTTP_message,
  create_HTTP_message,
  receive_full_message,
  censor,
  FORBIDDEN_PAGE,
  IMAGE_RESPONSE
)

IP_VM = "172.30.153.212"
 
if __name__ == "__main__":
  buff_size = 50
  proxy_address = (IP_VM, 8000)

  file_path = sys.argv[1]
  with open(file_path, "r") as file:
    data = json.load(file)
  user = data["user"]
  blocked = data["blocked"]
  forbidden_words = data["forbidden_words"]

  client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  client_socket.bind(proxy_address)
  client_socket.listen(3)
  print('... Esperando cliente')

  while True:
    new_client_socket, client_address = client_socket.accept()
    recv_message = receive_full_message(new_client_socket, buff_size)

    message = parse_HTTP_message(recv_message)

    # Conexión al server
    host = message.headers["Host"]
    if ":" in host:
      server_address, server_port = message.headers["Host"].split(":", 1)
      server_port = int(server_port)
    else:
      server_address = host; server_port = 80

    server_domain = message.start_line.split(" ")[1]

    if "/403.jpg" in server_domain:
      new_client_socket.send(IMAGE_RESPONSE)
      new_client_socket.close()
      continue

    blocked_domain = False
    for domain in blocked:
      if domain in server_domain:
        blocked_domain = True

    if blocked_domain:
      new_client_socket.send(FORBIDDEN_PAGE)
      new_client_socket.close()
      continue

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.connect((server_address, server_port))

    message.headers["X-ElQuePregunta"] = user
    send_message = create_HTTP_message(message)
    server_socket.send(send_message)

    server_message = receive_full_message(server_socket, buff_size)
    server_message = censor(server_message, forbidden_words)

    new_client_socket.send(server_message)

    server_socket.close()
    new_client_socket.close()