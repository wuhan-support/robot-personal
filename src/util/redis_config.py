import os

import redis
from src.util.constant import REDIS_HOST, STATE_NCOV_INFO, REDIS_HOST_DOCKER, USE_REDIS, DATA_DIR
import json

from src.util.log import LogSupport

ls = LogSupport()
def connect_redis():
    pool = judge_pool()
    conn = redis.Redis(connection_pool=pool)
    return conn

def get_pool():
    pool = redis.ConnectionPool(host=REDIS_HOST, port=6379, decode_responses=True)
    return pool

def connect_docker_redis():
    pool = redis.ConnectionPool(host=REDIS_HOST_DOCKER, port=6379, decode_responses=True)
    return pool

# 因docker中的redis与直接访问redis的host不一致，所以在这里判断
def judge_pool():
    try:
        pool = get_pool()
        conn = redis.Redis(connection_pool=pool)
        conn.set('redis_success', 1)
        return pool
    except BaseException:
        try:
            docker_pool = connect_docker_redis()
            conn = redis.Redis(connection_pool=docker_pool)
            conn.set('redis_success', 2)
            return docker_pool
        except BaseException as e:
            print("Failed to connect redis:", e)
            raise e

def save_json_info(conn, key, data):
    if USE_REDIS:
        conn.rpush(key, json.dumps(data, ensure_ascii=False))
    else:
        path = os.path.join(DATA_DIR, key + ".json")
        with open(path, 'w', encoding='utf-8') as w:
            json.dump(data, w, ensure_ascii=False)

def save_json_info_as_key(conn, key, data):
    if USE_REDIS:
        conn.set(key, json.dumps(data, ensure_ascii=False))
    else:
        path = os.path.join(DATA_DIR, key + ".json")
        with open(path, 'w', encoding='utf-8') as w:
            json.dump(data, w, ensure_ascii=False)

def load_last_info(conn):
    if USE_REDIS:
        data_len = conn.llen(STATE_NCOV_INFO)
        if data_len == 0:
            return None
        elif data_len >= 10:
            conn.lpop(STATE_NCOV_INFO)
        last = json.loads(conn.lrange(STATE_NCOV_INFO, -1, -1)[0])
        return last
    else:
        try:
            path = os.path.join(DATA_DIR, STATE_NCOV_INFO + ".json")
            with open(path, 'r', encoding='utf-8') as r:
                data = json.load(r)
            return data
        except BaseException as e:
            ls.logging.exception(e)
            return None


