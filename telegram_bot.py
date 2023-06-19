import os
import random
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "safety_places.settings")
django.setup()
import string
import environ
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ContentType
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
import aiohttp
import json
from accounts.models import User
from asgiref.sync import sync_to_async
from faker import Faker
from typing import Tuple

env = environ.Env(DEBUG=(bool, False))
from django.contrib.auth import get_user_model

TOKEN = env("TOKEN")
API_URL = "http://127.0.0.1:8000"

bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
fake = Faker()
from django.contrib.auth.tokens import PasswordResetTokenGenerator

default_token_generator = PasswordResetTokenGenerator()
# Keyboard with location button
location_kb = ReplyKeyboardMarkup(resize_keyboard=True)
location_kb.add(KeyboardButton("Отправить геолокацию", request_location=True))

# API authentication data
API_AUTH = {}

# Cache user locations
user_locations = {}


# Define user states
class UserStates(StatesGroup):
    WAITING_FOR_LOCATION = State()
    WAITING_FOR_DESCRIPTION = State()


async def check_user_exists(username: str) -> bool:
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
    password = "".join(random.choice(chars) for _ in range(length))
    return password


# Import the File class from Django
from django.core.files import File


# Add the get_profile_photo function above the start_cmd_handler function
async def get_profile_photo(chat_id: int):
    profile_pictures = await dp.bot.get_user_profile_photos(chat_id)
    if profile_pictures.total_count == 0:
        return None

    photo_path = f"media/avatars/{chat_id}.jpg"

    await profile_pictures.photos[0][-1].download(photo_path)

    return photo_path


async def generate_token(user):
    # Generate token for the user
    token = default_token_generator.make_token(user)
    return token


async def get_user_by_token(token):
    # Get user by token
    user_model = get_user_model()
    user = await sync_to_async(user_model.objects.get_by_natural_key)(token)
    return user


@dp.message_handler(commands="start")
async def start_cmd_handler(message: types.Message, state: FSMContext):
    global API_AUTH  # Update the global variable inside the function

    username = message.from_user.username
    if await check_user_exists(username):
        # User already exists, update the token
        user_model = get_user_model()
        user = await sync_to_async(user_model.objects.get)(username=username)
        token = await generate_token(user)
        user.token = token
        await sync_to_async(user.save)()

        await bot.send_message(message.chat.id, "Вы уже зарегистрированы.")
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
            is_active=True,
            is_staff=True,
        )
        set_password_sync = sync_to_async(user.set_password)
        await set_password_sync(password)
        save_sync = sync_to_async(user.save)
        await save_sync()

        # Download and save the profile photo
        photo_path = await get_profile_photo(message.chat.id)
        if photo_path is not None:
            with open(photo_path, "rb") as photo_file:
                django_file = File(photo_file)
                save_sync = sync_to_async(user.avatar.save)
                await save_sync(f"{username}_avatar.jpg", django_file)

        await bot.send_message(
            message.chat.id,
            f"Вы успешно зарегистрированы!\n"
            f"Логин: {username}\n"
            f"Пароль: {password}\n",
        )

    API_AUTH = {"token": user.token, "user_id": user.id}  # Update API_AUTH here

    await UserStates.WAITING_FOR_LOCATION.set()  # Transition to waiting for location state

    await message.answer(
        "Пожалуйста, отправьте мне свою геолокацию.", reply_markup=location_kb
    )


@dp.message_handler(
    content_types=ContentType.LOCATION, state=UserStates.WAITING_FOR_LOCATION
)
async def location_msg_handler(message: types.Message, state: FSMContext):
    # Handle location message
    latitude = message.location.latitude
    longitude = message.location.longitude

    # Save location in user_locations dictionary
    user_locations[message.chat.id] = {"latitude": latitude, "longitude": longitude}

    await UserStates.WAITING_FOR_DESCRIPTION.set()  # Transition to waiting for description state

    await message.answer("Теперь напишите комментарий к этому месту.")


@dp.message_handler(state=UserStates.WAITING_FOR_DESCRIPTION)
async def description_msg_handler(message: types.Message, state: FSMContext):
    # Handle description message
    description = message.text

    # Get location from user_locations dictionary
    location = user_locations.get(message.chat.id)

    if location:
        # Save location and description to database or perform necessary actions
        await save_location_description(
            location["latitude"], location["longitude"], description
        )

        # Clear the location from user_locations dictionary
        user_locations.pop(message.chat.id)

        await UserStates.WAITING_FOR_LOCATION.set()  # Transition back to waiting for location state

        await message.answer("Место успешно добавлено.")
    else:
        await message.answer("Произошла ошибка. Попробуйте еще раз.")


async def save_location_description(
        latitude: float, longitude: float, description: str
):
    headers = {"Authorization": f'Token {API_AUTH.get("token")}'}

    data = {
        "user": API_AUTH.get("user_id"),  # Передайте значение ID пользователя
        "comment": description,  # Передайте значение комментария
        "latitude": latitude,
        "longitude": longitude,
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
                f"{API_URL}/api/safetyplaces/", headers=headers, json=data
        ) as response:
            if response.status == 201:
                print("Место успешно добавлено!")
            else:
                error_message = await response.text()
                print(
                    f"Ошибка при добавлении места. Код ответа: {response.status}. Текст ошибки: {error_message}"
                )


if __name__ == "__main__":
    from aiogram import executor

    executor.start_polling(dp, skip_updates=True)
