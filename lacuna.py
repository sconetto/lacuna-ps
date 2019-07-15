import socket
import sys
import time
import re
import ipdb

server_commands = {
    1: "tell me more",
    2: "send again",
    3: "stop"
}

coordinates = []

def get_encription_key(message):
    test_msg = message
    while True:
        key = [ord(a) ^ ord(b) for a,b in zip('Vader', test_msg)]
        if len(set(key)) == 1:
            key = key[0]
            print(f'Key found!\nKey: {key}')
            break
        else:
            print('Key not found!')
            test_msg = test_msg[1:]

    return key 


def verify_checksum(data):
    translated = data.decode('utf-8')
    check_number = int(translated[-1])
    check = [ord(a) for a in translated[2:-1]]
    checksum = sum(check) + int(check_number)
    verify = int(str(checksum)[-1]) + int(str(checksum)[-2])
    if verify is check_number:
        print('Checksum is OK!')
    else:
        print('Checksum doesn\'t match!')
        return False
    return True


def close_connection(sock):
    msg = bytes(server_commands[3], 'ascii')
    sock.sendall(msg)
    sock.close()
    return


def get_coordinates(message):
    regex = r"x+\d+y\d+"
    coord = re.findall(regex, message)
    if len(coord) is 1:
        return coord[0]
    else:
        return False

def encrypt_coordinates_to_rebels(data, exponent, modulus):
    msg = data
    final_message = ''
    for letter in msg:
        value = letter
        encrypted_letter = str(((value ** exponent) % modulus) % 255)
        final_message += encrypted_letter
    final_message = bytes(final_message, 'ascii')
    size = len(final_message)
    binary = (bin(size)).rsplit('b')[1]
    if len(binary) < 64:
        zeros = '0' * (64 - len(binary))
        binary = zeros + binary
    lsb = binary[-8:]
    msb = binary[:8]
    lsb = int(lsb, 2).to_bytes(8 // 8, byteorder='big')
    msb = int(msb, 2).to_bytes(8 // 8, byteorder='big') 
    final_message = msb + lsb + final_message
    return final_message




def lacuna():
    global coordinates
    emp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    rebel_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ip = "lacuna-admission.brazilsouth.cloudapp.azure.com"
    rebel_port = 31955
    empire_port = 21955
    token = ""

    print(f'Connecting into imperial\'s server:\nADDR: {ip} - PORT: {empire_port}')
    server_addr = (ip, empire_port)
    emp_sock.connect(server_addr)
    print(f'Connecting into rebel\'s server:\nADDR: {ip} - PORT: {rebel_port}')
    server_addr = (ip, rebel_port)
    rebel_sock.connect(server_addr)

    try:
        msg = bytes(token, 'ascii')
        print(f'Seding access token to imperial server...')
        emp_sock.sendall(msg)
        print(f'Seding access token to rebels server...')
        rebel_sock.sendall(msg)
        print(f'Awaiting for response...')
        time.sleep(5)
        emp_data = emp_sock.recv(4096)
        rebel_data = rebel_sock.recv(4096)
        print(f'Response received!')
        while not verify_checksum(emp_data):
            print(f'Resending imperial identity...')
            msg = bytes(token, 'ascii')
            print(f'Seding access token to server...')
            emp_sock.sendall(msg)
            print(f'Awaiting for response...')
            time.sleep(5)
            emp_data = emp_sock.recv(4096)
            print(f'Response received!')

        response = emp_data.decode('utf-8')[2:-1]
        print(f'Received message: {response}')

        # Rebels connection
        cyper = rebel_data.decode('utf-8')
        cyper = cyper.rsplit(' ')
        exponent, modulus = cyper[0], cyper[1]
        print(f'Received message from rebels:\nExponent: {exponent} - Modulus: {modulus}')
        while True:
            print(f'Getting next message...')
            msg = bytes(server_commands[1], 'ascii')
            emp_sock.sendall(msg)
            print(f'Awaiting for response...')
            time.sleep(5)
            data = emp_sock.recv(4096)
            print(f'Response received')
            translated = data.decode('utf-8', 'ignore')[2:]
            print(f'Received message: {translated}')
            key = get_encription_key(translated)
            decripted = ''
            for a in translated:
                decripted += chr(ord(a) ^ key)

            print(f'Decripted message: {decripted}')
            print(f'Getting coordinates...')
            if get_coordinates(decripted):
                coord = get_coordinates(decripted)
                coordinates.append(coord)
                rebels_msg = encrypt_coordinates_to_rebels(
                    data[2:-1],
                    int(exponent),
                    int(modulus)
                )
                print(f'Sending message to rebels!!!\nMessage: {rebels_msg}')
                rebel_sock.sendall(rebels_msg)
                time.sleep(5)
                response = rebel_sock.recv(4096)
                response = response.decode('utf-8')
                if response == 'Game over!':
                    print(f'Failed to send message to rebels!')
                    break
            print(f'Coordinates (so far): {coordinates}')
        close_connection(emp_sock)

    except Exception as e:
        print(e)
        close_connection(emp_sock)
        close_connection(rebel_port)

if __name__ == '__main__':
    lacuna()