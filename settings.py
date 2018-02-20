from emoji import emojize

DATABASE = "database.sqlite"
BOT_TOKEN = ""
TEMP_FOLDER = 'temp'
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


try:
    from local_settings import *
except ImportError:
    pass


