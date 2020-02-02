import sys
import os
import random

curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
BASE_PATH = os.path.split(rootPath)[0]
sys.path.append(BASE_PATH)

#### Redis Key Begin
# 每个城市单独保存一个key做集合，订阅的用户在集合中

USE_REDIS = False
# 当前所有疫情数据，类型：list
STATE_NCOV_INFO = 'state_ncov_info'
# 所有有疫情的城市集合
ALL_AREA_KEY = 'all_area'
# 标记为，标记数据是有更新
SHOULD_UPDATE = 'should_update'
# 需要推送更新的数据
UPDATE_CITY = 'update_city'
# 当前已有订阅的城市集合，类型set
ORDER_KEY = 'order_area'
# 用户关注的群聊ID
USER_FOCUS_GROUP = 'user_focus_group'
# 用户关注的群聊名称
USER_FOCUS_GROUP_NAME = 'user_focus_group_name'

#### Redis Key End

### Reg Pattern Begin

UN_REGIST_PATTERN = '^取关|取消(订阅)?.+'
UN_REGIST_PATTERN2 = '^取关|取消(订阅)?'

### REG PAttern End

BASE_DIR = os.path.join(BASE_PATH, 'resource')
DATA_DIR = os.path.join(BASE_DIR, 'data')
# for localhost redis
REDIS_HOST = '127.0.0.1'
## for docker redis
REDIS_HOST_DOCKER = 'redis'

LOGGING_FORMAT = '%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s'

AREA_TAIL = '(自治+)|省|市|县|区|镇'

FIRST_NCOV_INFO = '{}目前有确诊病例{}例，死亡病例{}例，治愈病例{}例'

FIRST_NCOV_INFO2 = '{}目前有确诊病例{}例，死亡病例{}例，治愈病例{}例。'

INFO1 = '\n向所有奋斗在抗击疫情一线的工作人员、志愿者致敬！'
INFO2 = '\nfeiyan.help，病毒无情，但人间有爱。'
INFO3 = '\n疫情严峻，请您尽量减少外出，避免出入公共场所'
INFO4 = '\n为了保证您能持续最新的疫情消息，根据WX的规则，建议您偶尔回复我一下～'
INFO5 = '\n全部数据来源于腾讯实时疫情追踪平台：https://news.qq.com//zt2020/page/feiyan.htm'
INFO6 = '\n我们是公益组织wuhan.support，网址 https://feiyan.help'
INFO7 = '\n这里是面向疫区内外民众和医疗机构的多维度信息整合平台，https://feiyan.help'
INFO8 = '\nhttps://feiyan.help，支持武汉，我们在一起。'
INFO9 = '\n开源地址：https://github.com/wuhan-support，支持武汉，我们在一起。'
INFO10 = '\n查看更多信息可以戳这里，https://feiyan.help。'
INFO11 = '\n这是一个为了避免微信阻塞消息的随机小尾巴...'
INFO12 = '\n众志成城，抵御疫情，武汉加油！'
INFO13 = '\nhttps://feiyan.help，筑牢抵御疫情蔓延的一道屏障'

INFO_TAILS = [INFO1, INFO2, INFO3, INFO4, INFO5, INFO6, INFO7, INFO8, INFO9, INFO10, INFO11, INFO12, INFO13]

UPDATE_NCOV_INFO = '{}有数据更新，新增确诊病例{}例，目前共有确诊病例{}例，死亡病例{}例，治愈病例{}例。'
UPDATE_NCOV_INFO_ALL = '{}有数据更新，新增确诊病例{}例，疑似病例{}例，目前共有确诊病例{}例，疑似病例{}例，死亡病例{}例，治愈病例{}例。'

NO_NCOV_INFO = '{}暂无疫情信息，请检查地区名称是否正确。'

INFO_TAIL = "若{}等地区数据有更新，我会在第一时间通知您！您也可以通过发送 '取消+地区名'取消关注该地区，比如'取消{}'，'取消全部'。"
INFO_TAIL_ALL = "若全国的数据有更新，我会在第一时间通知您！您也可以通过发送'取消全部'取消对全部数据的关注。"

FOCUS_TAIL = "如果该群转发的新闻、分享存在谣言，将会自动发送辟谣链接！您也可以通过发送'停止辟谣+群名'取消对该群的谣言检查。"
CHAOYANG_INFO = '您的订阅"朝阳"有些模糊，如果您想订阅北京朝阳区，请输入订阅朝阳区，如果想订阅辽宁省朝阳市，请输入订阅朝阳市'
TIME_SPLIT = 60 * 3

SHORT_TIME_SPLIT = 60 * 5

LONG_TIME_SPLIT = 60 * 60

SEND_SPLIT = random.random() * 10

SEND_SPLIT_SHORT = random.random() * 5

HELP_CONTENT = "您好！这是微信疫情信息小助手（非官方）！我有以下功能：\n1.若好友向您发送 订阅/取消+地区名 关注/取消该地区疫情并实时向该好友推送；" \
               "\n2.您向文件传输助手发送辟谣+群名，比如\"辟谣家族群\"，将对该群的新闻长文、链接分享自动进行辟谣，使用停止辟谣+群名停止该功能。发送\"CX\"可查询已关注的群聊。" \
               "\n以上所有数据来自腾讯\"疫情实时追踪\"平台，链接：https://news.qq.com//zt2020/page/feiyan.htm"

GROUP_CONTENT_HELP = "您对这些群启用了辟谣功能：{}。若发现漏掉了一些群，请将该群保存到通讯录再重新发送辟谣+群名。"

NO_GROUP_CONTENT_HELP = "您目前没有对任何群开启辟谣功能。若发现有遗漏，请将该群保存到通讯录再重新发送辟谣+群名。"

FILE_HELPER = 'filehelper'

ONLINE_TEXT = 'Hello, 微信疫情信息小助手（自动机器人）又上线啦'
