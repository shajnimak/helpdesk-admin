from werkzeug.security import generate_password_hash

password = input("Введите пароль: ")
hashed = generate_password_hash(password)

print("\n🔐 Хешированный пароль:\n")
print(hashed)
