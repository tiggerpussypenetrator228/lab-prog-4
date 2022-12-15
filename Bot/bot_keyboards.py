from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

import bot_config
import bot_usercache

def multiple_choices(texts):
  start_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
  for text in texts:
    start_keyboard.add(KeyboardButton(text))

  return start_keyboard

def single_choice(text):
  return multiple_choices([text])

def start(cookie):
  source_selection_kbd = select_source()

  if cookie["preferred_source_code"] is not None and cookie["preferred_destination_code"] is not None:
    source_selection_kbd.add(KeyboardButton(bot_config.REPLIES["SEARCH"]))
    source_selection_kbd.add(KeyboardButton(bot_config.REPLIES["SWAP"]))

  return source_selection_kbd

def select_source():
  return single_choice(bot_config.REPLIES["SELECT_SOURCE"])

def select_destination():
  return multiple_choices([bot_config.REPLIES["SELECT_DESTINATION"], bot_config.REPLIES["EXIT"]])

def search_trips():
  return multiple_choices([bot_config.REPLIES["SEARCH"], bot_config.REPLIES["SWAP"], bot_config.REPLIES["EXIT"]])

def search_more_trips():
  return multiple_choices([bot_config.REPLIES["SEARCH_MORE"], bot_config.REPLIES["SWAP"], bot_config.REPLIES["EXIT"]])

def cached_source(userid, registry):
  cookie = bot_usercache.get_cache_cookie(userid, registry)
  if cookie["preferred_source"] is None:
    return ReplyKeyboardRemove()

  return single_choice(cookie["preferred_source"])

def cached_destination(userid, registry):
  cookie = bot_usercache.get_cache_cookie(userid, registry)
  if cookie["preferred_destination"] is None:
    return ReplyKeyboardRemove()

  return single_choice(cookie["preferred_destination"])
