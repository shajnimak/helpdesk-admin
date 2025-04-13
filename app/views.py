from wtforms import PasswordField
from wtforms.validators import Optional
from flask_admin.contrib.sqla import ModelView
from werkzeug.security import generate_password_hash
from flask_login import current_user
from .models import *
from . import db


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
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role in ['medic', 'admin']

    def inaccessible_callback(self, name, **kwargs):
        return "⛔ Доступ запрещён", 403


def setup_admin_views(admin):
    admin.add_view(UserAdminView(User, db.session))
    admin.add_view(AdminOnlyView(Contact, db.session))
    admin.add_view(AdminOnlyView(Room, db.session))
    admin.add_view(AdminOnlyView(Instruction, db.session))
    admin.add_view(AdminOnlyView(FAQ, db.session))
    admin.add_view(AdminOnlyView(Setting, db.session))
    admin.add_view(AdminOnlyView(SupportRequest, db.session))
    admin.add_view(EventManagerView(Event, db.session))
    admin.add_view(MedicView(MedicalRequest, db.session))
