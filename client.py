#!/usr/bin/env python3
import argparse
from clientSoc import Client


def getArgs():
  parser = argparse.ArgumentParser()
  parser.add_argument("-s", "--server", metavar="ip_address", dest="serverIp", help="IP address of the server to connect to", required=True)
  parser.add_argument("-p", "--port", metavar="port_number", dest="serverPort", help="Port of the server to connect to", required=True)
  return parser.parse_args()

def checkIp(ip):
  parts = ip.split(".")
  if len(parts) != 4:
    print("[-] Invalid IP address")
    exit()
  for i in parts:
    if int(i) < 0 or int(i) > 255:
      print("[-] Invalid IP address")
      exit()

def checkPort(port):
  if port >= 65535 or port < 0:
    print("[-] Invalid Port number")
    exit()

args = vars(getArgs())
ip, port = (args["serverIp"], int(args["serverPort"]))

checkIp(ip)
checkPort(port)

client = Client(ip, port)
client.run()

