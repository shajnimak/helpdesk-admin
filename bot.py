from aiogram import Bot, Dispatcher, types, Router
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
import json
import os
import requests
from dotenv import load_dotenv
import asyncio
from app.utils.database import AsyncSessionLocal
from app.utils.crud import get_token
from datetime import datetime
from aiogram.types import BotCommand


load_dotenv()
router = Router()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
TENANT_ID = os.getenv("TENANT_ID")
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
REDIRECT_URI = "https://helpdesk-admin-r0n0.onrender.com/callback"

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()
dp.include_router(router)

# /start
@router.message(Command("start"))
async def start_command(message: types.Message):
    user_id = str(message.from_user.id)
    async with AsyncSessionLocal() as session:
        access_token = await get_token(session, user_id)

    if access_token:
        email = get_user_email(access_token)
        if email:
            role = define_role(email)
            await message.answer(f"Добро пожаловать, {email}!\nВаша роль: {role}.")
        else:
            await message.answer("Не удалось получить email. Попробуйте авторизоваться заново: /login")
    else:
        await message.answer("Привет! Чтобы пользоваться ботом, авторизуйтесь: /login")

# /login
@router.message(Command("login"))
async def send_login_link(message: types.Message):
    auth_url = (
        f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/authorize"
        f"?client_id={CLIENT_ID}&response_type=code&redirect_uri={REDIRECT_URI}"
        f"&response_mode=query&scope=User.Read Mail.Read Mail.Send&state={message.from_user.id}"
    )
    await message.answer(f"Для авторизации перейдите по ссылке: [Войти]({auth_url})", parse_mode="Markdown")

def get_user_email(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    url = "https://graph.microsoft.com/v1.0/me"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json().get("mail")
    return None

def define_role(email):
    if email:
        local_part = email.split("@")[0]
        if local_part.isdigit():
            return "Студент"
        else:
            return "Преподаватель / Сотрудник"
    return "Неизвестная роль"

@router.message(Command("instructions"))
async def send_instructions_list(message: types.Message):
    try:
        response = requests.get("http://localhost:5001/api/instructions")
        if response.status_code != 200:
            await message.answer("Ошибка при получении инструкций.")
            return

        instructions = response.json()
        if not instructions:
            await message.answer("Инструкции не найдены.")
            return

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=instr["title_ru"],
                    callback_data=f"instr_{instr['id']}"
                )
            ] for instr in instructions
        ])

        await message.answer("📘 Выберите тему инструкции:", reply_markup=keyboard)

    except Exception as e:
        await message.answer(f"Произошла ошибка: {str(e)}")

@router.callback_query(lambda c: c.data.startswith("instr_"))
async def show_instruction(callback_query: CallbackQuery):
    instr_id = callback_query.data.split("_")[1]

    try:
        # Запрашиваем полную информацию по всем (или можно по одному)
        response = requests.get("http://localhost:5001/api/instructions")
        if response.status_code != 200:
            await callback_query.message.answer("Ошибка при получении инструкции.")
            return

        instructions = response.json()
        instr = next((i for i in instructions if str(i["id"]) == instr_id), None)
        if not instr:
            await callback_query.message.answer("Инструкция не найдена.")
            return

        # Проверка на наличие текста или ссылки
        if instr.get("text_ru") and ("http" in instr["text_ru"] or "www." in instr["text_ru"]):
            await callback_query.message.answer(f"🔗 Ссылка: {instr['text_ru']}")
        else:
            await callback_query.message.answer(f"<b>{instr['title_ru']}</b>\n\n{instr['text_ru']}", parse_mode="HTML")

    except Exception as e:
        await callback_query.message.answer(f"Произошла ошибка: {str(e)}")



# /events
@router.message(Command("events"))
async def get_events_command(message: types.Message):
    try:
        response = requests.get("http://localhost:5001/api/events")
        if response.status_code != 200:
            await message.answer("Ошибка при получении данных с API.")
            return

        events = response.json()
        if not events:
            await message.answer("События не найдены.")
            return

        grouped = {
            '🇷🇺 Русский': [(e['title_ru'], e['description_ru'], e['date']) for e in events if e['title_ru'] and e['description_ru']],
            '🇬🇧 English': [(e['title_en'], e['description_en'], e['date']) for e in events if e['title_en'] and e['description_en']],
            '🇰🇿 Қазақша': [(e['title_kk'], e['description_kk'], e['date']) for e in events if e['title_kk'] and e['description_kk']],
        }

        text = "<b>📅 Предстоящие события:</b>\n\n"
        for lang, items in grouped.items():
            if items:
                text += f"<b>{lang}</b>\n"
                for i, (title, desc, date) in enumerate(items, start=1):
                    text += f"\n<b>{i}. {title}</b>\n🕓 {date}\n{desc}\n"
                text += "\n"

        await message.answer(text, parse_mode="HTML")

    except Exception as e:
        await message.answer(f"Произошла ошибка: {str(e)}")

# /faqs
@router.message(Command("faqs"))
async def get_faq_command(message: types.Message):
    try:
        response = requests.get("http://localhost:5001/api/faqs")
        if response.status_code != 200:
            await message.answer("Ошибка при получении данных с API.")
            return

        faqs = response.json()
        if not faqs:
            await message.answer("Вопросы и ответы не найдены.")
            return

        grouped = {
            '🇷🇺 Русский': [(faq['question_ru'], faq['answer_ru']) for faq in faqs if faq['question_ru'] and faq['answer_ru']],
            '🇬🇧 English': [(faq['question_en'], faq['answer_en']) for faq in faqs if faq['question_en'] and faq['answer_en']],
            '🇰🇿 Қазақша': [(faq['question_kk'], faq['answer_kk']) for faq in faqs if faq['question_kk'] and faq['answer_kk']],
        }

        text = "<b>📚 Часто задаваемые вопросы (FAQ):</b>\n\n"
        for lang, items in grouped.items():
            if items:
                text += f"<b>{lang}</b>\n"
                for i, (q, a) in enumerate(items, start=1):
                    text += f"\n<b>{i}. {q}</b>\n{a}\n"
                text += "\n"

        await message.answer(text, parse_mode="HTML")

    except Exception as e:
        await message.answer(f"Произошла ошибка: {str(e)}")

# /clubs
@router.message(Command("clubs"))
async def get_clubs_command(message: types.Message):
    try:
        response = requests.get("http://localhost:5001/api/clubs")
        if response.status_code == 200:
            clubs = response.json()
            if not clubs:
                await message.answer("Клубы не найдены.")
                return

            text = "📚 Список клубов:\n\n"
            for club in clubs:
                text += (
                    f"🔸 <b>{club['name']}</b>\n"
                    f"{club['description']}\n"
                    f"<a href='{club['url']}'>Ссылка на клуб</a>\n\n"
                )
            await message.answer(text, parse_mode="HTML")
        else:
            await message.answer("Ошибка при получении клубов с API.")
    except Exception as e:
        await message.answer(f"Произошла ошибка: {str(e)}")

# /contacts
@router.message(Command("contacts"))
async def get_contacts_command(message: types.Message):
    try:
        response = requests.get("http://localhost:5001/api/contacts")
        if response.status_code == 200:
            contacts = response.json()
            if not contacts:
                await message.answer("Контакты не найдены.")
                return

            text = "📞 Список контактов:\n\n"
            for contact in contacts:
                text += (
                    f"🏢 <b>{contact['department']}</b>\n"
                    f"📱 Телефон: {contact['phone']}\n"
                    f"✉️ Email: {contact['email']}\n"
                    f"📂 Категория: {contact['category']}\n\n"
                )
            await message.answer(text, parse_mode="HTML")
        else:
            await message.answer("Ошибка при получении контактов с API.")
    except Exception as e:
        await message.answer(f"Произошла ошибка: {str(e)}")

# /inbox
@router.message(Command("inbox"))
async def get_inbox(message: types.Message):
    user_id = str(message.from_user.id)
    async with AsyncSessionLocal() as session:
        access_token = await get_token(session, user_id)

    if not access_token:
        await message.answer("Вы не авторизованы! Введите /login.")
        return

    headers = {"Authorization": f"Bearer {access_token}"}
    url = "https://graph.microsoft.com/v1.0/me/messages?$top=5&$orderby=receivedDateTime DESC"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        emails = response.json().get("value", [])
        if not emails:
            await message.answer("Входящие пусты.")
            return

        email_list = []
        for email in emails:
            subject = email.get("subject", "Без темы")
            sender = email.get("from", {}).get("emailAddress", {}).get("address", "Неизвестный отправитель")
            email_list.append(f"📩 <b>{subject}</b>\nОт: {sender}\n")

        await message.answer("\n".join(email_list), parse_mode="HTML")
    else:
        await message.answer(f"Ошибка при получении писем: {response.status_code}")

# ЧЕРНОВИК письма
email_draft = {}
support_draft = {}
medical_draft = {}
med_upload_draft = {}
id_card_draft = {}
reply_draft = {}
outlook_message_map = {}  # user_id -> {short_id: full_email_id}

from uuid import uuid4

@router.message(Command("replyinbox"))
async def get_replyable_messages(message: types.Message):
    user_id = str(message.from_user.id)
    async with AsyncSessionLocal() as session:
        token = await get_token(session, user_id)

    if not token:
        await message.answer("Вы не авторизованы! Введите /login.")
        return

    headers = {"Authorization": f"Bearer {token}"}
    url = "https://graph.microsoft.com/v1.0/me/messages?$top=5&$orderby=receivedDateTime DESC"
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        await message.answer("Ошибка при получении сообщений.")
        return

    emails = response.json().get("value", [])
    if not emails:
        await message.answer("Сообщений нет.")
        return

    outlook_message_map[user_id] = {}  # сброс старых id

    buttons = []
    for email in emails:
        subject = email.get("subject", "Без темы")
        full_id = email["id"]
        short_id = str(uuid4())[:8]  # безопасный и короткий ID
        outlook_message_map[user_id][short_id] = full_id

        buttons.append([InlineKeyboardButton(text=subject, callback_data=f"reply_{short_id}")])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer("📥 Выберите сообщение для ответа:", reply_markup=keyboard)

@router.callback_query(lambda c: c.data.startswith("reply_"))
async def prepare_reply(callback: CallbackQuery):
    user_id = str(callback.from_user.id)
    short_id = callback.data.replace("reply_", "")

    full_id = outlook_message_map.get(user_id, {}).get(short_id)

    if not full_id:
        await callback.message.answer("❌ Истекло время или сообщение не найдено.")
        return

    async with AsyncSessionLocal() as session:
        token = await get_token(session, user_id)

    headers = {"Authorization": f"Bearer {token}"}
    res = requests.get(f"https://graph.microsoft.com/v1.0/me/messages/{full_id}", headers=headers)

    if res.status_code != 200:
        await callback.message.answer("Ошибка при получении письма.")
        return

    email_data = res.json()
    sender_email = email_data.get("from", {}).get("emailAddress", {}).get("address")

    if not sender_email:
        await callback.message.answer("Не удалось определить отправителя.")
        return

    reply_draft[user_id] = {"msg_id": full_id, "to_email": sender_email}
    await callback.message.answer(f"✉️ Введите ваш ответ для {sender_email}:")

# @router.message()
# async def handle_reply_body(message: types.Message):
#     user_id = str(message.from_user.id)
#     if user_id not in reply_draft:
#         return
#
#     reply_info = reply_draft[user_id]
#     reply_body = message.text
#     to_email = reply_info["to_email"]
#
#     success = await send_email(user_id, to_email, reply_body)
#
#     if success:
#         await message.answer(f"✅ Ответ отправлен на {to_email}.")
#     else:
#         await message.answer("❌ Ошибка при отправке.")
#
#     # Здесь можно отправить Telegram уведомление студенту,
#     # если email-to-TG mapping хранится
#     del reply_draft[user_id]


@router.message(Command("idcard"))
async def start_id_card_request(message: types.Message):
    user_id = str(message.from_user.id)
    async with AsyncSessionLocal() as session:
        access_token = await get_token(session, user_id)

    if not access_token:
        await message.answer("Вы не авторизованы. Введите команду /login.")
        return

    id_card_draft[user_id] = {}
    await message.answer("🪪 Пожалуйста, введите сообщение по ID-карте (например, потеря, запрос на замену и т.д.):")


# @router.message()
# async def handle_user_message(message: types.Message):
#     user_id = str(message.from_user.id)
#
#     # Обработка сообщения для техподдержки
#     if user_id in support_draft:
#         message_body = message.text
#         success = await send_support_email(user_id, message_body)
#
#         if success:
#             await message.answer("✅ Ваше сообщение успешно отправлено в техподдержку!")
#         else:
#             await message.answer("❌ Не удалось отправить сообщение. Попробуйте позже.")
#
#         del support_draft[user_id]
#         return
#
#     # Обработка сообщения по ID-карте
#     if user_id in id_card_draft:
#         message_body = message.text
#         recipient = "m.m.shdmn@gmail.com"
#         success = await send_email(user_id, recipient, message_body)
#
#         if success:
#             await message.answer("✅ Ваше сообщение об ID-карте успешно отправлено в соответствующий отдел!")
#         else:
#             await message.answer("❌ Не удалось отправить сообщение. Попробуйте позже.")
#
#         del id_card_draft[user_id]
#         return
#
#     # Обработка черновика обычного письма
#     if user_id in email_draft and "recipient" not in email_draft[user_id]:
#         email_draft[user_id]["recipient"] = message.text
#         await message.answer("Теперь введите текст письма:")
#
#     elif user_id in email_draft and "recipient" in email_draft[user_id]:
#         email_draft[user_id]["message"] = message.text
#         recipient = email_draft[user_id]["recipient"]
#         email_body = email_draft[user_id]["message"]
#
#         success = await send_email(user_id, recipient, email_body)
#
#         if success:
#             await message.answer(f"Письмо отправлено на {recipient}!")
#         else:
#             await message.answer("Ошибка при отправке письма. Попробуйте позже.")
#
#         del email_draft[user_id]

@router.message(Command("medfile"))
async def upload_medical_file_start(message: types.Message):
    user_id = str(message.from_user.id)
    med_upload_draft[user_id] = {}
    await message.answer("📎 Пожалуйста, отправьте фото или PDF с медсправкой.")

@router.message(lambda msg: msg.document or msg.photo)
async def handle_med_file_upload(message: types.Message):
    user_id = str(message.from_user.id)

    if user_id not in med_upload_draft:
        return  # не активен сценарий

    # Получаем файл
    file = message.document or message.photo[-1]  # фото берём максимального размера
    file_id = file.file_id
    file_info = await bot.get_file(file_id)
    file_path = file_info.file_path

    file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_path}"
    file_bytes = requests.get(file_url).content

    # Имя файла
    filename = file.file_name if hasattr(file, "file_name") else f"{file_id}.jpg"
    mime = file.mime_type if hasattr(file, "mime_type") else "image/jpeg"

    # Отправка на сервер
    files = {
        'file': (filename, file_bytes, mime)
    }
    data = {
        'user_id': user_id,
        'reason': 'Справка отправлена через Telegram',
        'date': datetime.utcnow().isoformat()
    }

    try:
        res = requests.post("http://localhost:5001/api/medical_requests", json=data)
        if res.status_code == 201:
            request_id = res.json()["id"]

            # Загрузка файла
            upload_res = requests.post(
                f"http://localhost:5001/api/medical_requests/{request_id}/upload_file",
                files=files
            )

            if upload_res.status_code == 200:
                await message.answer("✅ Медсправка успешно отправлена в деканат.")
            else:
                await message.answer("⚠️ Ошибка при загрузке файла.")
        else:
            await message.answer("❌ Не удалось создать заявку.")
    except Exception as e:
        await message.answer(f"Произошла ошибка: {e}")

    del med_upload_draft[user_id]


@router.message(Command("medical"))
async def start_medical_request(message: types.Message):
    user_id = str(message.from_user.id)
    medical_draft[user_id] = {}
    await message.answer("📝 Введите причину обращения в медпункт:")

# @router.message()
# async def collect_medical_info(message: types.Message):
#     user_id = str(message.from_user.id)
#
#     # Шаг 1: причина
#     if user_id in medical_draft and "reason" not in medical_draft[user_id]:
#         medical_draft[user_id]["reason"] = message.text
#         await message.answer("📅 Введите дату и время записи в формате YYYY-MM-DD HH:MM")
#         return
#
#     # Шаг 2: дата и отправка
#     if user_id in medical_draft and "reason" in medical_draft[user_id] and "datetime" not in medical_draft[user_id]:
#         try:
#             from datetime import datetime
#             date = datetime.strptime(message.text.strip(), "%Y-%m-%d %H:%M")
#             medical_draft[user_id]["datetime"] = date.isoformat()
#
#             # Отправка запроса на Flask API
#             data = {
#                 "user_id": int(user_id),
#                 "reason": medical_draft[user_id]["reason"],
#                 "date": medical_draft[user_id]["datetime"]
#             }
#
#             res = requests.post("http://localhost:5001/api/medical_requests", json=data)
#             if res.status_code == 201:
#                 await message.answer("✅ Ваша заявка в медпункт успешно отправлена. Ожидайте подтверждения.")
#             else:
#                 await message.answer("❌ Ошибка при создании заявки. Попробуйте позже.")
#         except ValueError:
#             await message.answer("❗ Неверный формат. Попробуйте ещё раз (например: 2025-05-18 14:30)")
#         finally:
#             del medical_draft[user_id]

@router.message(Command("support"))
async def ask_support_message(message: types.Message):
    user_id = str(message.from_user.id)
    async with AsyncSessionLocal() as session:
        access_token = await get_token(session, user_id)

    if not access_token:
        await message.answer("Вы не авторизованы! Введите /login.")
        return

    support_draft[user_id] = {}
    await message.answer("✍️ Пожалуйста, введите ваше сообщение для технической поддержки:")

# @router.message()
# async def handle_support_message(message: types.Message):
#     user_id = str(message.from_user.id)
#
#     # Если ожидается сообщение для техподдержки
#     if user_id in support_draft:
#         message_body = message.text
#         success = await send_support_email(user_id, message_body)
#
#         if success:
#             await message.answer("✅ Ваше сообщение успешно отправлено в техподдержку!")
#         else:
#             await message.answer("❌ Не удалось отправить сообщение. Попробуйте позже.")
#
#         del support_draft[user_id]
#         return
#
#     # Оставим это как есть для черновика email
#     if user_id in email_draft and "recipient" not in email_draft[user_id]:
#         email_draft[user_id]["recipient"] = message.text
#         await message.answer("Теперь введите текст письма:")
#
#     elif user_id in email_draft and "recipient" in email_draft[user_id]:
#         email_draft[user_id]["message"] = message.text
#         recipient = email_draft[user_id]["recipient"]
#         email_body = email_draft[user_id]["message"]
#
#         success = await send_email(user_id, recipient, email_body)
#
#         if success:
#             await message.answer(f"Письмо отправлено на {recipient}!")
#         else:
#             await message.answer("Ошибка при отправке письма. Попробуйте позже.")
#
#         del email_draft[user_id]

async def send_support_email(user_id, email_body):
    async with AsyncSessionLocal() as session:
        access_token = await get_token(session, user_id)

    if not access_token:
        return False

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    email_data = {
        "message": {
            "subject": "Обращение в техподдержку через Telegram",
            "body": {
                "contentType": "Text",
                "content": email_body
            },
            "toRecipients": [
                {"emailAddress": {"address": "akzhanimanbazarova@gmail.com"}}
            ]
        },
        "saveToSentItems": "true"
    }

    response = requests.post("https://graph.microsoft.com/v1.0/me/sendMail", json=email_data, headers=headers)
    return response.status_code == 202


@router.message(Command("sendemail"))
async def ask_recipient(message: types.Message):
    user_id = str(message.from_user.id)
    async with AsyncSessionLocal() as session:
        access_token = await get_token(session, user_id)

    if not access_token:
        await message.answer("Вы не авторизованы! Введите /login.")
        return

    email_draft[user_id] = {}
    await message.answer("Введите email получателя:")

# @router.message()
# async def ask_email_body(message: types.Message):
#     user_id = str(message.from_user.id)
#
#     if user_id in email_draft and "recipient" not in email_draft[user_id]:
#         email_draft[user_id]["recipient"] = message.text
#         await message.answer("Теперь введите текст письма:")
#
#     elif user_id in email_draft and "recipient" in email_draft[user_id]:
#         email_draft[user_id]["message"] = message.text
#         recipient = email_draft[user_id]["recipient"]
#         email_body = email_draft[user_id]["message"]
#
#         success = await send_email(user_id, recipient, email_body)
#
#         if success:
#             await message.answer(f"Письмо отправлено на {recipient}!")
#         else:
#             await message.answer("Ошибка при отправке письма. Попробуйте позже.")
#
#         del email_draft[user_id]

@router.message()
async def general_message_handler(message: types.Message):
    user_id = str(message.from_user.id)

    # 1. Сообщение для техподдержки
    if user_id in support_draft:
        message_body = message.text
        success = await send_support_email(user_id, message_body)

        if success:
            await message.answer("✅ Ваше сообщение успешно отправлено в техподдержку!")
        else:
            await message.answer("❌ Не удалось отправить сообщение. Попробуйте позже.")

        del support_draft[user_id]
        return

    # 2. Сообщение по ID-карте
    if user_id in id_card_draft:
        message_body = message.text
        recipient = "akzhanimanbazarova@gmail.com"
        success = await send_email(user_id, recipient, message_body)

        if success:
            await message.answer("✅ Ваше сообщение об ID-карте успешно отправлено в соответствующий отдел!")
        else:
            await message.answer("❌ Не удалось отправить сообщение. Попробуйте позже.")

        del id_card_draft[user_id]
        return

    # 3. Ответ на письмо (reply)
    if user_id in reply_draft:
        reply_info = reply_draft[user_id]
        reply_body = message.text
        to_email = reply_info["to_email"]

        success = await send_email(user_id, to_email, reply_body)

        if success:
            await message.answer(f"✅ Ответ отправлен на {to_email}.")
        else:
            await message.answer("❌ Ошибка при отправке.")

        del reply_draft[user_id]
        return

    # 4. Черновик email — ввод email получателя (если ещё не введён)
    if user_id in email_draft and "recipient" not in email_draft[user_id]:
        email_draft[user_id]["recipient"] = message.text
        await message.answer("Теперь введите текст письма:")
        return

    # 5. Черновик email — ввод текста письма (если email получателя уже есть)
    if user_id in email_draft and "recipient" in email_draft[user_id]:
        email_draft[user_id]["message"] = message.text
        recipient = email_draft[user_id]["recipient"]
        email_body = email_draft[user_id]["message"]

        success = await send_email(user_id, recipient, email_body)

        if success:
            await message.answer(f"Письмо отправлено на {recipient}!")
        else:
            await message.answer("Ошибка при отправке письма. Попробуйте позже.")

        del email_draft[user_id]
        return

    # 6. Обработка медицинской заявки (medical_draft) **
    if user_id in medical_draft:
        if "reason" not in medical_draft[user_id]:
            medical_draft[user_id]["reason"] = message.text
            await message.answer("📅 Введите дату и время записи в формате YYYY-MM-DD HH:MM")
            return

        if "reason" in medical_draft[user_id] and "datetime" not in medical_draft[user_id]:
            try:
                from datetime import datetime
                date = datetime.strptime(message.text.strip(), "%Y-%m-%d %H:%M")
                medical_draft[user_id]["datetime"] = date.isoformat()

                data = {
                    "user_id": int(user_id),
                    "reason": medical_draft[user_id]["reason"],
                    "date": medical_draft[user_id]["datetime"]
                }

                res = requests.post("http://localhost:5001/api/medical_requests", json=data)
                if res.status_code == 201:
                    await message.answer("✅ Ваша заявка в медпункт успешно отправлена. Ожидайте подтверждения.")
                else:
                    await message.answer("❌ Ошибка при создании заявки. Попробуйте позже.")
            except ValueError:
                await message.answer("❗ Неверный формат. Попробуйте ещё раз (например: 2025-05-18 14:30)")
                return  # ждем правильный ввод
            finally:
                del medical_draft[user_id]
            return
    # Если ни одно условие не сработало — игнорируем или можно добавить общий ответ


# Async версия отправки email
async def send_email(user_id, recipient, email_body):
    async with AsyncSessionLocal() as session:
        access_token = await get_token(session, user_id)

    if not access_token:
        return False

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    email_data = {
        "message": {
            "subject": "Сообщение из Telegram бота",
            "body": {
                "contentType": "Text",
                "content": email_body
            },
            "toRecipients": [
                {"emailAddress": {"address": recipient}}
            ]
        },
        "saveToSentItems": "true"
    }

    response = requests.post("https://graph.microsoft.com/v1.0/me/sendMail", json=email_data, headers=headers)
    return response.status_code == 202

async def set_bot_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Начать работу"),
        BotCommand(command="login", description="Авторизация"),
        BotCommand(command="sendemail", description="Отправить email"),
        BotCommand(command="inbox", description="Посмотреть входящие"),
        BotCommand(command="replyinbox", description="Ответить на письмо"),
        BotCommand(command="instructions", description="Список инструкций"),
        BotCommand(command="events", description="Список событий"),
        BotCommand(command="faqs", description="Часто задаваемые вопросы"),
        BotCommand(command="clubs", description="Клубы"),
        BotCommand(command="contacts", description="Контакты"),
        BotCommand(command="medical", description="Запись в медпункт"),
        BotCommand(command="medfile", description="Отправить медсправку"),
        BotCommand(command="support", description="Техподдержка"),
        BotCommand(command="idcard", description="Запрос на ID-карту"),
    ]
    await bot.set_my_commands(commands)


# MAIN
async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await set_bot_commands(bot)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
