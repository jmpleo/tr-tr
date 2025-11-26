import os
import logging
import torch
from datetime import datetime
from app import App
from utils import resource_path


def setup_logging():
    log_file = f'{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.log'
    logs_path = resource_path('logs')

    if not os.path.exists(logs_path):
        os.makedirs(logs_path)

    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] - [%(name)s] - [%(levelname)s] - %(message)s',
        filename=os.path.join(logs_path, log_file),
        filemode='a'
    )

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter('[%(asctime)s] - [%(name)s] - [%(levelname)s] - %(message)s'))
    logging.getLogger().addHandler(console_handler)


if __name__ == "__main__":
    setup_logging()
    main_app = App()
    main_app.run()
