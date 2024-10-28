import logging
import os
from logging.handlers import RotatingFileHandler


def setup_logging_base_config():
    log_directory = 'logs'
    log_file = os.path.join(log_directory, 'app.log')
    # Создание директории для логов, если она не существует
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s() - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            RotatingFileHandler(log_file, maxBytes=5 * 1024 * 1024, backupCount=2),
            logging.StreamHandler()  # Вывод логов в консоль
        ]
    )
