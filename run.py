import os

from app import create_app

app = create_app()

if __name__ == '__main__':
    # run.py
    app.run(host='0.0.0.0', port=5000)