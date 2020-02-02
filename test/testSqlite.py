import os
import unittest

from src.util.constant import BASE_DIR
from src.util.sqlite_config import SQLiteConnect


class TestSqlite(unittest.TestCase):

    def setUp(self) -> None:
        self.sqlc = SQLiteConnect(os.path.join(BASE_DIR, "sqlite.db"))

    def test_init_sqlite(self):
        pass

    def test_subscription(self):
        user = 'test1'
        city = '重庆'
        res = self.sqlc.query_subscription(user, city)
        self.sqlc.save_subscription(user, city)
        self.sqlc.save_subscription(user, city)
        res = self.sqlc.query_subscription(user, city)
        print(res)
        res = self.sqlc.cancel_subscription(user, city)
        assert res == 2

    def test_update_flag(self):
        flag = self.sqlc.get_update_flag()
        print(flag)
        self.sqlc.do_update_flag(1)
        res1 = self.sqlc.get_update_flag()
        assert res1 == 1
        self.sqlc.do_update_flag(flag)

    def test_get_all_area(self):
        area_list = self.sqlc.get_all_area()
        return area_list

    def test_check_area(self):
        if not self.sqlc.check_area('重庆'):
            insert = self.sqlc.add_area_list('重庆')
            assert insert == 1
        area_list = self.sqlc.get_all_area()
        print(area_list)

    def test_group(self):
        user = 'test1'
        g1 = 'ID1'
        n1 = '群1'
        g2 = 'ID2'
        n2 = '群2'
        self.sqlc.add_group_for_user(user, g1, n1)
        res = self.sqlc.add_group_for_user(user, g2, n2)

        res = self.sqlc.query_all_group_for_user(user)
        print(res)
        assert len(res) == 2

        res = self.sqlc.cancel_group_for_user(user, n1)
        assert res == 1

        res = self.sqlc.add_group_for_user(user, g2, n2)
        assert res == 0

        res = self.sqlc.query_all_group_for_user(user)
        assert len(res) == 1
        self.sqlc.add_group_for_user(user, g1, n1)
        res = self.sqlc.cancel_all_group_for_user(user)
        assert res == 2
