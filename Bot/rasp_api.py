import rasp_api_config

import functools
import requests

from datetime import datetime

def rasp_method(endpoint):
  def decorator(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
      params = func(*args, **kwargs)

      target_url = rasp_api_config.API_URL + endpoint
      response = requests.get(target_url, params)

      return response.json()

    return wrapper

  return decorator

@rasp_method("search")
def search(source, destination, offset=0, limit=10):
  params = {
    "apikey": rasp_api_config.KEY,

    "from": str(source),
    "to": str(destination),

    "format": "json",
    "lang": "ru_RU",

    "system": "yandex",
    "show_systems": "yandex",

    "offset": str(offset),
    "limit": str(limit),

    "date": datetime.now().isoformat(),

    "add_days_mask": "false",

    "transfers": "false"
  }

  return params

@rasp_method("stations_list")
def stations_list():
  params = {
    "apikey": rasp_api_config.KEY,

    "format": "json",
    "lang": "ru_RU",
  }

  return params
