import aiohttp
import logging
import random
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from config import TOKEN, NASA_API_KEY
from datetime import datetime, timedelta
from googletrans import Translator

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher()
logging.basicConfig(level=logging.INFO)

# Инициализация переводчика
translator = Translator()


# Функция для перевода текста
def translate_text(text, dest_language='ru'):
    translation = translator.translate(text, dest=dest_language)
    return translation.text


# Функция для получения фотографии дня за случайную дату
async def get_apod_image_for_random_date(api_key: str):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    random_date = start_date + (end_date - start_date) * random.random()
    formatted_date = random_date.date()

    url = f"https://api.nasa.gov/planetary/apod?api_key={api_key}&date={formatted_date}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.json()
            if response.status == 200:
                return data
            else:
                return None


# Функция для получения всех астероидов
async def get_asteroids():
    url = f"https://api.nasa.gov/neo/rest/v1/feed?api_key={NASA_API_KEY}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.json()
            return data


# Функция для получения всех фотографий с Марса
async def get_mars_photos():
    url = f"https://api.nasa.gov/mars-photos/api/v1/rovers/curiosity/photos?sol=1000&api_key={NASA_API_KEY}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.json()
            return data


# Обработка команды /start
@dp.message(Command(commands=['start']))
async def start(message: Message):
    user = message.from_user
    await message.answer(
        f"Привет, {user.first_name}! Вот команды, которые я поддерживаю:\n"
        "/apod - Фотография дня\n"
        "/asteroids - Информация о ближайших астероидах\n"
        "/mars - Картинка с Марса"
    )


# Обработка команды /apod
@dp.message(Command(commands=['apod']))
async def apod(message: Message):
    # Отображаем статус набора сообщения
    await bot.send_chat_action(message.chat.id, action="upload_photo")

    apod_data = await get_apod_image_for_random_date(NASA_API_KEY)
    if apod_data:
        translated_description = translate_text(apod_data['explanation'])
        await message.answer_photo(
            apod_data['url'],
            caption=(
                f"Название: {apod_data['title']}\n"
                f"Описание: {translated_description}"
            )
        )
    else:
        await message.answer("Не удалось получить фотографию дня.")


# Обработка команды /asteroids
@dp.message(Command(commands=['asteroids']))
async def asteroids(message: Message):
    # Отображаем статус набора сообщения
    await bot.send_chat_action(message.chat.id, action="typing")

    data = await get_asteroids()
    if data['near_earth_objects']:
        date = random.choice(list(data['near_earth_objects'].keys()))
        asteroid = random.choice(data['near_earth_objects'][date])
        await message.answer(
            f"Название: {asteroid['name']}\n"
            f"Диаметр: {asteroid['estimated_diameter']['meters']['estimated_diameter_max']} метров\n"
            f"Расстояние до Земли: {asteroid['close_approach_data'][0]['miss_distance']['kilometers']} км\n"
            f"Скорость: {asteroid['close_approach_data'][0]['relative_velocity']['kilometers_per_hour']} км/ч"
        )
    else:
        await message.answer("Нет данных о ближайших астероидах.")


# Обработка команды /mars
@dp.message(Command(commands=['mars']))
async def mars(message: Message):
    # Отображаем статус набора сообщения
    await bot.send_chat_action(message.chat.id, action="upload_photo")

    data = await get_mars_photos()
    if data['photos']:
        random_photo = random.choice(data['photos'])
        await message.answer_photo(
            random_photo['img_src'],
            caption="Фотография с Марса"
        )
    else:
        await message.answer("Не удалось получить фотографию с Марса.")


# Основная функция
async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    import asyncio

    asyncio.run(main())
