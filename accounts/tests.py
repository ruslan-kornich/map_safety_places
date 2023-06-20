import os
import random
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "safety_places.settings")
django.setup()
from accounts.models import User
from django.conf import settings
from safety.models import SafetyPlace
from faker import Faker
import random

fake = Faker()
Faker.seed(0)

user = User.objects.get(id=1)


def generate_random_coordinates():
    lat_min, lat_max = 44.385, 52.379
    lon_min, lon_max = 22.128, 40.228
    latitude = random.uniform(lat_min, lat_max)
    longitude = random.uniform(lon_min, lon_max)
    return latitude, longitude


def generate_random_comment():
    return fake.words(nb=random.randint(1, 3), ext_word_list=None)


for _ in range(1000):  # Создаем 10 000 SafetyPlace объектов
    latitude, longitude = generate_random_coordinates()
    comment = generate_random_comment()
    SafetyPlace.objects.create(user=user, latitude=latitude, longitude=longitude, comment=comment)
