import os
import platform
import random
import re
import time

from src.util.constant import ALL_AREA_KEY, AREA_TAIL, FIRST_NCOV_INFO, NO_NCOV_INFO, ORDER_KEY, UN_REGIST_PATTERN, \
    UN_REGIST_PATTERN2, SHOULD_UPDATE, UPDATE_CITY, USE_REDIS, DATA_DIR, BASE_DIR
from src.util.log import LogSupport
from src.util.redis_config import load_last_info, connect_redis
import json

from src.util.sqlite_config import SQLiteConnect
from src.util.util import get_random_tail, get_random_split, get_random_long_time

ls = LogSupport()
def check_whether_register(text):
    return re.match('^订阅.+', text) != None

def user_subscribe(conn, user, area, jieba):
    """
    接收用户订阅
    :param conn: redis 连接
    :param user: 用户名
    :param area: 发送订阅的文字，如订阅湖北省
    :param jieba: jieba分词的对象，从外部传入是为了加载额外的词库
    :return:
    """
    if USE_REDIS:
        all_area = set(conn.smembers(ALL_AREA_KEY))
    else:
        all_area = set(conn.get_all_area())
    if len(all_area) == 0:
        ls.logging.error("all area key 为空")
    # 去掉订阅两字
    area = area.replace("订阅", '')
    succ_subscribe = []
    failed_subscribe = []
    # 全国有两个地方叫朝阳
    if area == '朝阳':
        return succ_subscribe, ['朝阳']
    if USE_REDIS:
        area_list = list(jieba.cut(area))
        area_list = list(filter(lambda x: len(x) > 1, area_list))
    else:
        area_list = [area]
    tails = ['省', '市', '区', '县','州','自治区', '自治州', '']

    for ar in area_list:
        if ar == '朝阳市' or ar == '朝阳区':
            add_order_key(conn, ar, user)
            succ_subscribe.append(ar)
        elif ar == '中国' or ar == '全国':
            add_order_key(conn, '全国', user)
            succ_subscribe.append('全国')
        else:
            ar = re.subn(AREA_TAIL, '', ar)[0]
            flag = False
            for tail in tails:
                if ar + tail in all_area:
                    # 使该地区的键值唯一，以腾讯新闻中的名称为准，比如湖北省和湖北都使用湖北，而涪陵区和涪陵都使用涪陵区
                    add_order_key(conn, ar + tail, user)
                    succ_subscribe.append(ar + tail)
                    flag =True
                    break
            if not flag:
                failed_subscribe.append(ar)
    return succ_subscribe, failed_subscribe

def find_true_name_for_city(conn, city):
    tails = ['省', '市', '区', '县', '州', '自治区', '自治州', '']
    ar = city
    all_area = set(conn.get_all_area())
    if ar == '朝阳市' or ar == '朝阳区':
        return ar
    elif ar == '中国' or ar == '全国':
        return '全国'
    else:
        ar = re.subn(AREA_TAIL, '', ar)[0]
        for tail in tails:
            if ar + tail in all_area:
                # 使该地区的键值唯一，以腾讯新闻中的名称为准，比如湖北省和湖北都使用湖北，而涪陵区和涪陵都使用涪陵区
                return ar + tail

    return city

def add_order_key(conn, area, user):
    if USE_REDIS:
        conn.sadd(area, user)
        conn.sadd(ORDER_KEY, area)
    else:
        conn.save_subscription(user, area)

def check_whether_unregist(text):
    return re.match(UN_REGIST_PATTERN, text) != None

def get_all_order_area(conn):
    if USE_REDIS:
        all_order_area = conn.smembers(ORDER_KEY)
    else:
        all_order_area = conn.get_all_area()
    return all_order_area

def user_unsubscribe_multi_redis(conn, user, area, jieba):
    """
    取消订阅 （使用redis的情况）
    :param conn:
    :param user:
    :param area:
    :param jieba:
    :return:
    """
    all_order_area = conn.smembers(ORDER_KEY)
    unsubscribe_list = []
    unsubscribe_list_fail = []
    # 全部取消订阅
    if area.find("全部") != -1:
        for area in all_order_area:
            conn.srem(area, user)
        unsubscribe_list.append("全部")
        return unsubscribe_list, unsubscribe_list_fail
    area = re.subn(UN_REGIST_PATTERN2, '', area)[0]
    if USE_REDIS:
        area_list = list(jieba.cut(area))
    else:
        area_list = list(area)
    for ar in area_list:
        flag = False
        ar = re.subn(AREA_TAIL, '', ar)[0]
        if ar in all_order_area:
            ret = conn.srem(ar, user)
            if ret > 0:
                unsubscribe_list.append(ar)
            else:
                unsubscribe_list_fail.append(ar)
        else:
            # 比如用户订阅时使用的是湘西自治州，取消订阅时使用的湘西，则取消一个个查找
            for order_area in all_order_area:
                if order_area.startswith(ar):
                    flag = True
                    ret = conn.srem(order_area, user)
                    if ret > 0:
                        unsubscribe_list.append(order_area)
                    else:
                        unsubscribe_list_fail.append(order_area)
                    break
            if not flag:
                unsubscribe_list_fail.append(ar)
    return unsubscribe_list, unsubscribe_list_fail

def user_unsubscribe_multi_sqlite(conn, user, area, jieba):
    """
    取消订阅（使用sqlite的情况）
    :param conn:
    :param user:
    :param area:
    :param jieba:
    :return:
    """
    unsubscribe_list = []
    unsubscribe_list_fail = []
    area = re.subn(UN_REGIST_PATTERN2, '', area)[0]
    if area.find("全部") != -1:
        conn.cancel_all_subscription(user)
        unsubscribe_list.append('全部')
    else:
        if USE_REDIS:
            area_list = list(jieba.cut(area))
        else:
            area_list = [area]
        for area in area_list:
            res = conn.cancel_subscription(user, area)
            if res > 0:
                unsubscribe_list.append(area)
            else:
                unsubscribe_list_fail.append(area)
    return unsubscribe_list, unsubscribe_list_fail


def get_ncvo_info_with_city(conn, citys, group=False):
    """
    根据传入的城市列表获取疫情信息
    :param conn: redis连接
    :param citys:
    :return:
    """
    try:
        last = load_last_info(conn)
        ncov = []
        if not last:
            return NO_NCOV_INFO.format(", ".join(citys))
        for city in citys:
            if city in last:
                info = last[city]
                ncov.append(FIRST_NCOV_INFO.format(info['city'], info['confirm'], info['dead'], info['heal']))
                if group:
                    today_info = get_today_push_info(info)
                    if len(today_info) > 0:
                        ncov.append(today_info)

            else:
                ncov.append(NO_NCOV_INFO.format(city))
        return "；".join(ncov)
    except BaseException as e:
        ls.logging.exception(e)
        return NO_NCOV_INFO.format(",".join(citys))

def restore_we_friend(conn, itchat):
    """
    添加好友，但是微信已经禁止了网页版添加好友的功能
    :param conn:
    :param itchat:
    :return:
    """
    all_order_area = conn.smembers(ORDER_KEY)
    all_users = set()
    for order_area in all_order_area:
        users = itchat.smembers(order_area)
        all_users.union(users)

    for user in all_users:
        itchat.add_friend(userName=user)

def do_ncov_update(itchat, debug=True):
    ls.logging.info("thread do ncov update info start success-----")
    if USE_REDIS:
        conn = connect_redis()
    else:
        conn = SQLiteConnect(os.path.join(BASE_DIR, 'sqlite.db'))
    try:
        while True:
            if USE_REDIS:
                should_update = conn.get(SHOULD_UPDATE)
                should_update = 0 if should_update == None else should_update
            else:
                should_update = conn.get_update_flag()
            ls.logging.info("update flag:{}".format(should_update))
            if should_update == 1:
                update_city = get_update_city(conn)
                if not update_city:
                    ls.logging.warning("-No update city info")
                else:
                    for city in update_city:
                        push_info = construct_push_info(city)
                        subscribe_user = get_members_by_city(conn, city['city'])
                        ls.logging.info("begin to send info...")
                        for user in subscribe_user:
                            try:
                                ls.logging.info("info:{},user: {}".format(push_info[:20], user))
                                itchat.send(push_info, toUserName=user)
                                # 发送太快容易出事
                                time.sleep(get_random_split())
                            except BaseException as e:
                                ls.logging.error("send failed，{}".format(user))
                                ls.logging.exception(e)
            if debug:
                break
            # 暂停几分钟
            time.sleep(get_random_long_time())
    except BaseException as e:
        ls.logging.error("Error in check ncov update-----")
        ls.logging.exception(e)

def get_update_city(conn):
    if USE_REDIS:
        update_city = conn.get(UPDATE_CITY)
        conn.set(SHOULD_UPDATE, 0)
        if update_city != None:
            update_city = json.loads(update_city)
    else:
        try:
            path = os.path.join(DATA_DIR, UPDATE_CITY +".json")
            with open(path, 'r', encoding='utf-8') as r:
                update_city = json.load(r)
            conn.do_update_flag(0)
        except BaseException as e:
            ls.logging.error("no update city, but flag is 1")
            ls.logging.exception(e)
            update_city = None
    return update_city

def get_members_by_city(conn, city):
    if USE_REDIS:
        subscribe_user = set(conn.smembers(city))
    else:
        subscribe_user = set(conn.get_subscribed_users(city))
    return subscribe_user


def construct_push_info(city):
    area = '{}有数据更新，新增'.format(city['city'])
    n_confirm = '确诊病例{}例'.format(city['n_confirm']) if city['n_confirm'] > 0 else ''
    n_suspect = '疑似病例{}例'.format(city['n_suspect']) if city['n_suspect'] > 0 else ''
    n_heal = '治愈病例{}例'.format(city['n_heal']) if city['n_heal'] > 0 else ''
    n_dead = '死亡病例{}例'.format(city['n_dead']) if city['n_dead'] > 0 else ''
    push_info = list(filter(lambda x: len(x) > 0, [n_confirm, n_suspect, n_heal, n_dead]))
    push_info_str = area + "、".join(push_info) + "；"

    today = '今日{}共累计新增'.format(city['city'])
    t_confirm = '确诊病例{}例'.format(city['t_confirm']) if city['t_confirm'] > 0 else ''
    t_suspect = '疑似病例{}例'.format(city['t_suspect']) if city['t_suspect'] > 0 else ''
    t_heal = '治愈病例{}例'.format(city['t_heal']) if city['t_heal'] > 0 else ''
    t_dead = '死亡病例{}例'.format(city['t_dead']) if city['t_dead'] > 0 else ''
    push_info = list(filter(lambda x: len(x) > 0, [t_confirm, t_suspect, t_heal, t_dead]))
    if len(push_info) > 0:
        push_info_str += today + "、".join(push_info) + "；"

    confirm = '目前共有确诊病例{}例'.format(city['confirm'])
    suspect = '疑似病例{}例'.format(city['suspect']) if city['suspect'] > 0 else ''
    heal = '治愈病例{}例'.format(city['heal'])
    dead = '死亡病例{}例'.format(city['dead'])
    push_info = list(filter(lambda x: len(x) > 0, [confirm, suspect, heal, dead]))
    push_info_str += "、".join(push_info) + "。"
    push_info_str += get_random_tail()
    return push_info_str

def get_today_push_info(city):
    push_info_str = ''
    today = '今日{}共累计新增'.format(city['city'])
    t_confirm = '确诊病例{}例'.format(city['t_confirm']) if city['t_confirm'] > 0 else ''
    t_suspect = '疑似病例{}例'.format(city['t_suspect']) if city['t_suspect'] > 0 else ''
    t_heal = '治愈病例{}例'.format(city['t_heal']) if city['t_heal'] > 0 else ''
    t_dead = '死亡病例{}例'.format(city['t_dead']) if city['t_dead'] > 0 else ''
    push_info = list(filter(lambda x: len(x) > 0, [t_confirm, t_suspect, t_heal, t_dead]))
    if len(push_info) > 0:
        push_info_str += today + "、".join(push_info)
    return push_info_str

def check_help(text):
    text = text.lower()
    return re.match('^help|帮助$', text) != None

