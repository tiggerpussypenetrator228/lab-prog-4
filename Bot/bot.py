import logging

import bot_config
import bot_keyboards
import bot_usercache

import rasp_api

from aiogram import Bot, Dispatcher, executor, types

from dateutil import parser as dateparser
from datetime import datetime

import copy

import pytz

logging.basicConfig(level=logging.INFO)

usercache = bot_usercache.load_cache_cookie_registry()
stations = rasp_api.stations_list()

bot = Bot(token=bot_config.TOKEN)
dispatcher = Dispatcher(bot)

@dispatcher.message_handler(commands=["start", "help", "exit"])
@dispatcher.message_handler(lambda message: message.text == bot_config.REPLIES["START"])
@dispatcher.message_handler(lambda message: message.text == bot_config.REPLIES["EXIT"])
async def on_start(message: types.Message):
  cookie = bot_usercache.get_cache_cookie(message.from_id, usercache)

  if cookie["preferred_source_code"] is not None and cookie["preferred_destination_code"] is not None:
    await message.answer(
      bot_config.MESSAGES["WELCOME_BACK"] % (cookie["preferred_source"], cookie["preferred_destination"]), 
      reply=False, 
      reply_markup=bot_keyboards.start(cookie)
    )
  else:
    await message.answer(bot_config.MESSAGES["WELCOME"], reply=False, reply_markup=bot_keyboards.start(cookie))

@dispatcher.message_handler(commands=["select_source"])
@dispatcher.message_handler(lambda message: message.text == bot_config.REPLIES["SELECT_SOURCE"])
async def on_select_source(message: types.Message):
  cookie = bot_usercache.get_cache_cookie(message.from_id, usercache)
  cookie["selecting_stage"] = "SOURCE"

  bot_usercache.update_cache_cookie(cookie, usercache)
  bot_usercache.save_cache_cookie_registry(usercache)

  await message.answer(
    bot_config.MESSAGES["ASK_FOR_SOURCE"], 
    reply=False, 
    reply_markup=bot_keyboards.cached_source(message.from_id, usercache)
  )

@dispatcher.message_handler(commands=["select_destination"])
@dispatcher.message_handler(lambda message: message.text == bot_config.REPLIES["SELECT_DESTINATION"])
async def on_select_destination(message: types.Message):
  cookie = bot_usercache.get_cache_cookie(message.from_id, usercache)
  cookie["selecting_stage"] = "DESTINATION"

  bot_usercache.update_cache_cookie(cookie, usercache)
  bot_usercache.save_cache_cookie_registry(usercache)

  await message.answer(
    bot_config.MESSAGES["ASK_FOR_DESTINATION"], 
    reply=False, 
    reply_markup=bot_keyboards.cached_destination(message.from_id, usercache)
  )

@dispatcher.message_handler(commands=["swap"])
@dispatcher.message_handler(lambda message: message.text == bot_config.REPLIES["SWAP"])
async def on_swap(message: types.Message):
  cookie = bot_usercache.get_cache_cookie(message.from_id, usercache)
  
  if cookie["preferred_source_code"] is None or cookie["preferred_destination_code"] is None:
    await message.answer(bot_config.MESSAGES["CITIES_NOT_SELECTED"], reply=False)

    return

  old_source = cookie["preferred_source"]
  old_source_code = cookie["preferred_source_code"]

  cookie["preferred_source"] = cookie["preferred_destination"]
  cookie["preferred_source_code"] = cookie["preferred_destination_code"]

  cookie["preferred_destination"] = old_source
  cookie["preferred_destination_code"] = old_source_code

  await message.answer(
    bot_config.MESSAGES["SWAPPED"] % (cookie["preferred_source"], cookie["preferred_destination"]),
    reply=False,
    reply_markup=bot_keyboards.search_trips()
  )

@dispatcher.message_handler(commands=["search", "search_more"])
@dispatcher.message_handler(lambda message: message.text == bot_config.REPLIES["SEARCH"])
@dispatcher.message_handler(lambda message: message.text == bot_config.REPLIES["SEARCH_MORE"])
async def on_search(message: types.Message):
  cookie = bot_usercache.get_cache_cookie(message.from_id, usercache)

  if cookie["preferred_source_code"] == None or cookie["preferred_destination_code"] == None:
    await message.answer(bot_config.MESSAGES["CITIES_NOT_SELECTED"], reply=False)

    return

  if message.text == bot_config.REPLIES["SEARCH"]:
    cookie["search_offset"] = 0
  else:
    cookie["search_offset"] += bot_config.TRIP_STRIDE

  trips = rasp_api.search(
    cookie["preferred_source_code"],
    cookie["preferred_destination_code"],
    0,

    100
  ) 

  initial_trips = copy.copy(trips)

  if trips.get("segments", None) is None:
    await message.answer(bot_config.MESSAGES["NO_TRIPS"], reply=False, reply_markup=bot_keyboards.search_trips())

    return

  trips["segments"] = list(filter(
    lambda trip: (trip["thread"]["transport_type"] == "train" or trip["thread"]["transport_type"] == "suburban"),
    trips["segments"])
  )

  trips["segments"] = list(filter(
    lambda trip: 
    dateparser.parse(trip["departure"]).replace(tzinfo=pytz.UTC) 
    > 
    datetime.now().replace(tzinfo=pytz.UTC), 
    
    trips["segments"])
  )

  bot_usercache.update_cache_cookie(cookie, usercache)
  bot_usercache.save_cache_cookie_registry(usercache)

  amount_of_trips = len(trips["segments"])

  if amount_of_trips <= 0:
    await message.answer(bot_config.MESSAGES["NO_TRIPS"], reply=False, reply_markup=bot_keyboards.search_trips())

    logging.warning("Hit filter absence")
    logging.warning(initial_trips)

    return

  if cookie["search_offset"] >= amount_of_trips:
    await message.answer(
      bot_config.MESSAGES["NO_MORE_TRIPS"], 
      reply=False, 
      reply_markup=bot_keyboards.search_trips()
    )

    return

  for trip in trips["segments"][cookie["search_offset"]:cookie["search_offset"] + bot_config.TRIP_STRIDE]:
    trips_message = ""

    train_id = trip["thread"]["number"]

    vehicle_name = "Поезд"
    if trip["thread"]["transport_type"] == "suburban":
      vehicle_name = "Электричка"

    trips_message += "🚂 %s #%s\n" % (vehicle_name, train_id)

    express_type = None
    if trip["thread"]["express_type"] == "express":
      express_type = "Экспресс"
    elif trip["thread"]["express_type"] == "aeroexpress":
      express_type = "Аэроэкспресс"
    
    if express_type is not None:
      trips_message += "❗ %s" % express_type

    first_from_title = trip["from"]["title"]
    second_from_title = trip["from"]["short_title"] or trip["from"]["popular_title"] or first_from_title

    first_to_title = trip["to"]["title"]
    second_to_title = trip["to"]["short_title"] or trip["to"]["popular_title"] or first_to_title

    trips_message += "🏙️ Отбывает из: %s (%s)\n" % (first_from_title, second_from_title)
    trips_message += "🏙️ Прибывает в: %s (%s)\n" % (first_to_title, second_to_title)

    departure_timestamp = dateparser.parse(trip["departure"])
    arrival_timestamp = dateparser.parse(trip["arrival"])

    departure_datetime = " ".join((" ".join(trip["departure"].split("T"))[:-6]).split(" ")[::-1])
    arrival_datetime = " ".join((" ".join(trip["arrival"].split("T"))[:-6]).split(" ")[::-1])

    time_till_departure = departure_timestamp.replace(tzinfo=pytz.UTC) - datetime.now().replace(tzinfo=pytz.UTC)
    left_hours = time_till_departure.seconds // 3600
    left_minutes = (time_till_departure.seconds // 60) % 60

    if left_hours > 0:
      trips_message += "🕒 Выезжает через: <b>%d часов %d минут</b>\n" % (left_hours, left_minutes)
    else:
      trips_message += "🕒 Выезжает через: <b>%d минут</b>\n" % left_minutes

    trips_message += "🕒 Отбытие: <b>%s</b>\n" % departure_datetime
    trips_message += "🕒 Прибытие: <b>%s</b>\n" % arrival_datetime

    time_in_trip = arrival_timestamp - departure_timestamp

    trips_message += "🕒 Время в пути: <b>%d часов %d минут</b>\n" % (
      time_in_trip.seconds // 3600, (time_in_trip.seconds // 60) % 60
    )

    if trip["departure_platform"] and trip["arrival_platform"]:
      trips_message += "📌 Платформа %s -> Платформа %s\n" % (trip["departure_platform"], trip["arrival_platform"])

    if trip["stops"]:
      trips_message += "🚏 Остановки: %s\n" % (trip["stops"])
    
    await message.answer(
      trips_message, 
      reply=False, 
      parse_mode="html", 
      reply_markup=bot_keyboards.search_more_trips()
    )

@dispatcher.message_handler()
async def on_city_selected(message: types.Message):
  cookie = bot_usercache.get_cache_cookie(message.from_id, usercache)
  
  should_update = False
  verified = None

  if cookie["selecting_stage"] == "SOURCE":
    should_update = bot_usercache.select_source(cookie, message.text, stations)

    verified = should_update
  elif cookie["selecting_stage"] == "DESTINATION":
    should_update = bot_usercache.select_destination(cookie, message.text, stations)

    verified = should_update

  if verified is not None:
    if not verified:
      await message.answer(bot_config.MESSAGES["CITY_INVALID"] % message.text, reply=False)

  if should_update:
    bot_usercache.update_cache_cookie(cookie, usercache)
    bot_usercache.save_cache_cookie_registry(usercache)

    if cookie["selecting_stage"] == "SOURCE":
      await message.answer(
        bot_config.MESSAGES["CITY_SELECTED"] % cookie["preferred_source"], 
        reply=False, 
        reply_markup=bot_keyboards.select_destination()
      )
    else:
      await message.answer(
        bot_config.MESSAGES["CITY_SELECTED"] % cookie["preferred_destination"], 
        reply=False, 
        reply_markup=bot_keyboards.search_trips()
      )

    cookie["selecting_stage"] = None

def main():
  executor.start_polling(dispatcher, skip_updates=True)

if __name__ == "__main__":
  main()
