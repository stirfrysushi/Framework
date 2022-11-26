import socketserver
import secrets
import string 
from pymongo import MongoClient
from template import render_template


mongo_client = MongoClient("mongo")

# database data contain collections 
db = mongo_client["data"]

# collections in database:
cookie_db = db["cookie"]

# syntax for cookie header 
# Set-Cookie: <cookie-name>=<cookie-value>

# ask TA about placement of cookie 

class MyTCPHandler(socketserver.BaseRequestHandler):
    def handle(self):

        received_data = self.request.recv(2048)
        rn = ("\r\n\r\n").encode() 
        currentData = received_data.split(rn)
        cookieData = received_data.decode()
        header = currentData[0]
        splitData = header.decode().split() 
        print("\r\n")
        print("received data is: ")
        print(splitData)

        # GET request -> home page 
        if splitData[0] == "GET": 
            # GET homepage / HTML
            if splitData[1] == "/":
                # if no cookie, set visits = 1 
                if cookieData.find("Cookie") == -1: 
                    with open("index.html", "r") as f:
                        content = f.read()
                        content = content.replace("{{cookie}}", "1")
                        length = len(content)
                    self.request.sendall(("HTTP/1.1 200 OK\r\nContent-Length: " + str(length) + "\r\nContent-Type: text/html; charset=utf-8\r\nX-Content-Type-Options: nosniff\r\nSet-Cookie: visits=1; Max-Age=7200\r\n\r\n"+ str(content)).encode())


                # if there is cookie -> increment 
                else:
                    i = 0 
                    visit_index = 0
                    while i < len(splitData):
                        if splitData[i] == 'Cookie:': 
                            visit_index += i + 1
                        i += 1 
                    visit = splitData[visit_index].split("visits=")
                    current_visit = str(int(visit[1]) + 1)
                    print(current_visit)
                    with open("index.html", "r") as f:
                        content = f.read()
                        content = content.replace("{{cookie}}", current_visit)
                        length = len(content)
                    self.request.sendall(("HTTP/1.1 200 OK\r\nContent-Length: " + str(length) + "\r\nContent-Type: text/html; charset=utf-8\r\nX-Content-Type-Options: nosniff\r\nSet-Cookie: visits=" + str(current_visit) + "; Max-Age=7200\r\n\r\n"+ str(content)).encode())
            
            # GET css
            elif splitData[1] == "/style.css": 
                with open("style.css", "r") as f:
                    css = f.read()
                    cssLength = len(css)
                    self.request.sendall(("HTTP/1.1 200 OK\r\nContent-Length: " + str(cssLength) + "\r\nContent-Type: text/css; charset=utf-8\r\nX-Content-Type-Options: nosniff\r\n\r\n"+ str(css)).encode())
            
            # GET js
            elif splitData[1] == "/functions.js": 
                with open("functions.js", "r") as f:
                    js = f.read()
                    jsLength = len(js)
                    self.request.sendall(("HTTP/1.1 200 OK\r\nContent-Length: " + str(js) + "\r\nContent-Type: text/js; charset=utf-8\r\nX-Content-Type-Options: nosniff\r\n\r\n"+ str(jsLength)).encode())
            
                    
            # GET image 
            elif splitData[1].find("/image/") != -1: 
                splitImage = splitData[1].split("/")
                image_filename = splitImage[2] 
                with open("./image/" + image_filename, "rb") as f: 
                    image = f.read()
                    imageLength = len(image)
                    self.request.sendall(("HTTP/1.1 200 OK\r\nContent-Length: " + str(imageLength) + "\r\nContent-Type: image/jpg; charset=utf-8\r\nX-Content-Type-Options: nosniff\r\n\r\n").encode() + image)



        else: 
            self.request.sendall(("HTTP/1.1 404 Not Found\r\nContent-Length: 36\r\nContent-Type: text/plain; charset=utf-8\r\nX-Content-Type-Options: nosniff\r\n\r\nThe requested content does not EXIST".encode()))
        
        

if __name__ == "__main__":
    host = "0.0.0.0"
    port = 8080 

    server = socketserver.ThreadingTCPServer((host, port), MyTCPHandler)
    server.serve_forever()




