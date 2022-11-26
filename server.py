import socketserver
import secrets
import string 
from pymongo import MongoClient
from template import render_template



mongo_client = MongoClient("mongo")

# database data contain collections 
db = mongo_client["data"]

# collections in cse312 database: 
upload_db = db["upload"]
token_db = db["tokens"]
comment_db = db["comments"]
post_db = db["post"]


class MyTCPHandler(socketserver.BaseRequestHandler):
    def handle(self):


        received_data = self.request.recv(2048)
        rn = ("\r\n\r\n").encode() 
        currentData = received_data.split(rn)
        header = currentData[0]
        header_length = len(header)
        splitData = header.decode().split() 

        # GET request -> home page 
        if splitData[0] == "GET": 

            # generate token + add to database 
            token = secrets.token_urlsafe(8) 
            token_db.insert_one({"id": 1,"token": token})

            # serve home page
            if splitData[1] == "/": 

                # build images 
                bytes_dict_list = [] 
                stuff = post_db.find({"id": 1}, {"_id": 0}) 

                for each in stuff:
                    bytes_dict_list.append(each)
                
                for each_dict in bytes_dict_list:
                    for eachItem in each_dict: 
                        current_name = each_dict["filename"]
                        image_bytes = each_dict["image_bytes"]

                        with open("./image/" + current_name, "wb") as f: 
                            f.write(image_bytes)
                            
                # get all image 
                list_of_dicts = [] 
                content = upload_db.find({"id": 1}, {"_id": 0}) 
                for each in content: 
                    list_of_dicts.append(each)
                
                list_of_data = [] 
                for each in list_of_dicts: 
                    file_dicts = {}
                    for eachKey in each: 
                        if eachKey == "filename": 
                            filename = each[eachKey]
                            file_dicts["filename"] = filename
                        if eachKey == "caption":
                            caption = each[eachKey]
                            file_dicts["caption"] = caption
                 
                    list_of_data.append(file_dicts)

                # get just comments 
                commentdicts = [] 
                list_of_comments = [] 
                comment_string = "" 
                stuff = comment_db.find({"id": 1}, {"_id": 0}) 
                for each in stuff:
                   commentdicts.append(each)
                
                for each in commentdicts:
                    for key in each:
                        if each[key] != 1: 
                            list_of_comments.append(each[key])
            
                if len(list_of_comments) != 0: 
                    comment_string += list_of_comments[0]

                    j = 1 
                    while j < len(list_of_comments): 
                        if list_of_comments[j] == "":
                            comment_string += ", "
                            answer = "empty string received from server"
                            comment_string += answer 
                        else: 
                            comment_string += ", "
                            comment_string += list_of_comments[j]
                        j += 1
                
                        
                # serve html 
                with open("index.html", "r") as f:
                    content = render_template("index.html",{"loop_data": list_of_data})
                    content = content.replace("{{comment}}",comment_string)
                    content = content.replace("{{token}}", token)
                    length = len(content)
                self.request.sendall(("HTTP/1.1 200 OK\r\nContent-Length: " + str(length) + "\r\nContent-Type: text/html; charset=utf-8\r\nX-Content-Type-Options: nosniff\r\n\r\n"+ str(content)).encode())
            
            elif splitData[1] == "/style.css": 
                with open("style.css", "r") as f:
                    css = f.read()
                    cssLength = len(css)
                    self.request.sendall(("HTTP/1.1 200 OK\r\nContent-Length: " + str(cssLength) + "\r\nContent-Type: text/css; charset=utf-8\r\nX-Content-Type-Options: nosniff\r\n\r\n"+ str(css)).encode())
            
            elif splitData[1] == "/functions.js": 
                with open("functions.js", "r") as f:
                    js = f.read()
                    jsLength = len(js)
                    self.request.sendall(("HTTP/1.1 200 OK\r\nContent-Length: " + str(js) + "\r\nContent-Type: text/js; charset=utf-8\r\nX-Content-Type-Options: nosniff\r\n\r\n"+ str(jsLength)).encode())
            
                    
            # split to get image 
            elif splitData[1].find("/image/") != -1: 
                splitImage = splitData[1].split("/")
                image_filename = splitImage[2] 
                with open("./image/" + image_filename, "rb") as f: 
                    image = f.read()
                    imageLength = len(image)
                    self.request.sendall(("HTTP/1.1 200 OK\r\nContent-Length: " + str(imageLength) + "\r\nContent-Type: image/jpg; charset=utf-8\r\nX-Content-Type-Options: nosniff\r\n\r\n").encode() + image)

                    
        
        elif splitData[0] == "POST": 
            if splitData[1] == "/image-upload":  
                content_length = 0 
                encoded_rn = "\r\n\r\n".encode()
                split = received_data.split(encoded_rn)

                # get length 
                header = split[0].decode().split() 
                length_index = (header.index("Content-Length:")) + 1 
                data_length = header[length_index]
                content_length += int(data_length)

                # get boundary 
                header_index = (header.index('multipart/form-data;')) + 1 
                boundary_section = header[header_index].split("=")
                boundary = boundary_section[1]

                # see if got enough data: 
                received_length = len(received_data)
                data_array = bytearray(received_data)
                if received_length < content_length + header_length: 
                    while received_length <= content_length + header_length:
                        more_data = self.request.recv(2048)
                        data_array += bytearray(more_data)
                        received_length += len(more_data)

                # split body 
                boundary_encoded = boundary.encode() 
                data_array = data_array.split(boundary_encoded)
               
                # get token
                token_section = data_array[2].decode().split("\r\n")
                token = token_section[3] 
                # get list of available token from database: 
                token_dicts = [] 
                listTokens = [] 
                tokens = token_db.find({"id": 1}, {"_id": 0}) 
                for each in tokens:
                   token_dicts.append(each)
                for each in token_dicts:
                    for key in each:
                        listTokens.append(each["token"])
                # check token 
                if token not in listTokens: 
                    self.request.sendall(("HTTP/1.1 403 Forbidden\r\nContent-Length: 34\r\nContent-Type: text/plain; charset=utf-8\r\nX-Content-Type-Options: nosniff\r\n\r\nThe requested content was REJECTED".encode()))

                else: 
                    # get comment 
                    caption_section = data_array[3].decode().split("\r\n")
                    caption = caption_section[3]
                    if caption_section[4] != "--": 
                        i = 4
                        while caption_section[i] != "--":
                            caption += "\r\n"
                            caption += caption_section[i]
                            i += 1
                    
                    # prevent html injections 
                    caption = caption.replace('&', '&amp;')
                    caption = caption.replace('<', '&lt;')
                    caption = caption.replace('>', '&gt;')
                
                    # get image 
                    image_section = data_array[4].split(encoded_rn)
                    image_bytes = bytes(image_section[1])

                    # if only comment -> put into database + redirect 
                    if image_bytes == b'\r\n--': 
                        comment_db.insert_one({"comment": caption, "id":1})
                        self.request.sendall(("HTTP/1.1 301 Moved Permanently\r\nContent-Length: 0\r\nLocation:/").encode())


                    # upload image: 
                    elif image_bytes != b'\r\n--':
            
                        # generate new name
                        letters = string.ascii_lowercase
                        new_name = letters.get_first_name()
                        filename = new_name + ".jpg"

                        # store the bytes for persistent 
                        post_db.insert_one({"filename": filename, "image_bytes": image_bytes, "id": 1})

                        # write to file + redirect 
                        with open("./image/" + filename, "wb") as f:
                            f.write(image_bytes)
                            upload_db.insert_one({"filename":filename, "caption": caption, "id": 1})
                            self.request.sendall(("HTTP/1.1 301 Moved Permanently\r\nContent-Length: 0\r\nLocation:/").encode())
            
        else: 
            self.request.sendall(("HTTP/1.1 404 Not Found\r\nContent-Length: 36\r\nContent-Type: text/plain; charset=utf-8\r\nX-Content-Type-Options: nosniff\r\n\r\nThe requested content does not EXIST".encode()))
        
        

if __name__ == "__main__":
    host = "0.0.0.0"
    port = 8080 

    server = socketserver.ThreadingTCPServer((host, port), MyTCPHandler)
    server.serve_forever()




