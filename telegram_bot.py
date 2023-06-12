import os
import random

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'safety_places.settings')
django.setup()
import string
import environ
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ContentType
import aiohttp
import json
from accounts.models import User
from asgiref.sync import sync_to_async
from faker import Faker

env = environ.Env(DEBUG=(bool, False))

TOKEN = env("TOKEN")
API_URL = 'http://127.0.0.1:8000'

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
fake = Faker()

# Keyboard with location button
location_kb = ReplyKeyboardMarkup(resize_keyboard=True)
location_kb.add(KeyboardButton('Отправить геолокацию', request_location=True))

# API authentication data
API_AUTH = {}

# Cache user locations
user_locations = {}


async def check_user_exists(username: int) -> bool:
    try:
        user = await sync_to_async(User.objects.get)(username=username)
        return True
    except User.DoesNotExist:
        return False


# Function to generate a random password
def generate_password(length):
    # All the characters that can be used to generate a password
    chars = string.ascii_letters + string.digits
    # Use a list comprehension to generate a list of random characters, then join them into a string
    password = ''.join(random.choice(chars) for _ in range(length))
    return password


@dp.message_handler(commands='start')
async def start_cmd_handler(message: types.Message):
    global API_AUTH  # Update the global variable inside the function

    username = message.from_user.username
    if await check_user_exists(username):
        await bot.send_message(message.chat.id, 'Вы уже зарегистрированы.')
    else:
        # Generate a random 6-character password
        password = generate_password(6)

        # Create new user in Django
        create_user_sync = sync_to_async(User.objects.create_user)
        user = await create_user_sync(
            username=username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
            email=fake.email(),
            password=password,
            is_superuser=True,  # Set is_superuser value
            is_active=True,  # Set is_active value
        )

        await bot.send_message(
            message.chat.id,
            f'Вы успешно зарегистрированы!\n'
            f'Логин: {username}\n'
            f'Пароль: {password}\n'
        )

        API_AUTH = {'username': username, 'password': password}  # Update API_AUTH here

        await message.answer('Пожалуйста, отправьте мне свою геолокацию.', reply_markup=location_kb)


@dp.message_handler(content_types=ContentType.LOCATION)
async def location_msg_handler(message: types.Message):
    user_locations[message.from_user.id] = (message.location.latitude, message.location.longitude)
    await message.answer('Спасибо! Теперь напишите комментарий к этому месту.')


@dp.message_handler()
async def text_msg_handler(message: types.Message):
    if message.from_user.id not in user_locations:
        return

    latitude, longitude = user_locations[message.from_user.id]
    comment = message.text

    # Send data to Django API
    async with aiohttp.ClientSession() as session:
        # Get token
        async with session.post(f'{API_URL}/api/token/', data=API_AUTH) as resp:
            data = await resp.text()
            data = json.loads(data)
            token = data['access']

        headers = {'Authorization': f'Bearer {token}'}
        username = API_AUTH.get("username")
        user = await sync_to_async(User.objects.get)(username=username)
        # Send place data
        place_data = {
            'latitude': latitude,
            'longitude': longitude,
            'comment': comment,
            'user': user.id,
        }

        async with session.post(f'{API_URL}/api/safetyplaces/', headers=headers, json=place_data) as resp:
            if resp.status == 201:
                await message.answer('Место успешно добавлено!')
            else:
                error_message = await resp.text()  # Get the response text
                print(f"Ошибка при добавлении места. Код ответа: {resp.status}. Текст ошибки: {error_message}")
                await message.answer('Ошибка при добавлении места.')


if __name__ == '__main__':
    from aiogram import executor

    executor.start_polling(dp)
