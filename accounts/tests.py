from faker import Faker

fake = Faker()
random_email = fake.email()
print(random_email)
