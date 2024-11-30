import socket as sc
import json
from datetime import datetime
import pandas as pd
from dateutil import parser
import os
import rsa
import base64
import time

class Client:
  def __init__(self, ip, port) -> None:
    self.name = input("Your Name: ")
    self.con = sc.socket(sc.AF_INET, sc.SOCK_STREAM)
    self.con.settimeout(15)
    self.con.connect((ip, port))
    print()

  def send(self, data):
    encoded = json.dumps(data).encode()
    self.con.send(encoded)
    time.sleep(0.01)

  def sendEncrypted(self, data):
    self.recvKeys()

    pub_keys = pd.read_csv(f"{self.name}_pub_keys.csv")
    if data["to"] not in pub_keys["name"].values:
      print("User not found, ask them to create account first...")
      return
    else: 
      pub_pem = pub_keys.loc[pub_keys["name"] == data["to"], "key"].iloc[0]
      # print(pub_pem)
      # print( type(pub_pem))
    # print(data)

    pub_key_partner = rsa.PublicKey.load_pkcs1(pub_pem)
    msg = data["msg"].encode()
    encrypted = rsa.encrypt(msg, pub_key_partner)
    # print("38: ", type(encrypted))
    # base64.b64encode(encrypted)
    # print("39: ", encrypted.decode())

    data["msg"] = base64.b64encode(encrypted).decode()
    encoded = json.dumps(data).encode()
    self.con.send(encoded)

  def recvKeys(self):
    self.send({
      "method": "KEYS",
      "from": self.name
    })

    jsonData = ""
    while True:
      # print("Receiveing keys...")
      time.sleep(0.01)
      try:
        jsonData += self.con.recv(1024).decode()
        # print(jsonData)
        data = json.loads(jsonData)
        if (jsonData == ""):
          print("[-] Connection closed by the server, try again later...")
          self.exit()
        pub_keys = pd.DataFrame(data)
        pub_keys.to_csv(f"{self.name}_pub_keys.csv", index=False)
        return
      except ValueError:
        continue
      except sc.timeout:
          print("[-] Some error occured, try again later...")
          self.exit()

  def recv(self):
    jsonData = ""
    while True:
      try:
        rec = self.con.recv(1024).decode()
        # print("HEREERE")
        # print(rec)

        if ( rec == ""):
          print("[-] Connection closed by the server, try again later...")
          self.exit()

        jsonData += rec
        data = json.loads(jsonData)
        if data == "EST":
          if not self.public_key:
            dic = {
                "name": self.name, 
                "pub": "" 
              }
          else:
            dic = {
                "name": self.name, 
                "pub": self.public_key.save_pkcs1("PEM").decode()
              }
          
          self.send(dic)
          time.sleep(0.01)
          # print("SENT pub key dict")
          self.recvKeys()

        else:
          if (len(data) > 0):
            result = pd.DataFrame(data)
            result["time"] = result["time"].apply(self.strToTime)
            result.drop("to", axis=1, inplace=True)
            result["msg"] = result["msg"].apply(self.decryptMsg)
            print(result)
          else:
            print("No Messages Found!")

          print()

        jsonData = ""
        break
      except ValueError:
        continue
      except BrokenPipeError:
        exit()
      except sc.timeout:
          print("[-] Some error occured, try again later...")
          self.exit()

  def decryptMsg(self, msg):
    return rsa.decrypt(base64.b64decode(msg.encode()), self.key).decode()

  def strToTime(self, time):
    return parser.parse(time)

  def exit(self):
    self.send({
      "method": "END",
      "from": self.name
    })
    self.con.close()
    exit()

  def setEncryption(self):
    if os.path.exists(f"./{self.name}_rsa_key"):
      with open(f"./{self.name}_rsa_key", "rb") as file:
        self.key = rsa.PrivateKey.load_pkcs1(file.read())
        self.public_key = ""
    else:
      self.public_key, self.key = rsa.newkeys(1024)
      with open(f"./{self.name}_rsa_key", "wb") as file:
        file.write(self.key.save_pkcs1("PEM"))
  
  def run(self):
    self.setEncryption()
    self.recv()
    try:
      while True:
        opt = input("""Enter option\t
                    1. Receive Messages\t
                    2. Send Message\t
                    3. Exit\n""")
        match opt:
          case "1":
            toSend = {
              "method": "GET",
              "from": self.name
            }
            # print(toSend)
            self.send(toSend)
            self.recv()
          case "2":
            to = input("To: ")
            data = input("Message: ")
            self.sendEncrypted({
                "method": "POST",
                "to": to, 
                "msg": data, 
                "from": self.name, 
                "time": str(datetime.now())
              })
            print()

          case "3":
            self.exit()
    except KeyboardInterrupt:
      self.exit()
