from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_admin import Admin, AdminIndexView
from flask_babel import Babel
from flask_login import LoginManager
from .config import Config

class MyAdminIndexView(AdminIndexView):
    def __init__(self):
        super().__init__(template='admin/master.html')

db = SQLAlchemy()
migrate = Migrate()
admin = Admin(name="HelpDesk Admin", index_view=MyAdminIndexView(), template_mode="bootstrap4")
babel = Babel()
login_manager = LoginManager()
login_manager.login_view = 'login'


def get_locale():
    # Можно переключать язык через параметр ?lang=ru / en / kk
    return request.args.get("lang") or "ru"


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    admin.init_app(app)
    babel.init_app(app, locale_selector=get_locale)  # <-- Новый способ
    login_manager.init_app(app)

    from .views import setup_admin_views
    from .auth import auth_bp

    app.register_blueprint(auth_bp)
    setup_admin_views(admin)

    from .models import User
    from app.controllers.contacts_controller import contacts_bp
    from app.controllers.instructions_controller import instructions_bp
    from app.controllers.medical_requests_controller import medical_requests_bp
    from app.controllers.events_controller import events_bp
    from app.controllers.clubs_controller import clubs_bp
    from app.controllers.faq_controller import faq_bp
    from app.controllers.telegram_token_controller import telegram_token_bp
    app.register_blueprint(contacts_bp)
    app.register_blueprint(instructions_bp)
    app.register_blueprint(medical_requests_bp)
    app.register_blueprint(events_bp)
    app.register_blueprint(clubs_bp)
    app.register_blueprint(faq_bp)
    app.register_blueprint(telegram_token_bp)


    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    return app
