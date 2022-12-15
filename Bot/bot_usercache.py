import bot_config

import json

REGISTRY_FILENAME = "usercache.json"

def create_cache_cookie_registry():
  return {}

def save_cache_cookie_registry(registry):
  file = open(REGISTRY_FILENAME, "w")
  file.write(json.dumps(registry, indent=4))
  file.close()

def load_cache_cookie_registry():
  try:
    file = open(REGISTRY_FILENAME, "r")
    if not file:
      return create_cache_cookie_registry()
  except FileNotFoundError:
    return create_cache_cookie_registry()

  registry = json.loads(file.read())
  file.close()

  return registry

def create_cache_cookie(userid):
  return {
    "user": str(userid),

    "selecting_stage": None,

    "preferred_source": None,
    "preferred_destination": None,

    "preferred_source_code": None,
    "preferred_destination_code": None,

    "search_offset": 0
  }

def get_cache_cookie(userid, registry):
  if registry.get(str(userid), None) is None:
    return create_cache_cookie(userid)

  return registry[str(userid)]

def bake_place_name(city):
  return city.lower().replace(".", "").replace(",", "").replace("ё", "е")

def get_city_info(city, stations):
  city = bake_place_name(city)
  if bot_config.CITY_ALIASES.get(city, None) is not None:
    city = bake_place_name(bot_config.CITY_ALIASES[city])

  result = {
    "name": city,
    "code": None
  }

  for country in stations["countries"]:
    for region in country["regions"]:
      for settlement in region["settlements"]:        
        if bake_place_name(settlement["title"]) == city:
          result["name"] = settlement["title"]
          result["code"] = settlement["codes"]["yandex_code"]

          return result

        for station in settlement["stations"]:
          if bake_place_name(station["title"]) == city:
            result["name"] = station["title"]
            result["code"] = station["codes"]["yandex_code"]

            return result

  return result

def select_source(cookie, source, stations=None):
  if stations is not None:
    result = get_city_info(source, stations)
    if result["code"] is None:
      return False

    cookie["preferred_source"] = result["name"]
    cookie["preferred_source_code"] = result["code"]

    return True

  return False

def select_destination(cookie, destination, stations=None):
  if stations is not None:
    result = get_city_info(destination, stations)
    if result["code"] is None:
      return False

    cookie["preferred_destination"] = result["name"]
    cookie["preferred_destination_code"] = result["code"]

    return True

  return False

def add_cache_cookie(cookie, registry):
  registry[cookie["user"]] = cookie

def update_cache_cookie(cookie, registry):
  add_cache_cookie(cookie, registry)
