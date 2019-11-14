import sys
import time
import re
import threading
from socket import *

# Take in port number
if len(sys.argv) == 2:
    # input: python mt_proxy.py PORT_NUMBER
    server_port = int(sys.argv[1])
else:
    # Default 8080
    server_port = 8080
logger_file_name = "log.txt"


class Server:
    def __init__(self):
        try:
            self.server_socket = socket(AF_INET, SOCK_STREAM)
            self.server_socket.setsockopt(
                SOL_SOCKET, SO_REUSEADDR, 1)
        except error as e:
            print 'Unable to create/re-use the socket. Error: {}'.format(e)
            message = 'Unable to create/re-use the socket. Error: {}'.format(e)
            self.log_info(message)

        self.server_socket.bind(('', server_port))

        # allowing up to 10 client connections
        self.server_socket.listen(10)
        message = "Host Name: Localhost and Host address: 127.0.0.1 and Host port: {}\n".format(
            str(server_port))
        self.log_info(message)
        print "Listening for clients..."

    def listen_to_client(self):
        """ Listening for client to connect over tcp to the proxy"""
        while True:
            # accepting client connection
            client_connection_socket, client_address = self.server_socket.accept()
            # printing the relevant client details on the server side
            client_details_log = "-------------------- Client Details: --------------------\n"
            client_details_log += "Client host name: {0}\nClient port number: {1}".format(
                str(client_address[0]), str(client_address[1]))
            client_socket_details = getaddrinfo(
                str(client_address[0]), client_address[1])
            client_details_log += "Socket family: {}\n".format(
                str(client_socket_details[0][0]))
            client_details_log += "Socket type: {}\n".format(
                str(client_socket_details[0][1]))
            client_details_log += "Socket protocol: {}\n".format(
                str(client_socket_details[0][2]))
            client_details_log += "Timeout: {}\n".format(
                str(client_connection_socket.gettimeout()))
            client_details_log += "--------------------------------------------------------\n"
            self.log_info(client_details_log)

            message = "Client IP address: {0} and Client port number: {1}\n".format(
                str(client_address[0]), str(client_address[1]))
            self.log_info(message)

            # creating a new thread for every client
            d = threading.Thread(name=str(client_address), target=self.proxy_thread,
                                 args=(client_connection_socket, client_address))
            d.setDaemon(True)
            d.start()
        self.server_socket.close()

    def proxy_thread(self, client_connection_socket, client_address):
        """ Create a new thread for every client connected """
        # starting the timer to calculate the elapsed time
        start_time = time.time()

        client_request = client_connection_socket.recv(1024)
        # if the request is not empty
        if client_request:
            request_length = len(client_request)
            message = "Client with port: {0} request length is {1} bytes\n".format(
                str(client_address[1]), str(request_length))
            self.log_info(message)

            message = "Client with port: {0} generated request: {1}\n".format(
                str(client_address[1]), str(client_request).splitlines()[0])
            self.log_info(message)

            resp_part = client_request.split(' ')[0]
            if resp_part == "GET":
                http_part = client_request.split(' ')[1]
                # strip the http:// portion of url
                double_slash_pos = str(http_part).find("//")
                url_connect = ""
                url_slash_check = list()
                url_slash = str()
                # if http:// portion not found
                if double_slash_pos == -1:
                    url_part = http_part[1:]
                    # get the www.abc.com portion of the url
                    url_connect = url_part.split('/')[0]
                else:
                    # remove / at the end of the url if it exists
                    if http_part.split('//')[1][-1] == "/":
                        url_part = http_part.split('//')[1][:-1]
                        url_connect = url_part.split('/')[0]
                    else:
                        url_part = http_part.split('//')[1]
                        url_connect = url_part.split('/')[0]

                # get the portion after the www.abc.com
                url_slash_check = url_part.split('/')[1:]
                url_slash = ""
                if url_slash_check:
                    for path in url_slash_check:
                        url_slash += "/"
                        url_slash += path
                # checking if port number is provided
                client_request_port_start = str(url_part).find(":")

                # replacing all the non alphanumeric characters with under score
                url_file_name = re.sub('[^0-9a-zA-Z]+', '_', url_part)
                if client_request_port_start == -1:
                    # default port number
                    port_number = 80
                else:
                    port_number = int(url_part.split(':')[1])
                self.find_file(url_file_name, client_connection_socket, port_number,
                               client_address, start_time, url_connect, url_slash)
            else:
                # a call other than GET occurred
                message = "Client with port: {0} generated a call other than GET: {1}\n".format(
                    str(client_address[1]), resp_part)
                client_connection_socket.send(
                    "HTTP/1.1 405 Method Not Allowed\r\n\r\n")
                client_connection_socket.close()
                self.log_info(message)
                message = "HTTP/1.1 405 Method Not Allowed\r\n\r\n"
                self.log_info(message)
        else:
            # a blank request call was made by a client
            client_connection_socket.send("")
            client_connection_socket.close()
            message = "Client with port: {} connection closed\n".format(
                str(client_address[1]))
            self.log_info(message)

    def find_file(self, url_file_name, client_connection_socket, port_number, client_address, start_time, url_connect, url_slash):
        try:
            # getting the cached file for the url if it exists
            cached_file = open(url_file_name, "r")
            # reading the contents of the file
            message = "Client with port: {} Cache hit occurred for the request. Reading from file\n".format(
                str(client_address[1]))
            self.log_info(message)
            # get proxy server details since the data is fetched from cache
            server_socket_details = getaddrinfo("localhost", port_number)
            server_details_message = "<body> Cached Server Details:- <br />"
            server_details_message += "Server host name: localhost <br /> Server port number: {} <br>".format(
                str(port_number))
            server_details_message += "Socket family: {}<br>".format(
                str(server_socket_details[0][0]))
            server_details_message += "Socket type: {}<br>".format(
                str(server_socket_details[0][1]))
            server_details_message += "Socket protocol: {}<br>".format(
                str(server_socket_details[0][2]))
            server_details_message += "Timeout: {}<br> </body>".format(
                str(client_connection_socket.gettimeout()))
            response_message = ""
            # print "reading data line by line and appending it"
            with open(url_file_name) as f:
                for line in f:
                    response_message += line

            response_message += server_details_message

            cached_file.close()

            client_connection_socket.send(response_message)
            end_time = time.time()
            size_message = "Client with port: {0}, Response Length: {1} bytes\n".format(
                str(client_address[1]), str(len(response_message)))
            self.log_info(size_message)
            time_message = "Client with port: {0}, Time Elapsed(RTT): {1} seconds\n".format(
                str(client_address[1]), str(end_time - start_time))
            self.log_info(time_message)

        except IOError as e:
            message = "Client with port: {} Cache miss occurred for the request. Hitting web server\n".format(
                str(client_address[1]))
            self.log_info(message)

            proxy_connection_socket = None
            try:
                # creating the socket from the proxy server
                proxy_connection_socket = socket(AF_INET, SOCK_STREAM)
                # setting time out so that after last packet if not other packet comes socket will auto close
                # in 2 seconds
            except error as e:
                print 'Unable to create the socket. Error: {}'.format(e)
                message = 'Unable to create the socket. Error: {}'.format(e)
                self.log_info(message)
            try:
                proxy_connection_socket.settimeout(2)
                # connecting to the url specified by the client
                proxy_connection_socket.connect((url_connect, port_number))
                # sending GET request from client to the web server
                web_request = str()
                if url_slash:
                    web_request = b"GET /" + \
                        url_slash[1:] + " HTTP/1.1\nHost: " + \
                        url_connect + "\n\n"
                else:
                    web_request = b"GET / HTTP/1.1\nHost: " + url_connect + "\n\n"

                # print "GET web request: "+web_request
                proxy_connection_socket.send(web_request)
                size_message = "Client with port: {0} generated request of length {1} bytes to web server\n".format(
                    str(client_address[1]), str(len(web_request)))
                self.log_info(size_message)
                request_message = "Client with port: {0} generated request to web server as: {1}\n".format(
                    str(client_address[1]), str(web_request))
                self.log_info(request_message)
                # getting the web server response which is expected to be a file
                server_socket_details = getaddrinfo(url_connect, port_number)
                server_details_message = "<body> Web Server Details:- <br />"
                server_details_message += "Server host name: {0} <br /> Server port number: {1}<br />".format(
                    url_connect, str(port_number))
                server_details_message += "Socket family: {}<br />".format(
                    str(server_socket_details[0][0]))
                server_details_message += "Socket type: {}<br />".format(
                    str(server_socket_details[0][1]))
                server_details_message += "Socket protocol: {}<br />".format(
                    str(server_socket_details[0][2]))
                server_details_message += "Timeout: {}<br /> </body>".format(
                    str(client_connection_socket.gettimeout()))
                web_server_response_append = ""
                # to get server response in loop until zero data or timeout of 2 seconds is reached
                timeout_flag = False
                while True:
                    try:
                        web_server_response = proxy_connection_socket.recv(
                            4096)
                    except timeout:
                        # a time out occurred on waiting for server response
                        if len(web_server_response_append) <= 0:
                            timeout_flag = True
                        break
                    if len(web_server_response) > 0:
                        web_server_response_append += web_server_response
                    else:
                        # all the data has been received
                        break

                response_to_file = web_server_response_append
                web_server_response_append += server_details_message
                if timeout_flag:
                    error_response = "HTTP/1.1 408 Request timeout\r\n\r\n"
                    error_response += server_details_message
                    client_connection_socket.send(error_response)
                else:
                    client_connection_socket.send(web_server_response_append)
                end_time = time.time()
                time_message = "Client with port: {0}, Time Elapsed(RTT): {1} seconds\n".format(str(client_address[1]), str(
                    end_time - start_time))
                self.log_info(time_message)

                proxy_temp_file = open(url_file_name, "wb")
                proxy_temp_file.write(response_to_file)
                proxy_temp_file.close()
                size_message = "Client with port: {0} got response of length {1} bytes\n".format(
                    str(client_address[1]), str(len(response_to_file)))
                self.log_info(size_message)

                proxy_connection_socket.close()
            except error as e:
                error_message = ""
                error_message = "HTTP/1.1 404 Not Found\r\n\r\n"
                client_connection_socket.send('HTTP/1.1 404 not found\r\n\r\n')
                end_time = time.time()
                err_occurred_message = "Client with port: {0}, the following error occurred: {1}\n".format(
                    str(client_address[1]), str(e))
                self.log_info(err_occurred_message)
                er_msg = "Client with port: {0}, response sent: {1}\n".format(
                    str(client_address[1]), error_message)
                self.log_info(er_msg)
                time_message = "Client with port: {0}, Time Elapsed(RTT): {1} seconds\n".format(
                    str(client_address[1]), str(end_time - start_time))
                self.log_info(time_message)

        client_connection_socket.close()
        close_connection_message = "Client with port: {}, connection closed\n".format(
            str(client_address[1]))
        self.log_info(close_connection_message)

    def log_info(self, message):
        """ Logger method to write messages to log.txt """
        logger_file = open(logger_file_name, "a")
        logger_file.write(message)
        logger_file.close()


if __name__ == "__main__":
    server = Server()
    server.listen_to_client()
