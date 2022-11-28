import socketserver
import bcrypt
import secrets 

from functions import escape_html
from functions import hash_password
from functions import check_password
from functions import get_digit
from functions import database_list
from handle_bytes import get_all_bytes

from pymongo import MongoClient
from template import render_template


mongo_client = MongoClient("mongo")

# database data contain collections 
db = mongo_client["data"]

# collections in database:
cookie_db = db["cookie"]
user_db = db["user"]
token_db = db["token"]
chat_db = db["chat"]
xsrf_db = db["xsrf"]

# syntax for cookie header 
# TA questions: 
# placement of cookie in header
# checkpw of bcrypt 
# redirect failing sometime 
# cookie counting and user login, should I be counting cookie regardless of whether user is logged in? 
# ask about obj4
# do we need to worry about messages that needs buffering? 
# worry about username spacing


class MyTCPHandler(socketserver.BaseRequestHandler):
    def handle(self):

        received_data = self.request.recv(2048)
        cookieData = received_data.decode()
        splitData = received_data.decode().split() 

        # GET request -> home page 
        if splitData[0] == "GET": 
            # GET homepage / HTML
            if splitData[1] == "/":
                print("\r\n")
                print("received data is: ")
                print(received_data.decode().split())

                # have to show chat-history regardless when getting to homepage 
                list_of_message = database_list(chat_db)

                # if no cookie, set visits = 1 
                if cookieData.find("Cookie") == -1: 
                    with open("index.html", "r") as f:
                        content = f.read()
                        content = render_template("index.html", {"loop_data": list_of_message})
                        content = content.replace("{{cookie}}", "1")
                        content = content.replace("{{user}}","!")
                        length = len(content)
                    self.request.sendall(("HTTP/1.1 200 OK\r\nContent-Length: " + str(length) + "\r\nContent-Type: text/html; charset=utf-8\r\nX-Content-Type-Options: nosniff\r\nSet-Cookie: visits=1; HttpOnly; Max-Age=7200\r\n\r\n"+ str(content)).encode())

                # if there is cookie -> increment 
                else:
                    current = ""
                    token_string = ""
                    for each in splitData:
                        if each.find("visits") != -1: 
                            current += each 

                        if each.find("id=") != -1: 
                            token_string += each 

                    
                    current_visit = int(get_digit(current))
                    current_visit += 1 
                    
                    # auth_token index; make sure there is token 
                    if len(token_string) != 0: 
                        token_string = token_string.split("=")
                        token_part = token_string[1]
                        token = ""
                        i = 0 
                        while i < len(token_part) and token_part[i] != ";":
                            token += token_part[i]
                            i += 1

                        print(token)

                        # find token in database -> if validated -> get user 
                        list_of_token = database_list(token_db)
                        current_user = ""
                        for each in list_of_token: 
                            current_token = each["token"]
                            check = check_password(current_token, token)
                            if check == True: 
                                current_user += each["username"] 
                        print("current user is: " + str(current_user))
                        
                        with open("index.html", "r") as f:
                            content = f.read()
                            content = render_template("index.html", {"loop_data": list_of_message})
                            content = content.replace("{{cookie}}", str(current_visit))
                            content = content.replace("{{user}}", str(current_user + "!"))
                            length = len(content)
                            self.request.sendall(("HTTP/1.1 200 OK\r\nContent-Length: " + str(length) + "\r\nContent-Type: text/html; charset=utf-8\r\nX-Content-Type-Options: nosniff\r\nSet-Cookie: visits=" + str(current_visit) + "; HttpOnly; Max-Age=7200\r\n\r\n"+ str(content)).encode())

                    # if there is no auth -> no welcome user 
                    else: 
                        with open("index.html", "r") as f:
                            content = f.read()
                            content = render_template("index.html", {"loop_data": list_of_message})
                            content = content.replace("{{cookie}}", str(current_visit))
                            content = content.replace("{{user}}", "!")
                            length = len(content)
                        self.request.sendall(("HTTP/1.1 200 OK\r\nContent-Length: " + str(length) + "\r\nContent-Type: text/html; charset=utf-8\r\nX-Content-Type-Options: nosniff\r\nSet-Cookie: visits=" + str(current_visit) + "; HttpOnly; Max-Age=7200\r\n\r\n"+ str(content)).encode())
            
            
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

            # list for user db ->> username + hash 
            list_of_data = database_list(user_db)
            print("list of data for users: ")
            print(list_of_data)
            print("\r\n\r\n")

            if splitData[1] == "/signup":
                split = received_data.decode().split()
                signup_index = len(split) - 1 
                signup_info = split[signup_index].split("&")
                username = str((signup_info[0].split("="))[1])

                # if username exist ->> ask for a different username 
                for each_dict in list_of_data:
                    if each_dict["username"] == username: 
                        self.request.sendall("HTTP/1.1 200 OK\r\nContent-Length: 74\r\nContent-Type: text/plain; charset=utf-8\r\nX-Content-Type-Options: nosniff\r\n\r\nUsername is taken, please go back to main page and choose a different name".encode())
                   
            
                password = str((signup_info[1].split("="))[1])
                hash = hash_password(password)

                # security -> escape html username from signup
                username = escape_html(username)
                username = username.replace("+", " ")
                #insert into database: username, password
                user_db.insert_one({"username": username, "password": hash, "id": 1})
                
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
                password = ((signup_info[1].split("="))[1])


                for each_dict in list_of_data:
                    if each_dict["username"] == username: 
                        stored_password = each_dict["password"]
                        check = check_password(stored_password, password)
                        
                        # user is authenticated 
                        if check == True: 
                            # generate token
                            token = secrets.token_urlsafe(32)

                            salt = bcrypt.gensalt()
                            hash = bcrypt.hashpw(token.encode(), salt)
                            # store hash of token 
                            token_db.insert_one({"username": username, "token": hash,"id": 1})

                            # set cookie for authentication, redirect back to home page with user 
                            self.request.sendall(("HTTP/1.1 302 Found\r\nContent-Length: 0\r\nSet-Cookie: id=" + str(token) + "; HttpOnly; Max-Age=7200\r\nLocation: /").encode())

                        # if user is not succesfully authenticated -> redirect to home 
                        else: 
                            self.request.sendall(("HTTP/1.1 404 Not Found\r\nContent-Length: 36\r\nContent-Type: text/plain; charset=utf-8\r\nX-Content-Type-Options: nosniff\r\n\r\nThe requested content does not EXIST".encode()))

                            
            if splitData[1] == "/chat": 
                print(splitData)

                # if no auth-token -> redirect 
                if cookieData.find("id=") == -1: 
                    self.request.sendall("HTTP/1.1 301 Moved Permanently\r\nContent-Length: 0\r\nLocation: /".encode())
            
                else:
                    current_message = "" 
                    for each in splitData:
                        if each.find("message") != -1: 
                            each = (each.split("="))[1]
                            current_message += each
                    
                    print("current message is: ")
                    print(current_message)

                    token_string = ""
                    for each in splitData:
                        if each.find("id=") != -1: 
                            token_string += each 

                    # auth_token index; make sure there is token 
                    if len(token_string) != 0: 
                        token_string = token_string.split("=")
                        token_part = token_string[1]
                        token = ""
                        i = 0 
                        while i < len(token_part) and token_part[i] != ";":
                            token += token_part[i]
                            i += 1

                        print("current token is: ")
                        print(token)

                        # find token in database -> if validated -> get user 
                        list_of_token = database_list(token_db)
                        current_user = ""
                        for each in list_of_token: 
                            current_token = each["token"]
                            check = check_password(current_token, token)
                            if check == True: 
                                current_user += each["username"] 
                        
                        print("current sender is " + str(current_user))

                        # security check -> esape html for both username + message 
                        current_user = escape_html(current_user)
                        current_message = escape_html(current_message)
                        current_message = current_message.replace("+", " ")

                        if current_user != "": 
                            chat_db.insert_one({"username": current_user, "message": current_message, "id": 1})
                            self.request.sendall("HTTP/1.1 301 Moved Permanently\r\nContent-Length: 0\r\nLocation: /".encode())

                        # couldn't find user -> redirect to homepage 
                        else: 
                            self.request.sendall("HTTP/1.1 301 Moved Permanently\r\nContent-Length: 0\r\nLocation: /".encode())

                
        else: 
            self.request.sendall(("HTTP/1.1 404 Not Found\r\nContent-Length: 36\r\nContent-Type: text/plain; charset=utf-8\r\nX-Content-Type-Options: nosniff\r\n\r\nThe requested content does not EXIST".encode()))
        
        

if __name__ == "__main__":
    host = "0.0.0.0"
    port = 8000 

    socketserver.TCPServer.allow_reuse_address = True 
    server = socketserver.ThreadingTCPServer((host, port), MyTCPHandler)
    server.serve_forever()




