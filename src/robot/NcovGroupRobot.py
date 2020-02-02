import re
import time
from src.robot.IdentifyNews import get_identify_result
from src.util.constant import USER_FOCUS_GROUP, SEND_SPLIT, USER_FOCUS_GROUP_NAME, USE_REDIS, BASE_DIR
from src.util.log import LogSupport
from src.util.sqlite_config import SQLiteConnect

"""
针对微信群的功能函数
"""
ls = LogSupport()
def check_whether_identify(text):
    return re.match('^辟谣.+', text) != None

def check_whether_unidentify(text):
    return re.match('^停止辟谣.+', text) != None

def add_identify_group(conn, itchat, user, group):
    group_name = group.replace("辟谣", '')
    target_chatroom = itchat.search_chatrooms(group_name)
    succ = []
    failed = []
    if len(target_chatroom) > 0:
        chatroom_name = target_chatroom[0]['UserName']
        if USE_REDIS:
            conn.sadd(USER_FOCUS_GROUP, chatroom_name)
            conn.sadd(USER_FOCUS_GROUP_NAME, group_name)
            succ.append(group_name)
        else:
            res = conn.add_group_for_user(user, chatroom_name, group_name)
            if res < 0:
                failed.append(group_name)
            else:
                succ.append(group_name)

    else:
        failed.append(group_name)
    return succ, failed

def cancel_identify_group(conn, itchat, user, group):
    group_name = group.replace("停止辟谣", '')
    target_chatroom = itchat.search_chatrooms(group_name)
    succ = []
    failed = []
    if len(target_chatroom) > 0:
        chatroom_name = target_chatroom[0]['UserName']
        if USE_REDIS:
            conn.srem(USER_FOCUS_GROUP, chatroom_name)
            conn.srem(USER_FOCUS_GROUP_NAME, group_name)
            succ.append(group_name)
        else:
            res = conn.cancel_group_for_user(user, group_name)
            if res > 0:
                succ.append(group_name)
            else:
                failed.append(group_name)
    else:
        failed.append(group_name)
    return succ, failed

def identify_news(text_list, itchat, group_name):
    reply = get_identify_result(text_list)
    if reply != None:
        itchat.send(reply, group_name)
        time.sleep(SEND_SPLIT)

def restore_group(conn, itchat, user):
    if USE_REDIS:
        conn.delete(USER_FOCUS_GROUP)
        group_name = conn.smembers(USER_FOCUS_GROUP_NAME)
    else:
        group_name = conn.query_all_group_for_user(user)
    succ_list = []
    failed_list = []
    for gname in group_name:
        succ, failed = add_identify_group(conn, itchat, user, gname)
        succ_list.extend(succ)
        failed_list.extend(failed)

    ls.logging.info("成功恢复的辟谣群聊:{},失败的:{}".format("，".join(succ_list), "，".join(failed_list)))