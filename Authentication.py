import json
import requests
import time
import GuildFileManager

class Authentication:
    token:str
    client_id:str
    client_secret:str
    def __init__(self) -> None:
        with open(GuildFileManager.path('auth.json')) as f: #read tokens and other auth from file
            d = json.loads(f.read())
            self.token,self.client_id,self.client_secret = [d[x] for x in d]

    def get_oauth(self)->str: #returns an OAuth key for helix api authorization -> "Bearer xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        with open(GuildFileManager.path("oauth.json"),"r") as f:  #checks if the saved key that is more than a day from expiry
            d = json.loads(f.read())
            if d['expiration_timestamp'] - time.time() > 24*60*60: 
                return f'Bearer {d["oauth"]}'
        
        with open(GuildFileManager.path("oauth.json"),"w") as f: #generate new auth key if needed
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