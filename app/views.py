from flask_admin.contrib.sqla import ModelView
from flask_login import current_user
from .models import *
from . import db
from flask_admin.helpers import get_url
from markupsafe import Markup
from app.utils.telegram_notify import send_telegram_message
from flask import request, redirect, flash


class AdminOnlyView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == 'admin'

    def inaccessible_callback(self, name, **kwargs):
        return "⛔ Доступ запрещён", 403


class UserAdminView(ModelView):
    column_exclude_list = ['password']  # не отображаем пароль

    # Отображаем только нужные поля
    column_list = ('id', 'name', 'email', 'telegram_id', 'telegram_username')
    column_searchable_list = ('name', 'email', 'telegram_username', 'telegram_id')
    form_columns = ('name', 'email', 'telegram_id', 'telegram_username')

    def on_model_change(self, form, model, is_created):
        if form.password.data:
            model.password = form.password.data  # сохраняем без хеширования
        elif not is_created:
            existing = self.session.get(self.model, model.id)
            if existing:
                model.password = existing.password
        return super().on_model_change(form, model, is_created)

    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == 'admin'

    def inaccessible_callback(self, name, **kwargs):
        return "⛔ Доступ запрещён", 403

class EventManagerView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role in ['event_manager', 'admin']

    def inaccessible_callback(self, name, **kwargs):
        return "⛔ Доступ запрещён", 403


class MedicView(ModelView):
    column_list = ('id', 'user', 'reason', 'status', 'date', 'file_download')

    def _file_download(view, context, model, name):
        if model.file_data:
            url = f"/admin/medical_request/{model.id}/download"
            return Markup(f'<a href="{url}" target="_blank">📎 Скачать</a>')
        return '—'

    column_formatters = {
        'file_download': _file_download
    }

    column_labels = {
        'file_download': 'Файл'
    }

    form_columns = ('status',)  # Разрешаем редактировать только статус

    def is_accessible(self):
        return current_user.is_authenticated and current_user.role in ['medic', 'admin']

    def inaccessible_callback(self, name, **kwargs):
        return "⛔ Доступ запрещён", 403

    def after_model_change(self, form, model, is_created):
        # Получаем старое значение из базы
        db.session.expire_all()  # сбрасываем кэш SQLAlchemy
        latest = MedicalRequest.query.get(model.id)

        if latest:
            formatted_date = latest.date.strftime('%Y-%m-%d %H:%M')
            message = (
                f"📄 <b>Обновление по вашей заявке</b>\n"
                f"🆔 Заявка №{latest.id}\n"
                f"📅 Дата подачи: {formatted_date}\n"
                f"📝 Причина: {latest.reason}\n"
                f"📌 <b>Новый статус:</b> {latest.status}"
            )
            send_telegram_message(latest.user_id, message)


def setup_admin_views(admin):
    admin.add_view(UserAdminView(User, db.session))
    admin.add_view(AdminOnlyView(Contact, db.session))
    admin.add_view(AdminOnlyView(Room, db.session))
    admin.add_view(AdminOnlyView(Instruction, db.session))
    admin.add_view(AdminOnlyView(FAQ, db.session))
    admin.add_view(AdminOnlyView(Setting, db.session))
    admin.add_view(AdminOnlyView(SupportRequest, db.session))
    admin.add_view(AdminOnlyView(Club, db.session))
    admin.add_view(EventManagerView(Event, db.session))
    admin.add_view(MedicView(MedicalRequest, db.session))
