from bot.db import init_db, create_user

init_db()

# ВВЕДИ СВОЇ ДАНІ
full_name = "міндальов владислав"
username = "admin"
password = "123789456"

create_user(full_name, username, password, is_admin=1)

print("Admin user created!")
