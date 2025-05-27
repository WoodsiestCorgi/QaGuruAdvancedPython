# QaGuruAdvancedPython
Домашнее задание для курса Python Advanced

Простой сервис на FastAPI и набор автотестов для него.

Маршруты
--------

POST /register

    Регистрация пользователя. Принимает JSON:
    {
        "email": "user@example.com",
        "password": "your_password"
    }

    Ответ:
    {
        "id": int,
        "token": str
    }

    В случае ошибки (например, отсутствует поле):
    {
        "error": "Missing password"
    }

