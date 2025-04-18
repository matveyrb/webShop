import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    SECRET_KEY = os.environ.get('3fa85f64a3b128e5a3d5f1f5e9b2c7a1d4e6f3b2a9c8d7e6f5a4b3c2d1e0f9') or '3fa85f64a3b128e5a3d5f1f5e9b2c7a1d4e6f3b2a9c8d7e6f5a4b3c2d1e0f9'
    SQLALCHEMY_DATABASE_URI = os.environ.get('postgresql://my_shop_render_user:8dhqNSXKPDDTIx7dPilCUU4SQirRh8vK@dpg-d01353qdbo4c73dqbts0-a/my_shop_render') or \
        'postgresql://my_shop_render_user:8dhqNSXKPDDTIx7dPilCUU4SQirRh8vK@dpg-d01353qdbo4c73dqbts0-a/my_shop_render'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Настройки для статистики
    STATS_DAYS_TO_KEEP = 30
    STATS_CACHE_TIMEOUT = 3600  # 1 час в секундах