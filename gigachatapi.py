

import requests
from uuid import uuid4
import json
import time

class GigaChatAPI:

  def __init__(self, token):
    self.token = token
    self.uuid = str(uuid4())
    self.auth_url = 'https://ngw.devices.sberbank.ru:9443/api/v2/oauth'
    self.models_url = 'https://gigachat.devices.sberbank.ru/api/v1/models'
    self.completions_url = 'https://gigachat.devices.sberbank.ru/api/v1/chat/completions'

    self.headers = {
      'Content-Type': 'application/x-www-form-urlencoded',
      'Accept': 'application/json',
      'RqUID': self.uuid,
      'Authorization': f'Basic {token}'
    }

    self.auth_token = ''
    self.expires_at = ''

  def login(self):
    payload = 'scope=GIGACHAT_API_PERS'
    response = requests.request("POST", self.auth_url, headers=self.headers, data=payload, verify=False)
    self.auth_token, self.expires_at = response.json()['access_token'], response.json()['expires_at']

  def chat(self, messages):
    self.check_token()

    payload = json.dumps({
      "model": "GigaChat",
      "messages": messages,
      "stream": False,
      "repetition_penalty": 1
    })

    headers = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      'Authorization': f'Bearer {self.auth_token}'
    }

    response = requests.request("POST", self.completions_url, headers=headers, data=payload, verify=False)
    print(response.text)
    return response.json()['choices'][0]['message']['content']
  
  def get_expiration(self):
    return self.expires_at
  
  def check_token(self):
    print(self.expires_at)
    if (round(self.expires_at) // 1000 - time.time() < 300):
      self.login()

