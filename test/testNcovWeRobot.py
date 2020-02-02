import threading
import unittest

import itchat

from src.util.util import move_image, check_identify
from src.robot.NcovWeRobotFunc import *
from src.robot.NcovWeRobotServer import do_ncov_update, start_server
from src.spider.TXSpider import TXSpider
from src.util.constant import SHOULD_UPDATE, UPDATE_CITY, UN_REGIST_PATTERN2, BASE_DIR
from src.util.redis_config import connect_redis, save_json_info_as_key
import jieba
import os


class testNcovWeRobot(unittest.TestCase):

    def setUp(self) -> None:
        self.sp = TXSpider()
        self.data1 = [
            {"country": "中国", "area": "湖北", "city": "武汉", "confirm": 618, "suspect": 0, "dead": 45, "heal": 40},
            {"country": "中国", "area": "湖北", "city": "黄冈", "confirm": 122, "suspect": 0, "dead": 2, "heal": 2},
            {"country": "中国", "area": "湖北", "city": "孝感", "confirm": 55, "suspect": 0, "dead": 0, "heal": 0},
            {"country": "中国", "area": "湖北", "city": "荆门", "confirm": 38, "suspect": 0, "dead": 1, "heal": 0},
            {"country": "中国", "area": "湖北", "city": "恩施州", "confirm": 17, "suspect": 0, "dead": 0, "heal": 0},
            {"country": "中国", "area": "湖北", "city": "荆州", "confirm": 33, "suspect": 0, "dead": 2, "heal": 0},
            {"country": "中国", "area": "湖北", "city": "仙桃", "confirm": 11, "suspect": 0, "dead": 0, "heal": 0},
            {"country": "中国", "area": "湖北", "city": "十堰", "confirm": 20, "suspect": 0, "dead": 0, "heal": 0},
            {"country": "中国", "area": "湖北", "city": "随州", "confirm": 36, "suspect": 0, "dead": 0, "heal": 0},
            {"country": "中国", "area": "湖北", "city": "天门", "confirm": 5, "suspect": 0, "dead": 0, "heal": 0},
            {"country": "中国", "area": "湖北", "city": "宜昌", "confirm": 20, "suspect": 0, "dead": 1, "heal": 0},
            {"country": "中国", "area": "湖北", "city": "鄂州", "confirm": 1, "suspect": 0, "dead": 0, "heal": 0},
            {"country": "中国", "area": "湖北", "city": "咸宁", "confirm": 43, "suspect": 0, "dead": 0, "heal": 0},
            {"country": "中国", "area": "广东", "city": "广州", "confirm": 17, "suspect": 0, "dead": 0, "heal": 0},
            {"country": "加拿大", "area": "", "city": "", "confirm": 1, "suspect": 0, "dead": 0, "heal": 0},
            {"country": "法国", "area": "", "city": "", "confirm": 3, "suspect": 0, "dead": 0, "heal": 0}]

        self.data2 = [
            {"country": "中国", "area": "湖北", "city": "武汉", "confirm": 698, "suspect": 0, "dead": 45, "heal": 40},
            {"country": "中国", "area": "湖北", "city": "黄冈", "confirm": 122, "suspect": 0, "dead": 2, "heal": 2},
            {"country": "中国", "area": "湖北", "city": "孝感", "confirm": 55, "suspect": 0, "dead": 0, "heal": 0},
            {"country": "中国", "area": "湖北", "city": "荆门", "confirm": 38, "suspect": 0, "dead": 1, "heal": 0},
            {"country": "中国", "area": "湖北", "city": "恩施州", "confirm": 17, "suspect": 0, "dead": 0, "heal": 0},
            {"country": "中国", "area": "湖北", "city": "荆州", "confirm": 33, "suspect": 0, "dead": 2, "heal": 0},
            {"country": "中国", "area": "湖北", "city": "仙桃", "confirm": 11, "suspect": 0, "dead": 0, "heal": 0},
            {"country": "中国", "area": "湖北", "city": "十堰", "confirm": 20, "suspect": 0, "dead": 0, "heal": 0},
            {"country": "中国", "area": "湖北", "city": "随州", "confirm": 36, "suspect": 0, "dead": 0, "heal": 0},
            {"country": "中国", "area": "湖北", "city": "天门", "confirm": 5, "suspect": 0, "dead": 0, "heal": 0},
            {"country": "中国", "area": "湖北", "city": "宜昌", "confirm": 20, "suspect": 0, "dead": 1, "heal": 0},
            {"country": "中国", "area": "湖北", "city": "鄂州", "confirm": 1, "suspect": 0, "dead": 0, "heal": 0},
            {"country": "中国", "area": "湖北", "city": "咸宁", "confirm": 43, "suspect": 0, "dead": 0, "heal": 0},
            {"country": "中国", "area": "广东", "city": "广州", "confirm": 17, "suspect": 0, "dead": 0, "heal": 0},
            {"country": "加拿大", "area": "", "city": "", "confirm": 2, "suspect": 0, "dead": 0, "heal": 0},
            {"country": "法国", "area": "", "city": "", "confirm": 3, "suspect": 0, "dead": 0, "heal": 0},
            {"country": "中国", "area": "重庆", "city": "重庆", "confirm": 3, "suspect": 0, "dead": 0, "heal": 0}]

        self.update_city = [
            {"country": "中国", "area": "辽宁", "city": "沈阳", "confirm": 8, "suspect": 0, "dead": 0, "heal": 0,
             "n_confirm": 1, "n_suspect": 0, "n_dead": 0, "n_heal": 0},
            {"area": "天津", "confirm": 24, "suspect": 0, "dead": 0, "heal": 0, "city": "天津", "n_confirm": 1,
             "n_suspect": 0, "n_dead": 0, "n_heal": 0},
            {"country": "中国", "area": "辽宁", "city": "丹东", "confirm": 5, "suspect": 0, "dead": 0, "heal": 0,
             "n_confirm": 1, "n_suspect": 0, "n_dead": 0, "n_heal": 0},
            {"country": "中国", "area": "上海", "city": "外地来沪", "confirm": 33, "suspect": 0, "dead": 0, "heal": 0,
             "n_confirm": 33, "n_suspect": 0, "n_dead": 0, "n_heal": 0},
            {"country": "中国", "area": "上海", "city": "浦东", "confirm": 9, "suspect": 0, "dead": 0, "heal": 0,
             "n_confirm": 9, "n_suspect": 0, "n_dead": 0, "n_heal": 0},
            {"country": "中国", "area": "上海", "city": "长宁", "confirm": 5, "suspect": 0, "dead": 0, "heal": 0,
             "n_confirm": 5, "n_suspect": 0, "n_dead": 0, "n_heal": 0},
            {"country": "中国", "area": "上海", "city": "静安", "confirm": 5, "suspect": 0, "dead": 0, "heal": 0,
             "n_confirm": 5, "n_suspect": 0, "n_dead": 0, "n_heal": 0},
            {"country": "中国", "area": "上海", "city": "徐汇", "confirm": 3, "suspect": 0, "dead": 0, "heal": 0,
             "n_confirm": 3, "n_suspect": 0, "n_dead": 0, "n_heal": 0},
            {"country": "中国", "area": "上海", "city": "虹口", "confirm": 2, "suspect": 0, "dead": 0, "heal": 0,
             "n_confirm": 2, "n_suspect": 0, "n_dead": 0, "n_heal": 0},
            {"country": "中国", "area": "上海", "city": "闵行", "confirm": 2, "suspect": 0, "dead": 0, "heal": 0,
             "n_confirm": 2, "n_suspect": 0, "n_dead": 0, "n_heal": 0},
            {"country": "中国", "area": "上海", "city": "青浦", "confirm": 2, "suspect": 0, "dead": 0, "heal": 0,
             "n_confirm": 2, "n_suspect": 0, "n_dead": 0, "n_heal": 0},
            {"country": "中国", "area": "上海", "city": "黄埔", "confirm": 2, "suspect": 0, "dead": 0, "heal": 0,
             "n_confirm": 2, "n_suspect": 0, "n_dead": 0, "n_heal": 0},
            {"country": "中国", "area": "上海", "city": "宝山", "confirm": 1, "suspect": 0, "dead": 0, "heal": 0,
             "n_confirm": 1, "n_suspect": 0, "n_dead": 0, "n_heal": 0},
            {"country": "中国", "area": "上海", "city": "嘉定", "confirm": 1, "suspect": 0, "dead": 0, "heal": 0,
             "n_confirm": 1, "n_suspect": 0, "n_dead": 0, "n_heal": 0},
            {"country": "中国", "area": "上海", "city": "奉贤", "confirm": 1, "suspect": 0, "dead": 0, "heal": 0,
             "n_confirm": 1, "n_suspect": 0, "n_dead": 0, "n_heal": 0},
            {"country": "中国", "area": "辽宁", "city": "辽阳", "confirm": 1, "suspect": 0, "dead": 0, "heal": 0,
             "n_confirm": 1, "n_suspect": 0, "n_dead": 0, "n_heal": 0},
            {"area": "辽宁", "confirm": 30, "suspect": 0, "dead": 0, "heal": 0, "city": "辽宁", "n_confirm": 3,
             "n_suspect": 0, "n_dead": 0, "n_heal": 0},
            {"confirm": 4533, "dead": 106, "heal": 60, "suspect": 6973, "area": "全国", "country": "全国", "city": "全国",
             "n_confirm": 4, "n_suspect": 0, "n_dead": 0, "n_heal": 0}]

    def testCheckRegister(self):
        assert check_whether_register("订阅湖北") == True
        assert check_whether_register("不订阅") == False
        assert check_whether_register("订阅") == False

    def testCheckUnregist(self):
        assert check_whether_unregist("取消湖北") == True
        assert check_whether_unregist("取消") == False
        assert check_whether_unregist("取关湖北") == True
        assert re.subn(UN_REGIST_PATTERN2, "", "取消湖北")[0] == '湖北'
        assert re.subn(UN_REGIST_PATTERN2, "", "取消关注湖北")[0] == '湖北'
        assert re.subn(UN_REGIST_PATTERN2, "", "取关湖北")[0] == '湖北'

    def test_user_subscribe(self):
        conn = connect_redis()
        succ, failed = user_subscribe(conn, 'test', '订阅湖北', jieba)
        assert succ == ['湖北']

    def test_user_unsubscribe(self):
        """
        因数据格式已经改变，该测试已废弃
        :return:
        """
        conn = connect_redis()
        # 完成数据转化并更新数据库
        self.sp.change_raw_data_format_new(self.data2)
        user_subscribe(conn, 'test', '订阅湖北', jieba)
        succ, failed = user_unsubscribe_multi_redis(conn, 'test', '取消关注湖北', jieba)
        assert succ == ['湖北']
        succ, failed = user_subscribe(conn, 'test', '订阅湖北重庆', jieba)
        assert succ == ['湖北', '重庆']
        succ, failed = user_unsubscribe_multi_redis(conn, 'test', '取消重庆市', jieba)
        assert succ == ['重庆']
        succ, failed = user_unsubscribe_multi_redis(conn, 'test', '取关全部', jieba)
        assert succ == ['全部']
        succ, failed = user_unsubscribe_multi_redis(conn, 'test', '取消湖南', jieba)
        assert succ == [] and failed == ['湖南']

    def test_do_ncov_update(self):
        # 完成数据转化并更新数据库
        last = self.sp.change_raw_data_format_new(self.data1)
        now = self.sp.change_raw_data_format_new(self.data2)
        update_city = self.sp.parse_increase_info(now, last)
        self.sp.re.set(SHOULD_UPDATE, 1)
        save_json_info_as_key(self.sp.re, UPDATE_CITY, update_city)
        itchat.auto_login()
        user_subscribe(self.sp.re, 'filehelper', '订阅湖北重庆', jieba)
        do_ncov_update(self.sp.re, itchat)

    def test_start_server(self):
        succ, failed = user_subscribe(self.sp.re, 'filehelper', '订阅全国', jieba)
        assert len(succ) == 1
        p = threading.Thread(target=self.test_save_data_loop)
        p.start()
        start_server()

    def test_check_identify(self):
        test1 = '湖北省防控指挥部'
        test2 = '这是谣言'
        test3 = '辟谣！'
        assert check_identify(test1) == True
        assert check_identify(test2) == True
        assert check_identify(test3) == True

    def test_group_exists(self):
        test1 = '群1'
        key1 = 'test_set'
        conn = connect_redis()
        conn.sadd(key1, test1)
        if not conn.sismember(key1, test1):
            print("not exists")
        else:
            print("exists")

    def test_construct_push_info(self):
        city1 = {"confirm": 4, "suspect": 0, "dead": 0, "heal": 0, "city": "德国", "t_confirm": 0, "t_suspect": 0,
                 "t_dead": 0, "t_heal": 0, "n_confirm": 3, "n_suspect": 0, "n_dead": 0, "n_heal": 0}
        city2 = {"confirm": 6, "suspect": 0, "dead": 0, "heal": 0, "city": "张家口", "t_confirm": 5, "t_suspect": 0, "t_dead": 0, "t_heal": 0, "n_confirm": 6, "n_suspect": 0, "n_dead": 0, "n_heal": 0}
        print(construct_push_info(city1))
        print(construct_push_info(city2))

    def test_info_tail(self):
        for i in range(20):
            print(get_random_tail())

    def test_long_time_split(self):
        for i in range(20):
            print(get_random_long_time())

    def test_save_data_loop(self):
        while True:
            self.sp.re.set(SHOULD_UPDATE, 1)
            save_json_info_as_key(self.sp.re, UPDATE_CITY, self.update_city)
            time.sleep(10)

    def test_move_image(self):
        move_image('../200128-081500.png', os.path.join(BASE_DIR, 'download_image/') + '200128-081500.png')
