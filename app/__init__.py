
from flask import Flask
from flask_bootstrap import Bootstrap5
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect

# Инициализация расширений без приложения
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
bootstrap = Bootstrap5()


def create_app(config_class='config.Config'):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Конфигурация приложения
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://my_shop_render_user:8dhqNSXKPDDTIx7dPilCUU4SQirRh8vK@dpg-d01353qdbo4c73dqbts0-a/my_shop_render'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['WTF_CSRF_ENABLED'] = False

    # Если уже инициализировали CSRFProtect
    csrf = CSRFProtect()
    csrf.init_app(app)  # Но будет игнорироваться из-за WTF_CSRF_ENABLED=False
    app.config['SECRET_KEY'] = '3fa85f64a3b128e5a3d5f1f5e9b2c7a1d4e6f3b2a9c8d7e6f5a4b3c2d1e0f9'  # Добавьте секретный ключ

    # Инициализация расширений с приложением
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    bootstrap.init_app(app)

    from app.middleware.visit_logger import init_visit_logger
    init_visit_logger(app)

    if not app.debug and not app.testing:
        import logging
        from logging.handlers import RotatingFileHandler
        import os

        # Создаем папку для логов если ее нет
        if not os.path.exists('logs'):
            os.mkdir('logs')

        # Ротация логов (1 файл 10MB, максимум 3 файла)
        file_handler = RotatingFileHandler(
            'logs/app.log',
            maxBytes=1024 * 1024 * 10,
            backupCount=3
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s '
            '[in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info('AppleShop startup')

    # Настройка Flask-Login
    login_manager.login_view = 'login'  # Измените на имя вашей функции входа
    login_manager.login_message_category = 'info'

    # Импорт моделей и создание таблиц
    with app.app_context():
        from app.models import User
        db.create_all()  # Создаст таблицы, если их нет

        # Декоратор для загрузчика пользователя
        @login_manager.user_loader
        def load_user(user_id):
            return User.query.get(int(user_id))

    from app.routes import main_bp
    app.register_blueprint(main_bp)

    from app.routes import products_bp
    app.register_blueprint(products_bp)

    from app.routes import auth_bp
    app.register_blueprint(auth_bp)

    from app.routes import cart_bp
    app.register_blueprint(cart_bp)

    return app