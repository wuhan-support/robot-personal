import os
import sqlalchemy as db

from src.util.log import LogSupport

ls = LogSupport()


class SQLiteConnect:
    '''SQLite 数据库接口封装类'''

    def __init__(self, db_file):
        create_tables = not os.path.isfile(db_file)
        self.engine = db.create_engine('sqlite:///{}'.format(db_file))
        self.conn = self.engine.connect()
        self.metadata = db.MetaData()
        self.cities_list = []
        self.initialize_tables(create_tables)

    def initialize_tables(self, create_tables=False):
        self.subscriptions = db.Table('subscriptions', self.metadata,
                                      db.Column('id', db.Integer(), primary_key=True, nullable=False),
                                      db.Column('uid', db.String(255), nullable=True),
                                      db.Column('city', db.String(255), nullable=True)
                                      )

        self.update_flag = db.Table('update_flag', self.metadata,
                                    db.Column('id', db.Integer(), primary_key=True, nullable=False),
                                    db.Column("flag", db.Integer()))

        self.group_name = db.Table('group_name', self.metadata,
                                   db.Column('id', db.Integer(), primary_key=True, nullable=False),
                                   db.Column("uid", db.String(255), nullable=False),
                                   db.Column("gid", db.String(255), nullable=False),
                                   db.Column('gname', db.String(255), nullable=False))

        self.area_list = db.Table('area_list', self.metadata,
                                  db.Column('id', db.Integer(), primary_key=True, nullable=False),
                                  db.Column('area', db.String(255), nullable=False))

        if create_tables:
            try:
                self.metadata.create_all(self.engine)
                # 初始化update flag为1
                query = db.insert(self.update_flag).values(id=1, flag=0)
                res = self.conn.execute(query)
                ls.logging.info("初始化数据库成功: {}".format(res.rowcount))
            except BaseException as e:
                ls.logging.error("初始化数据库出错")
                ls.logging.exception(e)

    def do_update_flag(self, flag):
        try:
            update = db.update(self.update_flag).where(self.update_flag.columns.id == 1).values(flag=flag)
            res = self.conn.execute(update)
            return res.rowcount
        except BaseException as e:
            ls.logging.error("ERROR: 更新update flag出错")
            ls.logging.exception(e)
            return 0

    def get_update_flag(self):
        try:
            query = db.select([self.update_flag]).where(self.update_flag.columns.id == 1)
            result_proxy = self.conn.execute(query)
            result = result_proxy.fetchone()
            return result[1]
        except BaseException as e:
            ls.logging.error("RROR: 获取update flag 出错")
            ls.logging.exception(e)
            return 0

    def save_subscription(self, uid, city):
        '''保存一个用户对于制定城市的订阅'''
        # TODO: add feedback for invalid input
        try:
            res = self.query_subscription(uid, city)
            if res == None:
                # 插入数据
                query = db.insert(self.subscriptions).values(uid=uid, city=city)
                res = self.conn.execute(query)
                return res.rowcount
        except BaseException as e:
            raise e

    def query_subscription(self, uid, city):
        query = db.select([self.subscriptions]).where(
            db.and_(
                self.subscriptions.columns.uid == uid,
                self.subscriptions.columns.city == city
            )
        )
        result_proxy = self.conn.execute(query)
        result = result_proxy.fetchone()
        return result

    def cancel_subscription(self, uid, city):
        """
        '''取消一个用户对于指定城市的订阅'''
        成功删除返回一个对象，否则返回影响的行数
        :param uid:
        :param city:
        :return:
        """
        query = db.delete(self.subscriptions).where(
            db.and_(
                self.subscriptions.columns.uid == uid,
                self.subscriptions.columns.city == city
            )
        )
        res = self.conn.execute(query)
        return res.rowcount

    def cancel_all_subscription(self, uid):
        query = db.delete(self.subscriptions).where(
            self.subscriptions.columns.uid == uid
        )
        res = self.conn.execute(query)
        return res.rowcount

    def get_subscribed_users(self, city):
        '''获取所有订阅指定城市的用户'''
        # TODO: add feedback for invalid input
        query = db.select([self.subscriptions]).where(self.subscriptions.columns.city == city)
        result_proxy = self.conn.execute(query)
        results = result_proxy.fetchall()
        return [sub[1] for sub in results]

    def add_group_for_user(self, uid, gid, gname):
        """
        user id
        :param uid: user id
        :param gid: 需要添加的群id,群id每次登陆可能会变
        :param gname: 群名称
        :return:
        """
        try:
            already = self.query_group_for_user(uid, gname)
            if already == None or len(already) == 0:
                insert = db.insert(self.group_name).values(uid=uid, gid=gid, gname=gname)
                res = self.conn.execute(insert)
                return res.rowcount
            else:
                update = db.update(self.group_name).where(
                    db.and_(
                        self.group_name.columns.uid == uid,
                        self.group_name.columns.gname == gname
                    )).values(gid=gid)
                res = self.conn.execute(update)
                return res.rowcount
        except BaseException as e:
            ls.logging.error("关注{}的群聊{}失败".format(uid, gname))
            ls.logging.exception(e)
            return -1

    def query_group_for_user(self, uid, gname):
        """
        根据群名称和用户名查找是否已关该群，避免重复添加
        :param uid:
        :param gname:
        :return:
        """
        query = db.select([self.group_name]).where(
            db.and_(
                self.group_name.columns.uid == uid,
                self.group_name.columns.gname == gname
            )
        )
        result_proxy = self.conn.execute(query)
        result = result_proxy.fetchall()
        return [x[3] for x in result]

    def query_all_group_for_user(self, uid):
        """
        根据id查询该用户所有辟谣的群
        :param uid:
        :return:
        """
        query = db.select([self.group_name]).where(
            self.group_name.columns.uid == uid,
        )
        result_proxy = self.conn.execute(query)
        result = result_proxy.fetchall()
        return [x[3] for x in result]

    def query_all_group_id_for_user(self, uid):
        """
        根据id查询该用户所有辟谣的群
        :param uid:
        :return:
        """
        query = db.select([self.group_name]).where(
            self.group_name.columns.uid == uid,
        )
        result_proxy = self.conn.execute(query)
        result = result_proxy.fetchall()
        return [x[2] for x in result]

    def cancel_group_for_user(self, uid, gname):
        """
        根据群和uid取消辟谣
        :param uid:
        :param gname:
        :return:
        """
        query = db.delete(self.group_name).where(
            db.and_(
                self.group_name.columns.uid == uid,
                self.group_name.columns.gname == gname
            )
        )
        res = self.conn.execute(query)
        return res.rowcount

    def cancel_all_group_for_user(self, uid):
        delete = db.delete(self.group_name).where(
            self.group_name.columns.uid == uid
        )
        res = self.conn.execute(delete)
        return res.rowcount

    def get_all_area(self):
        select = "select area from {};".format('area_list')
        res = self.conn.execute(select).fetchall()
        all_area = [sub[0] for sub in res]
        return all_area

    def check_area(self, city):
        select = "select id from area_list where area='{}'".format(city)
        res = self.conn.execute(select)
        return len(res.fetchall()) > 0

    def add_area_list(self, city):
        insert = db.insert(self.area_list).values(area=city)
        res = self.conn.execute(insert)
        return res.rowcount