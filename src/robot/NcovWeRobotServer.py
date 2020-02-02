import itchat
import os
import sys
import platform
curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
BASE_PATH = os.path.split(rootPath)[0]
sys.path.append(BASE_PATH)
from src.ocr.OCR import Image2Title
from src.ocr.TextSummary import get_text_summary
from src.util.util import check_image, check_identify, remove_image, get_random_split_short
from itchat.content import *
from src.robot.NcovWeRobotFunc import *
from src.util.constant import INFO_TAIL, INFO_TAIL_ALL, FOCUS_TAIL, HELP_CONTENT, \
    GROUP_CONTENT_HELP, ONLINE_TEXT, FILE_HELPER, CHAOYANG_INFO, NO_GROUP_CONTENT_HELP
from src.util.redis_config import connect_redis
from src.robot.NcovGroupRobot import *

import jieba
import threading
from src.spider.SpiderServer import start_tx_spider

ocr = Image2Title(topK=5)
if USE_REDIS:
    conn = connect_redis()
else:
    conn = SQLiteConnect(os.path.join(BASE_DIR, 'sqlite.db'))

@itchat.msg_register([TEXT])
def text_reply(msg):
    try:
        if msg['FromUserName'] == itchat.originInstance.storageClass.userName and msg['ToUserName'] != 'filehelper':
            return
        nickname = itchat.originInstance.storageClass.nickName
        if check_whether_register(msg.text):
            succ, failed = user_subscribe(conn, msg.user.UserName, msg.text, jieba)
            if len(failed) == 1 and failed[0] == '朝阳':
                itchat.send(CHAOYANG_INFO, toUserName=msg.user.UserName)
                return
            succ_text = ''
            if len(succ) > 0:
                succ_text = '成功订阅{}的疫情信息!'.format(",".join(succ))
            failed_text = ''
            if len(failed) > 0:
                failed_text = '订阅{}失败，该地区名称不正确或暂无疫情信息。'.format("，".join(failed))
            # msg.user.send('%s: %s' % (succ_text, failed_text))
            ls.logging.info('用户%s: %s %s' % (msg.user.UserName, succ_text, failed_text))
            itchat.send('%s %s' % (succ_text, failed_text), toUserName=msg.user.UserName)
            if len(succ) > 0:
                time.sleep(get_random_split())
                itchat.send(get_ncvo_info_with_city(conn, succ), toUserName=msg.user.UserName)
                area = succ[0]
                if area != '全国' and area != '中国':
                    time.sleep(get_random_split())
                    itchat.send(INFO_TAIL.format(area, area) + get_random_tail(), toUserName=msg.user.UserName)
                else:
                    time.sleep(get_random_split())
                    itchat.send(INFO_TAIL_ALL + get_random_tail(), toUserName=msg.user.UserName)
        elif check_whether_unregist(msg.text):
            if USE_REDIS:
                succ, failed = user_unsubscribe_multi_redis(conn, msg.user.UserName, msg.text, jieba)
            else:
                succ, failed = user_unsubscribe_multi_sqlite(conn, msg.user.UserName, msg.text, jieba)
            succ_text = ''
            if len(succ) > 0:
                succ_text = '成功取消{}的疫情信息订阅'.format("，".join(succ))
            failed_text = ''
            if len(failed) > 0:
                failed_text = '取消{}的疫情信息订阅失败，您好像没有订阅该地区信息或者地区名称错误'.format("，".join(failed))
            ls.logging.info('用户%s: %s %s' % (msg.user.UserName, succ_text, failed_text))
            itchat.send('%s %s' % (succ_text, failed_text), toUserName=msg.user.UserName)
        elif msg['ToUserName'] == FILE_HELPER:
            if check_whether_identify(msg.text):
                succ, failed = add_identify_group(conn, itchat, nickname, msg.text)
                succ_text =''
                failed_text = ''
                if len(succ) > 0:
                    succ_text = '成功关注{}，会自动鉴别该群的疫情谣言'.format("，".join(succ))
                else:
                    failed_text = '关注{}失败，请检查该群名称是否正确'.format("，".join(failed))
                ls.logging.info('用户%s: %s %s' % (msg.user.UserName, succ_text, failed_text))
                itchat.send('%s %s' % (succ_text, failed_text), toUserName=FILE_HELPER)
                if len(succ) > 0:
                    time.sleep(get_random_split_short())
                    itchat.send(FOCUS_TAIL, toUserName=FILE_HELPER)
            elif check_whether_unidentify(msg.text):
                succ, failed = cancel_identify_group(conn, itchat, nickname, msg.text)
                succ_text = ''
                failed_text = ''
                if len(succ) > 0:
                    succ_text = '停止鉴别{}等群的谣言成功'.format("，".join(succ))
                else:
                    failed_text = '停止鉴别{}等群的谣言失败，请检查该群名称是否正确'.format("，".join(failed))
                ls.logging.info('用户%s: %s %s' % (msg.user.UserName, succ_text, failed_text))
                itchat.send('%s %s' % (succ_text, failed_text), toUserName=FILE_HELPER)
            elif check_help(msg.text):
                time.sleep(get_random_split_short())
                itchat.send(HELP_CONTENT, toUserName='filehelper')
            elif msg.text.lower() == 'cx':
                time.sleep(get_random_split_short())
                if USE_REDIS:
                    groups = list(conn.smembers(USER_FOCUS_GROUP_NAME))
                else:
                    groups = conn.query_all_group_for_user(nickname)
                if len(groups) > 0:
                    itchat.send(GROUP_CONTENT_HELP.format("，".join(groups)), toUserName=FILE_HELPER)
                else:
                    itchat.send(NO_GROUP_CONTENT_HELP, toUserName=FILE_HELPER)

            elif msg.text:pass
    except BaseException as e:
        ls.logging.exception(e)


@itchat.msg_register([TEXT, NOTE], isGroupChat=True)
def text_reply(msg):
    if msg.isAt:
        if msg.text.find('查') == -1:
            return
        city = msg.text.split('查')
        if len(city) < 2:
            return
        city = city[1].strip()
        if len(city) > 10:
            return
        if city == '水表':
            itchat.send("水表在门外，请自便！", toUserName=msg.user.UserName)
            return
        if city == '':
            itchat.send("您想查啥？", toUserName=msg.user.UserName)
            return
        if city == '朝阳':
            itchat.send(CHAOYANG_INFO, toUserName=msg.user.UserName)
            return
        city = find_true_name_for_city(conn, city)
        push_info = get_ncvo_info_with_city(conn, [city], True)
        itchat.send(push_info + get_random_tail(), toUserName=msg.user.UserName)
        return
    # 筛掉过短的长文和重复字段过多的长文
    if len(msg.text) < 50 or len(set(msg.text)) < 20:
        return
    # 带有辟谣等字眼的信息直接返回
    if check_identify(msg.text):
        return
    # 判断是在否在关注的群列表里
    if not judge_whether_foucs_group(conn, itchat.originInstance.storageClass.nickName, msg['FromUserName']):
        return
    # 获取文字摘要
    text_list = get_text_summary(msg.text, topK=2)
    # 鉴别
    identify_news(text_list, itchat, msg['FromUserName'])

@itchat.msg_register([SHARING], isGroupChat=True)
def text_reply(msg):
    if msg['FromUserName'] == itchat.originInstance.storageClass.userName and msg['ToUserName'] != 'filehelper':
        return
    if check_identify(msg.text) or len(msg.text) < 10:
        return
    # 判断是在否在关注的群列表里
    if not judge_whether_foucs_group(conn, itchat.originInstance.storageClass.nickName, msg['FromUserName']):
        return
    # 鉴别
    identify_news([msg.text], itchat, msg['FromUserName'])

@itchat.msg_register([SHARING])
def text_reply(msg):
    if msg['FromUserName'] == itchat.originInstance.storageClass.userName and msg['ToUserName'] != 'filehelper':
        return
    if check_identify(msg.text):
        return
    # 鉴别
    identify_news([msg.text], itchat, msg['FromUserName'])

@itchat.msg_register([PICTURE, RECORDING, ATTACHMENT, VIDEO], isGroupChat=True)
def text_reply(msg):
    if msg['FromUserName'] == itchat.originInstance.storageClass.userName and msg['ToUserName'] != 'filehelper':
        return
    if not judge_whether_foucs_group(conn, itchat.originInstance.storageClass.nickName, msg['FromUserName']):
        return
    if check_image(msg.fileName):
        return
        # msg.download(msg.fileName)
        # # new_file = os.path.join(BASE_DIR, 'download_image/') + msg.fileName
        # text_list = ocr(msg.fileName)
        # # 删除图片
        # remove_image(msg.fileName)
        # # 带有辟谣等字眼的信息直接返回
        # if len(text_list) == 0 or check_identify("".join(text_list)):
        #     return
        # text_list = list(filter(lambda x: len(x) > 10, text_list))
        # identify_news(text_list, itchat, msg['FromUserName'])

def judge_whether_foucs_group(conn, user, group):
    # 判断是在否在关注的群列表里
    if USE_REDIS:
        return conn.sismember(USER_FOCUS_GROUP, group)
    else:
        return group in set(conn.query_all_group_id_for_user(user))

def init_jieba():
    if USE_REDIS:
        all_area = conn.get_all_area()
        if len(all_area) == 0:
            ls.logging.error("尚无地区信息")
        for words in all_area:
            jieba.add_word(words)
    return jieba

jieba = init_jieba()

def start_server():

    # 在不同的终端上，需要调整CMDQR的值
    # itchat.auto_login(True, enableCmdQR=2)
    itchat.auto_login(True)
    ls.logging.info("begin to start tx spider")
    p1 = threading.Thread(target=start_tx_spider)
    p1.start()
    ls.logging.info("begin to start ncov update")
    p2 = threading.Thread(target=do_ncov_update, args=[itchat, False])
    p2.start()
    itchat.send(ONLINE_TEXT, toUserName=FILE_HELPER)
    myself = itchat.search_friends()
    restore_group(conn, itchat, myself['NickName'])
    itchat.run(True)

if __name__ == '__main__':
    start_server()
