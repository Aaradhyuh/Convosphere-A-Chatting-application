import socket as sc
import json
from pymongo import MongoClient
from dateutil import parser
from threading import Thread
# from threading import Lock
from threading import Semaphore
import pandas as pd
import sys
import time
import os

class Server:
  clients = pd.DataFrame()
  def __init__(self, ip, port) -> None:
    self.soc = sc.socket(sc.AF_INET, sc.SOCK_STREAM)
    self.soc.bind((ip, port))
    self.soc.listen(0)

    # self.sendLock = Lock()
    # self.recvLock = Lock()
    # self.sem = Lock()
    self.sem = Semaphore(0)

    self.coll = self.mongoConnect()

    print(f"[+] Waiting for incoming connections on {ip}:{port}...")

  def mongoConnect(self):
    client = MongoClient("127.0.0.1", 27017)
    db = client["chatApp"]
    return db["messages"]
  
  def send(self, data, con):
    encoded = json.dumps(data).encode()
    # self.sendLock.acquire()
    print(end="")
    con.send(encoded)
    # self.sendLock.release()
    print(end="")

  def recv(self, con):
    jsonData = ""
    # self.recvLock.acquire()
    print(end="")
    while True:
      try:
        jsonData += con.recv(1024).decode()
        data = json.loads(jsonData)
        # self.recvLock.release()
        print(end="")
        return data
      except ValueError:
        continue
      except sc.timeout:
        print("hello test")
        continue
    
  def sendMessages(self, data, name):
    con = Server.clients.loc[Server.clients["name"] == name, "con"].iloc[0]
    # print(data)
    self.send(data, con)

  def uploadData(self, data):
    self.coll.insert_one(data)

  def getData(self, name):
    res = self.coll.find({"to": name}).sort("time", -1)
    if self.coll.count_documents({"to": name}) != 0:
      df = pd.DataFrame(list(res))
      df.drop("_id", axis=1, inplace=True)
      df["time"] = df["time"].apply(self.timeToStr)

      return df.to_dict("records")

    else:
      return {}

  def timeToStr(self, time):
    return str(time)

  def closeAndDeleteFromList(self, name):
    con = Server.clients.loc[Server.clients["name"] == name, "con"].iloc[0]
    con.close()

    print(f"[-] Connection ended with {name}")
    Server.clients = Server.clients.drop(
        Server.clients[Server.clients["name"] == name].index
      )

  def cont_recv(self, con):
    jsonData = ""
    while True:
      try:
        jsonData += con.recv(1024).decode()
        data = json.loads(jsonData)

        if data["method"] == "POST":
          dataToUpload = {
            "to": data["to"], 
            "msg": data["msg"], 
            "from": data["from"], 
            "time": parser.parse(data["time"]) 
          }
          self.uploadData(dataToUpload)
        elif data["method"] == "GET":
          recdData = self.getData(data["from"])
          self.sendMessages(recdData, data["from"])

        elif data["method"] == "END":
          self.closeAndDeleteFromList(data["from"])
          return

        elif data["method"] == "KEYS":
          print(end="")
          pub_keys = self.getKeys()
          self.sendMessages(pub_keys.to_dict("records"), data["from"])

        jsonData = ""
      except ValueError:
        continue
      except sc.timeout:
        time.sleep(0.01)
        continue
  
  def getKeys(self):
    if os.path.exists("./pub_keys.csv"):
      pub_keys = pd.read_csv("./pub_keys.csv")
    else:
      pub_keys = pd.DataFrame()

    return pub_keys
  
  def checkAndInsertKey(self, name, key):
    if os.path.exists("./pub_keys.csv"):
      pub_keys = pd.read_csv("./pub_keys.csv")
      if name not in pub_keys["name"].values and key:
        df = pd.DataFrame([{"name": name, "key": key}]) 
        pub_keys = pd.concat([pub_keys, df])

    else:
      pub_keys = pd.DataFrame([{"name": name, "key": key, }])
    
    pub_keys.to_csv("./pub_keys.csv", index=False)


  def handleClient(self, con, addr):
    # self.initLock.acquire()
    # print("1")
    time.sleep(0.01)
    self.send("EST", con)
    time.sleep(0.01)
    # print("2")
    res = self.recv(con)
    time.sleep(0.01)
    # print("3 ")
    nickname = res["name"]
    time.sleep(0.01)
    # print("4")
    


    if res["pub"]:
      pub_key = res["pub"]
      self.checkAndInsertKey(nickname, pub_key)

    print(f"[+] Connection established with {addr}: {nickname}")

    print(end="")
    ip, port = addr
    dict =  {"con": con, "ip": ip, "port": port, "name":nickname}
    dict = pd.DataFrame([dict])

    print(end="")
    Server.clients = pd.concat([Server.clients,dict], ignore_index=True)

    self.sem.release()
    self.cont_recv(con)



  def run(self):
    try:
      while True:
        self.sem.release()
        time.sleep(0.01)
        # print("[+] Listening...")
        con, addr = self.soc.accept()
        con.settimeout(1)
        
        time.sleep(0.01)

        self.sem.acquire()
        thread = Thread(target=self.handleClient, args=(con, addr), daemon=True)
        thread.start()

        self.sem.acquire()
    
    except KeyboardInterrupt:
      for _, client in Server.clients.iterrows():
        client["con"].close()
        self.soc.close()

      sys.exit()



