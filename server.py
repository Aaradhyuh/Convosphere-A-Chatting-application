#!/usr/bin/env python3
import re
import argparse
import subprocess
from serverSoc import Server

def getArg():
  parser = argparse.ArgumentParser()
  parser.add_argument("-p", "--port", dest="port", metavar="Port_Address", help="Port to listen on")
  return parser.parse_args()

def getIp():
  res = str(subprocess.check_output("ifconfig", shell=True))
  return re.findall(r'(?:inet )(\d+\.\d+\.\d+\.\d+)', res)[1]

def checkIp(ip):
  parts = ip.split(".")
  for i in parts:
    if int(i) < 0 or int(i) > 255:
      print("[-] Invalid IP address")
      exit()
  
def checkPort(port):
  if port > 65535 or port < 0:
    print("[-] Invalid Port number")
    exit()

args = getArg()
ip = getIp()

try:
  port = int(args.port)
except TypeError:
  port = 4444

checkIp(ip)
checkPort(port)

server = Server(ip, port)
server.run()
