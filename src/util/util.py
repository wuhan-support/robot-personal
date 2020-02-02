import os
import random
import re

from src.util.constant import INFO_TAILS, USE_REDIS, SHOULD_UPDATE


def move_image(img_path, new_img_path):
    os.rename(img_path, new_img_path)

def remove_image(image_path):
    os.remove(image_path)

def check_image(title):
    return title.find('.png') != -1

def check_identify(text):
    return len(re.findall('谣言|辟谣|假消息|假的|防控|卫健委|卫生部|指挥部|地图|抗击', text)) > 0

def get_random_tail():

    tail = "\n=========" + INFO_TAILS[random.randint(0, 12)]
    return tail

def get_random_split():
    return random.random() * 3

def get_random_split_short():
    return random.random() * 1

def get_random_long_time():
    return random.random() * 60 * 60

def check_should_update(conn):
    if USE_REDIS:
        should_update = conn.get(SHOULD_UPDATE)
        should_update = 0 if should_update == None else should_update
    else:
        should_update = conn.get_update_flag()
    return should_update

def check_dir_exist(dir):
    if os.path.exists(dir) == False:
        os.makedirs(dir)

def parse_identify_res(text, source):
    reply_text = 'em...这个「{}」大概是{}，详细的情况是: {}。\n这里有详细的报道:{}'.format(text[0:20], source['result'].split('-')[1], source['abstract'], source['oriurl'])
    return reply_text

