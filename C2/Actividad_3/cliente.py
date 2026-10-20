import socket_class as SocketTCP
import sys

if __name__ == "__main__":
    address = (sys.argv[1], int(sys.argv[2]))
    data = sys.stdin.buffer.read()

    client_socketTCP = SocketTCP.SocketTCP()
    client_socketTCP.connect(address)

    client_socketTCP.send(data)

    # test 1
    #message = "Mensje de len=16".encode()
    #print("enviando mensaje 1")
    #client_socketTCP.send(message)
    # test 2
    #message = "Mensaje de largo 19".encode()
    #client_socketTCP.send(message)
    # test 3
    #message = "Mensaje de largo 19".encode()
    #client_socketTCP.send(message)

    client_socketTCP.close()