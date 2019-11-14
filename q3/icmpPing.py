from socket import *
from os import getpid
from sys import platform, argv
from time import time, sleep
from select import select
from statistics import stdev
import struct

ICMP_ECHO_REQUEST = 8


def checksum(str_):
    str_ = bytearray(str_)
    csum = 0
    countTo = (len(str_) // 2) * 2

    for count in range(0, countTo, 2):
        thisVal = str_[count + 1] * 256 + str_[count]
        csum = csum + thisVal
        csum = csum & 0xFFFFFFFF

    if countTo < len(str_):
        csum = csum + str_[-1]
        csum = csum & 0xFFFFFFFF

    csum = (csum >> 16) + (csum & 0xFFFF)
    csum = csum + (csum >> 16)
    answer = ~csum
    answer = answer & 0xFFFF
    answer = answer >> 8 | (answer << 8 & 0xFF00)
    return answer


def receiveOnePing(mySocket, ID, timeout, destAddr):
    timeLeft = timeout
    while 1:
        startedSelect = time()
        whatReady = select([mySocket], [], [], timeLeft)
        howLongInSelect = time() - startedSelect
        if whatReady[0] == []:  # Timeout
            return "Request timed out."

        timeReceived = time()
        recPacket, addr = mySocket.recvfrom(1024)

        icmpHeader = recPacket[20:28]
        icmpType, code, mychecksum, packetID, sequence = struct.unpack(
            "bbHHh", icmpHeader
        )

        if type != 8 and packetID == ID:
            bytesInDouble = struct.calcsize("d")
            timeSent = struct.unpack("d", recPacket[28 : 28 + bytesInDouble])[0]
            return timeReceived - timeSent

        timeLeft = timeLeft - howLongInSelect

        if timeLeft <= 0:
            return "Request timed out."


def sendOnePing(mySocket, destAddr, ID):
    # Header is type (8), code (8), checksum (16), id (16), sequence (16)

    myChecksum = 0

    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
    data = struct.pack("d", time())
    myChecksum = checksum(header + data)

    if platform == "darwin":
        myChecksum = htons(myChecksum) & 0xFFFF
    else:
        myChecksum = htons(myChecksum)

    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
    packet = header + data
    mySocket.sendto(packet, (destAddr, 1))


def buildPing(destAddr, timeout):
    icmp = getprotobyname("icmp")
    open_socket = socket(AF_INET, SOCK_DGRAM, icmp)

    myID = getpid() & 0xFFFF
    sendOnePing(open_socket, destAddr, myID)
    delay = receiveOnePing(open_socket, myID, timeout, destAddr)

    open_socket.close()
    return delay


def ping(host, pings=10, timeout=1):
    dest = gethostbyname(host)
    print("Pinging {}\n".format(dest))

    times = []
    packets_lost = 0

    for seq in range(pings):
        delay = buildPing(dest, timeout)
        if isinstance(delay, str):
            times.append(0)
            packets_lost += 1
            print("64 Bytes to {0}: icmp_seq={1} Packet Lost".format(host, str(seq)))
        else:
            times.append(buildPing(dest, timeout) * 1000)
            print(
                "64 Bytes to {0}: icmp_seq={1} Elapsed Time(RTT)={2} ms".format(
                    host, str(seq), str(round(times[seq], 3))
                )
            )
        sleep(1)

    times = list(filter(lambda time: time != 0, times))
    print("\n--- {} ping statistics ---".format(host))
    print("Min time: {} ms".format(str(round(min(times), 3))))
    print("Max time: {} ms".format(str(round(max(times), 3))))
    print("Avg time: {} ms".format(str(round(sum(times) / len(times), 3))))
    print("Stddev time: {} ms".format(str(round(stdev(times), 3))))
    print("Packets lost: {} (% = {})".format(str(packets_lost), str(packets_lost/pings)))
    return


def main():
    default_host = "8.8.8.8"  # Google
    if len(argv) == 1:
        ping(default_host)
    elif len(argv) == 2:
        if "." in argv[1]:
            ping(argv[1])
        else:
            ping(default_host, int(argv[1]))
    elif len(argv) == 3:
        if "." in argv[1]:
            ping(argv[1], int(argv[2]))
        else:
            ping(argv[2], int(argv[1]))
    else:
        print("Too many parameters")
        print('Usage: python3 icmpPing.py "Host" NumberOfPings')
        print('Example: python3 icmpPing.py "8.8.8.8" 10')


if __name__ == "__main__":
    main()
