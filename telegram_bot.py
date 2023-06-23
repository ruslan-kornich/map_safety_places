import os
import random
import django
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

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
from django.core.files import File
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator

env = environ.Env(DEBUG=(bool, False))

TOKEN = env("TOKEN")
API_URL = env("API_URL")


bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
fake = Faker()

default_token_generator = PasswordResetTokenGenerator()
location_kb = ReplyKeyboardMarkup(resize_keyboard=True)
location_kb.add(KeyboardButton("Відправити свою геолокацію", request_location=True))


class UserStates(StatesGroup):
    WAITING_FOR_LOCATION = State()
    WAITING_FOR_DESCRIPTION = State()


async def check_user_exists(username: str) -> bool:
    try:
        user = await sync_to_async(User.objects.get)(username=username)
        return True
    except User.DoesNotExist:
        return False


def generate_password(length):
    # All the characters that can be used to generate a password
    chars = string.ascii_letters + string.digits
    # Use a list comprehension to generate a list of random characters, then join them into a string
    password = "".join(random.choice(chars) for _ in range(length))
    return password


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
    try:
        username = message.from_user.username
        if not username:
            # Generate a random username using Faker
            username = fake.user_name()

        if await check_user_exists(username):
            # User already exists, update the token
            user_model = get_user_model()
            user = await sync_to_async(user_model.objects.get)(username=username)
            token = await generate_token(user)
            user.token = token
            await sync_to_async(user.save)()

            await bot.send_message(message.chat.id, "Вас вже зареєстровано")
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
                os.makedirs(os.path.dirname(photo_path), exist_ok=True)
                with open(photo_path, "rb") as photo_file:
                    django_file = File(photo_file)
                    save_sync = sync_to_async(user.avatar.save)
                    await save_sync(f"{username}_avatar.jpg", django_file)
                os.remove(
                    photo_path
                )

            await bot.send_message(
                message.chat.id,
                f"Вас успішно зареєстровано!\n"
                f"Логін: {username}\n"
                f"Пароль: {password}\n",
            )

        # Save the user's token and id to the state context
        await state.update_data(api_auth={"token": user.token, "user_id": user.id})

        await UserStates.WAITING_FOR_LOCATION.set()  # Transition to waiting for location state

        await message.answer(
            "Будь-ласка відправте мені свою геолокацию, або виберіть точку на карті.",
            reply_markup=location_kb,
        )
    except Exception as e:
        logger.exception("An error occurred")
        await bot.send_message(message.chat.id, f"Сталась помилка: {e}\nСпробуй ще раз")


@dp.message_handler(commands=["help", "settings", "something_else"])
async def unknown_command_handler(message: types.Message):
    await bot.send_message(message.chat.id, "Почніть з команди /start ")


@dp.message_handler(
    state=UserStates.WAITING_FOR_LOCATION, content_types=ContentType.TEXT
)
async def wrong_input_in_location_state_handler(message: types.Message):
    await bot.send_message(
        message.chat.id, "Будь-ласка, відправте геолокацію, а не текст."
    )


@dp.message_handler(
    state=UserStates.WAITING_FOR_LOCATION, content_types=ContentType.LOCATION
)
async def location_message_handler(message: types.Message, state: FSMContext):
    try:
        user_location = message.location
        latitude = user_location.latitude
        longitude = user_location.longitude

        # Save the location to the state context
        await state.update_data(location={"latitude": latitude, "longitude": longitude})

        await UserStates.WAITING_FOR_DESCRIPTION.set()  # Transition to waiting for description state

        await bot.send_message(message.chat.id, "Будь-ласка, введіть опис місця.")
    except Exception as e:
        logger.exception("An error occurred")
        await bot.send_message(message.chat.id, f"Сталась помилка: {e}\nСпробуй ще раз")


@dp.message_handler(
    state=UserStates.WAITING_FOR_DESCRIPTION, content_types=ContentType.TEXT
)
async def description_message_handler(message: types.Message, state: FSMContext):
    try:
        description = message.text

        # Get the location from the state context
        state_data = await state.get_data()
        location = state_data.get("location", {})

        await save_location_description(
            location["latitude"], location["longitude"], description, state
        )

        await bot.send_message(message.chat.id, "Ваше місце було збережено.")

        await UserStates.WAITING_FOR_LOCATION.set()  # Transition back to waiting for location state


    except Exception as e:
        print(f"An error occurred: {e}")
        await bot.send_message(message.chat.id, f"Сталась помилка: {e}\nСпробуй ще раз")


@dp.message_handler(
    state=UserStates.WAITING_FOR_DESCRIPTION, content_types=ContentType.ANY
)
async def wrong_input_in_description_state_handler(message: types.Message):
    await bot.send_message(
        message.chat.id,
        "Будь-ласка, введіть опис місця, а не відправляйте геолокацію або інший тип контента.",
    )


async def save_location_description(
        latitude: float, longitude: float, description: str, state: FSMContext
):
    try:
        # Get the user's API authentication data from the state
        state_data = await state.get_data()
        api_auth = state_data.get("api_auth", {})

        headers = {"Authorization": f'Token {api_auth.get("token")}'}

        data = {
            "user": api_auth.get("user_id"),
            "comment": description,
            "latitude": latitude,
            "longitude": longitude,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                    f"{API_URL}/api/safetyplaces/", headers=headers, json=data
            ) as response:
                if response.status == 201:
                    print("Місце успішно додано")
                else:
                    error_message = await response.text()
                    print(
                        f"Помилка при додаванні місця, Код {response.status}. Текст помилки: {error_message}"
                    )
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    from aiogram import executor

    executor.start_polling(dp)
