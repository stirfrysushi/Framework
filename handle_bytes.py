def get_all_bytes(received_data, self): 
    rn = ("\r\n\r\n").encode() 
    currentData = received_data.split(rn)
    header = currentData[0]
    header_length = len(header)
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

    received_length = len(received_data)
    data_array = bytearray(received_data)
    if received_length < content_length + header_length: 
        while received_length <= content_length + header_length:
            more_data = self.request.recv(2048)
            data_array += bytearray(more_data)
            received_length += len(more_data)

    return data_array