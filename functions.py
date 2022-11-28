import bcrypt 

def escape_html(current_string):
    current_string = current_string.replace('&', '&amp;')
    current_string = current_string.replace('<', '&lt;')
    current_string = current_string.replace('>', '&gt;')
    return current_string 

def hash_password(password): 
    pass_bytes = password.encode('utf-8') 
    salt = bcrypt.gensalt()
    hash = bcrypt.hashpw(pass_bytes, salt)
    return hash 

def check_password(stored_hash, current_password): 
    current_bytes = current_password.encode('utf-8')
    check = bcrypt.checkpw(current_bytes,stored_hash)
    return check 

def get_digit(string):
    result = ""
    i = 0
    while i < len(string):
        if (string[i]).isdigit():
            result += string[i]
        i += 1

    return int(result) 


def database_list(database):
    current_users = database.find({"id": 1}, {"_id": 0}) 
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

            if eachKey == "token":
                token = each[eachKey]
                file_dicts["token"] = token 
        list_of_data.append(file_dicts)

    return list_of_data