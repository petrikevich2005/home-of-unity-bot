import logging

#Logger settings
def get_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    handler = logging.FileHandler("bot.log")
    handler.setLevel(logging.INFO)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s | (%(levelname)s): %(message)s (Line: %(lineno)d) [%(filename)s]', datefmt='%d-%m-%Y %I:%M:%S')

    handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(handler)
    logger.addHandler(console_handler)

    return logger