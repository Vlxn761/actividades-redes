import C2.Actividad_4.socketTCP as SocketTCP

address = ('localhost', 5000)

# CLIENT
client_socketTCP = SocketTCP.SocketTCP()
client_socketTCP.connect(address)
# Control de congestion
client_socketTCP.set_congestion_control(True)
# test 1
message = "Mensje de len=16".encode()
print("enviando mensaje 1")
client_socketTCP.send(message, mode="go_back_n")
# test 2
message = "Mensaje de largo 19".encode()
client_socketTCP.send(message, mode="go_back_n")
# test 3
message = "Mensaje de largo 19".encode()
client_socketTCP.send(message, mode="go_back_n")

client_socketTCP.close()