from . import db
from datetime import datetime
from flask_login import UserMixin


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    role = db.Column(db.String(50))  # admin, medic и т.д.
    default_language = db.Column(db.String(10))
    password = db.Column(db.Text)  # без хеширования
    telegram_id = db.Column(db.String(100), unique=True)
    telegram_username = db.Column(db.String(100), nullable=True)

    def __str__(self):
        return self.name


class Instruction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title_ru = db.Column(db.String(200))
    title_en = db.Column(db.String(200))
    title_kk = db.Column(db.String(200))
    text_ru = db.Column(db.Text)
    text_en = db.Column(db.Text)
    text_kk = db.Column(db.Text)

    def __str__(self):
        return self.title_ru or "Instruction"


class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    department = db.Column(db.String(100))
    email = db.Column(db.String(100))
    phone = db.Column(db.String(30))
    category = db.Column(db.String(100))

    def __str__(self):
        return self.department


class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_name = db.Column(db.String(100))
    projector_ip = db.Column(db.String(50))
    info = db.Column(db.Text)

    def __str__(self):
        return self.room_name


class FAQ(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_ru = db.Column(db.String(300))
    question_en = db.Column(db.String(300))
    question_kk = db.Column(db.String(300))
    answer_ru = db.Column(db.Text)
    answer_en = db.Column(db.Text)
    answer_kk = db.Column(db.Text)

    def __str__(self):
        return self.question_ru


class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title_ru = db.Column(db.String(200))
    title_en = db.Column(db.String(200))
    title_kk = db.Column(db.String(200))
    description_ru = db.Column(db.Text)
    description_en = db.Column(db.Text)
    description_kk = db.Column(db.Text)
    date = db.Column(db.DateTime, default=datetime.utcnow)

    def __str__(self):
        return self.title_ru


class MedicalRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    reason = db.Column(db.Text)
    status = db.Column(db.String(50), default='Новая')
    date = db.Column(db.DateTime, default=datetime.utcnow)

    file_name = db.Column(db.String(255))
    file_data = db.Column(db.LargeBinary)  # храним файл в бинарном виде
    file_mime = db.Column(db.String(100))

    user = db.relationship("User")

    def __str__(self):
        return f"Request from {self.user.name}"


class SupportRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    message = db.Column(db.Text)
    status = db.Column(db.String(50), default='Открыта')

    user = db.relationship("User")

    def __str__(self):
        return f"Support from {self.user.name}"


class Setting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True)
    value = db.Column(db.String(300))
    encrypted = db.Column(db.Boolean, default=False)

    def __str__(self):
        return self.key


class Club(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    description = db.Column(db.Text)
    url = db.Column(db.Text)

    def __str__(self):
        return self.name


class TelegramToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    telegram_id = db.Column(db.String(100), unique=True, nullable=False)
    token = db.Column(db.String(500), nullable=False)

    def __str__(self):
        return f"TelegramToken({self.telegram_id})"


class UserToken(db.Model):
    __tablename__ = 'user_tokens'

    user_id = db.Column(db.String, primary_key=True)
    token = db.Column(db.String)

    def __init__(self, user_id, token):
        self.user_id = user_id
        self.token = token

    def __str__(self):
        return f"Token for User ID {self.user_id}"
