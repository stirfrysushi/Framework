import socketserver
import bcrypt
import secrets 
from pymongo import MongoClient
from template import render_template


mongo_client = MongoClient("mongo")

# database data contain collections 
db = mongo_client["data"]

# collections in database:
cookie_db = db["cookie"]
user_db = db["user"]
token_db = db["token"]

# syntax for cookie header 
# ask TA about placement of cookie 
# ask TA about checkpw of bcrypt 

class MyTCPHandler(socketserver.BaseRequestHandler):
    def handle(self):

        received_data = self.request.recv(2048)
        rn = ("\r\n\r\n").encode() 
        currentData = received_data.split(rn)
        cookieData = received_data.decode()
        header = currentData[0]
        splitData = header.decode().split() 

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

            elif splitData[1] == "/favicon.ico": 
                with open("./image/favicon.ico", "rb") as f: 
                    content = f.read()
                    length = len(content)
                    self.request.sendall(("HTTP/1.1 200 OK\r\nContent-Length: " + str(length) + "\r\nContent-Type: image/ico; charset=utf-8\r\nX-Content-Type-Options: nosniff\r\n\r\n").encode() + content)

    
            # GET image 
            elif splitData[1].find("/image/") != -1: 
                splitImage = splitData[1].split("/")
                image_filename = splitImage[2] 
                with open("./image/" + image_filename, "rb") as f: 
                    image = f.read()
                    imageLength = len(image)
                    self.request.sendall(("HTTP/1.1 200 OK\r\nContent-Length: " + str(imageLength) + "\r\nContent-Type: image/jpg; charset=utf-8\r\nX-Content-Type-Options: nosniff\r\n\r\n").encode() + image)
                    
        elif splitData[0] == "POST": 
            current_users = user_db.find({"id": 1}, {"_id": 0}) 
            list_of_dicts = []
            for each in current_users: 
                list_of_dicts.append(each)
            
            list_of_data = []
            for each in list_of_dicts: 
                file_dicts = {}
                for eachKey in each: 
                    if eachKey == "username": 
                        username = each[eachKey]
                        file_dicts["username"] = username
                    if eachKey == "password":
                        password = each[eachKey]
                        file_dicts["password"] = password
                    if eachKey == "salt": 
                        salt = each[eachKey]
                        file_dicts["salt"] = salt
                list_of_data.append(file_dicts)

            print(list_of_data)
            print("\r\n\r\n")

            if splitData[1] == "/signup":
                split = received_data.decode().split()
                signup_index = len(split) - 1 
                signup_info = split[signup_index].split("&")
                username = str((signup_info[0].split("="))[1])
                # check username 
                for each_dict in list_of_data:
                    if each_dict["username"] == username: 
                        self.request.sendall("HTTP/1.1 200 OK\r\nContent-Length: 74\r\nContent-Type: text/plain; charset=utf-8\r\nX-Content-Type-Options: nosniff\r\n\r\nUsername is taken, please go back to main page and choose a different name".encode())
                   
                password = str((signup_info[1].split("="))[1])
                pass_bytes = password.encode('utf-8')
                salt = bcrypt.gensalt()
                hash = bcrypt.hashpw(pass_bytes, salt)

                #insert into database: username, password, salt 
                user_db.insert_one({"username": username, "password": hash, "salt": salt, "id": 1})
                
                # load a new page
                with open("signup.html", "r") as f:
                    content = f.read()
                    content = content.replace("{{username}}", str(username))
                    length = len(content)
                    self.request.sendall(("HTTP/1.1 200 OK\r\nContent-Length: " + str(length) + "\r\nContent-Type: text/html; charset=utf-8\r\nX-Content-Type-Options: nosniff\r\n\r\n"+ str(content)).encode())

                    
            if splitData[1] == "/login": 
                split = received_data.decode().split()
                signup_index = len(split) - 1 
                signup_info = split[signup_index].split("&")
                username = (signup_info[0].split("="))[1]
                password = ((signup_info[1].split("="))[1]).encode("utf-8")
                check = False 


                for each_dict in list_of_data:
                    if each_dict["username"] == username: 
                        stored_password = each_dict["password"]
                        stored_salt = each_dict["salt"]
                        current_hash = bcrypt.hashpw(password, stored_salt)
                        if current_hash == stored_password: 
                            check = True 
                        
                if check == True: 
                    # generate random token -> store in database 
                    token = (secrets.token_urlsafe(100)).encode("utf-8")
                    salt = bcrypt.gensalt()
                    hash = bcrypt.hashpw(token, salt)
                    token_db.insert_one({"username": username, "token": hash, "salt": salt, "id": 1})

                    # update html with welcome back + cookie 


                else: 
                    self.request.sendall("HTTP/1.1 200 OK\r\nContent-Length:32\r\nContent-Type: text/plain; charset=utf-8\r\nX-Content-Type-Options: nosniff\r\n\r\nWrong password, please try again".encode())

                
        else: 
            self.request.sendall(("HTTP/1.1 404 Not Found\r\nContent-Length: 36\r\nContent-Type: text/plain; charset=utf-8\r\nX-Content-Type-Options: nosniff\r\n\r\nThe requested content does not EXIST".encode()))
        
        

if __name__ == "__main__":
    host = "0.0.0.0"
    port = 8080 

    server = socketserver.ThreadingTCPServer((host, port), MyTCPHandler)
    server.serve_forever()




