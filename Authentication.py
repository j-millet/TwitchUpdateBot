import os
import json
import requests
import time

def path(filename): #returns whole path to a file (must be in the same folder as code), needed for raspb
        return f"{os.path.dirname(__file__)}\{filename}"

class Authentication:
    token:str
    client_id:str
    client_secret:str
    def __init__(self) -> None:
        with open(path('auth.json')) as f: #read tokens and other auth from file
            d = json.loads(f.read())
            self.token,self.client_id,self.client_secret = [d[x] for x in d]

    def get_oauth(self)->str: #returns an OAuth key for helix api authorization -> "Bearer xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        with open(path("oauth.json"),"r") as f:  #checks if we already have a key that is more than a day from expiry
            d = json.loads(f.read())
            if d['expiration_timestamp'] - time.time() > 24*3600: return f'Bearer {d["oauth"]}'
        
        with open(path("oauth.json"),"w") as f: #generate new auth key
            d = {}
            data={
                "client_id":self.client_id,
                "client_secret":self.client_secret,
                "grant_type":"client_credentials"
            }
            rdata = requests.post("https://id.twitch.tv/oauth2/token",data=data).json()
            d['expiration_timestamp'] = (time.time()+rdata['expires_in'])
            d['oauth'] = rdata["access_token"]
            f.write(json.dumps(d))
            return f'Bearer {d["oauth"]}'