import logging.config
from os import path, mkdir

from emoji import emojize

PROJECT_ROOT = path.dirname(path.realpath(__file__))
DATABASE = "postgresql://user:pass@localhost:5432/botname"  # override in local settings
BOT_TOKEN = ""
TEMP_FOLDER = path.join(PROJECT_ROOT, '..', 'temp')
NUMBER_OF_ENTRIES_ON_PAGE = 7
ADMINISTRATOR = None
DISTRIBUTION_COMMAND = None
DISTRIBUTION_STOP_COMMAND = None
DISTRIBUTION_DELAY = 60
plus_emo = emojize(":heavy_plus_sign:", use_aliases=True)
minus_emo = emojize(":heavy_minus_sign:", use_aliases=True)
key_emo = emojize(":key:", use_aliases=True)
arrow_right_emo = emojize(":arrow_forward:", use_aliases=True)
arrow_left_emo = emojize(":arrow_backward:", use_aliases=True)
arrow_up_emo = emojize(":arrow_up:", use_aliases=True)
arrow_down_emo = emojize(":arrow_down:", use_aliases=True)
folder_emo = emojize(":file_folder:", use_aliases=True)
lock_emo = emojize(":lock:", use_aliases=True)
exm_mark_emo = emojize(":heavy_exclamation_mark:", use_aliases=True)
x_emo = emojize(":x:", use_aliases=True)
black_x_emo = emojize(":heavy_multiplication_x:", use_aliases=True)
back_emo = emojize(":back:", use_aliases=True)
pencil_emo = emojize(":pencil:", use_aliases=True)
repeat_emo = emojize(":repeat:", use_aliases=True)

new_line = '\n'

opened_databases = {}


logging.config.dictConfig({
                            'version': 1,
                            'disable_existing_loggers': False,
                            'formatters': {
                                'default': {
                                    'format': '%(asctime)s-%(name)s-%(levelname)s-%(message)s'
                                },
                            },
                            'handlers': {
                                'console': {
                                    'level': 'INFO',
                                    'formatter': 'default',
                                    'class': 'logging.StreamHandler',
                                },
                                'deb_file': {
                                    'level': 'DEBUG',
                                    'formatter': 'default',
                                    'class': 'logging.handlers.RotatingFileHandler',
                                    'maxBytes': 10485760,  # 10MB
                                    'backupCount': 10,
                                    'encoding': 'utf8',
                                    'filename': path.join(PROJECT_ROOT, '..', 'logs', 'app.log')
                                },
                                'err_file': {
                                    'level': 'ERROR',
                                    'formatter': 'default',
                                    'class': 'logging.handlers.RotatingFileHandler',
                                    'maxBytes': 10485760,  # 10MB
                                    'backupCount': 5,
                                    'encoding': 'utf8',
                                    'filename': path.join(PROJECT_ROOT, '..', 'logs', 'error.log')
                                },
                            },
                            'loggers': {
                                '': {
                                    'handlers': ['console', 'deb_file', 'err_file'],
                                    'level': 'DEBUG',
                                    'propagate': True
                                },
                            }
                        })
try:
    from .local_settings import *
except ImportError:
    pass


