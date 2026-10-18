#Integrante: Alejandro Molina

class HTTPMessage:
  def __init__(
      self,
      start_line: str,
      headers: dict[str, str],
      body: bytes
  ):
    self.start_line = start_line
    self.headers = headers
    self.body = body

def parse_HTTP_message(http_message):
  head, body = http_message.split(b"\r\n\r\n", 1)

  start_line, headers = head.split(b"\r\n", 1)
  headers = headers.decode()
  headers = headers.split("\r\n")
  
  headers_dict = {}
  for header in headers:
    name, info = header.split(":", 1)
    headers_dict[name] = info[1:]

  parsed_message = HTTPMessage(
                    start_line = start_line.decode(),
                    headers=headers_dict,
                    body=body
                  )

  return parsed_message

def create_HTTP_message(parsed_message):
  start_line = parsed_message.start_line + "\r\n"
  start_line = start_line.encode()

  headers = ""
  for name, value in parsed_message.headers.items():
    headers += f'{name}: {value}\r\n'
  headers = headers.encode()

  message = start_line + headers + b"\r\n" + parsed_message.body
  
  return message

def receive_full_message(socket, buff_size):
  full_message = b""

  while b"\r\n\r\n" not in full_message:
    full_message += socket.recv(buff_size)

  head, body = full_message.split(b"\r\n\r\n", 1)

  content_length = 0
  headers = head.split(b"\r\n")
  for header in headers:
    if b"Content-Length:" in header:
      _, content_length = header.split(b" ", 1)
      content_length = int(content_length.strip())

  while len(body) < content_length:
    body += socket.recv(buff_size)

  return head + b"\r\n\r\n" + body 

def censor(http_message, forbidden_words):
  message = parse_HTTP_message(http_message)
  body = message.body

  for dict in forbidden_words:
    for word, word2 in dict.items():
      body =  body.replace(word.encode(), word2.encode())

  message.body = body
  message.headers["Content-Length"] = str(len(body))

  return create_HTTP_message(message)


# Página forbidden
page_body = b"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Forbidden</title>
</head>
<body>
    <h1>403 Forbidden</h1>
    <img src="403.jpg">
</body>
</html>"""

page_head = (b"HTTP/1.1 403 Forbidden\r\n" 
             + b"Content-Type: text/html; charset=utf-8\r\n" 
             + b"Content-Length: " + str(len(page_body)).encode() + b"\r\n" 
             + b"Connection: close\r\n" 
             )

FORBIDDEN_PAGE = page_head + b"\r\n" + page_body

# Imagen 403
with open("403.jpg", "rb") as image:
  img_body = image.read()

img_head = (b"HTTP/1.1 200 OK\r\n" 
             + b"Content-Type: image/jpeg; charset=utf-8\r\n" 
             + b"Content-Length: " + str(len(img_body)).encode() + b"\r\n" 
             + b"Connection: close\r\n" 
             )
IMAGE_RESPONSE = img_head + b"\r\n" + img_body