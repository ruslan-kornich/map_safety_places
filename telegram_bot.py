import environ
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ContentType
import aiohttp
import json
env = environ.Env(
    # set casting, default value
    DEBUG=(bool, False)
)

TOKEN = "6157857080:AAEUkI6FRDnQqqRSMhE6accOA6L8WlHHpV8"

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# Клавиатура с кнопкой геолокации
location_kb = ReplyKeyboardMarkup(resize_keyboard=True)
location_kb.add(KeyboardButton('Отправить геолокацию', request_location=True))

# Ваш URL API и данные для аутентификации
API_URL = 'http://127.0.0.1:8000'
API_AUTH = {'username': 'admin', 'password': 'admin'}

# Кеширование геолокаций пользователей
user_locations = {}


@dp.message_handler(commands='start')
async def start_cmd_handler(message: types.Message):
    await message.answer('Привет! Пожалуйста, отправьте мне свою геолокацию.', reply_markup=location_kb)


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

    # Отправка данных в Django API
    async with aiohttp.ClientSession() as session:
        # Получение токена
        async with session.post(f'{API_URL}/api/token/', data=API_AUTH) as resp:
            data = await resp.text()
            data = json.loads(data)
            token = data['access']

        headers = {'Authorization': f'Bearer {token}'}

        # Отправка данных места
        place_data = {
            'latitude': latitude,
            'longitude': longitude,
            'comment': comment,
            'user': 1,
        }

        async with session.post(f'{API_URL}/api/safetyplaces/', headers=headers, json=place_data) as resp:
            if resp.status == 201:
                await message.answer('Место успешно добавлено!')
            else:
                error_message = await resp.text()  # Получаем текст ответа
                print(f"Ошибка при добавлении места. Код ответа: {resp.status}. Текст ошибки: {error_message}")
                await message.answer('Ошибка при добавлении места.')




if __name__ == '__main__':
    from aiogram import executor

    executor.start_polling(dp)