import os

import requests
from urllib import parse
from src.util.constant import ALL_AREA_KEY, AREA_TAIL, SHOULD_UPDATE, STATE_NCOV_INFO, UPDATE_CITY, TIME_SPLIT, \
    USE_REDIS, BASE_DIR, DATA_DIR
from src.util.log import LogSupport
import json
import re
from src.util.redis_config import connect_redis, save_json_info, load_last_info, save_json_info_as_key
from src.util.sqlite_config import SQLiteConnect
from src.util.util import check_dir_exist


class TXSpider():
    def __init__(self, debug=True):
        """
        爬取腾讯新闻平台的实时疫情数据
        :param debug:
        """
        self.req = requests.Session()
        self.log = LogSupport()
        if USE_REDIS:
            self.re = connect_redis()
        else:
            self.re = None
        self.debug = debug
        self.sqlc = SQLiteConnect(os.path.join(BASE_DIR, "sqlite.db"))
        self.check_dirs()

    def check_dirs(self):
        check_dir_exist(DATA_DIR)
        check_dir_exist(os.path.join(os.path.join(BASE_DIR, "download_image")))

    def main(self):
        """
        主函数
        :return:
        """
        try:
            data = self.get_raw_real_time_info()
            chinaTotal = data['chinaTotal']
            # 腾讯areaTree中的全国数据与chinaTotal不一致，以chinaTotal为准
            now_data = self.change_raw_data_format_new(data['areaTree'])
            now_data['全国']['confirm'] = int(chinaTotal['confirm'])
            now_data['全国']['suspect'] = int(chinaTotal['suspect'])
            now_data['全国']['dead'] = int(chinaTotal['dead'])
            now_data['全国']['heal'] = int(chinaTotal['heal'])
            # 保存所有的地区名
            self.save_all_area(now_data)
            # 加载上一次最新的数据
            last_data = load_last_info(self.re)
            if not last_data:
                save_json_info(self.re, STATE_NCOV_INFO, now_data)
                last_data = now_data
            update_city = self.parse_increase_info(now_data, last_data)
            if USE_REDIS:
                should_update = self.re.get(SHOULD_UPDATE)
                should_update = 0 if should_update == None else should_update
            else:
                should_update = self.sqlc.get_update_flag()
            # 如果数据有更新，则保存新数据和更新的数据
            if len(update_city) > 0:
                save_json_info(self.re, STATE_NCOV_INFO, now_data)
                if should_update == 0:
                    if USE_REDIS:
                        self.re.set(SHOULD_UPDATE, 1)
                    else:
                        self.sqlc.do_update_flag(1)
                # 如果上一次的数据还没推出去，要先合并新增数据
                elif should_update == 1:
                    old_update_city = self.get_old_data_city()
                    if old_update_city != None:
                        update_city = self.merge_update_city(old_city_list=old_update_city, new_city_list=update_city)
                save_json_info_as_key(self.re, UPDATE_CITY, update_city)
                self.log.logging.info("set update city {}".format(json.dumps(update_city)[:20]))
            else:
                # self.re.set(SHOULD_UPDATE, 0)
                self.log.logging.info("no update city")

        except BaseException as e:
            self.log.logging.exception(e)

    def get_old_data_city(self):
        try:
            if USE_REDIS:
                old_update_city = json.loads(self.re.get(UPDATE_CITY))
            else:
                file = os.path.join(DATA_DIR, UPDATE_CITY + ".json")
                with open(file, 'r', encoding='utf-8') as r:
                    old_update_city = json.load(r)
            return old_update_city
        except BaseException as e:
            self.log.logging.error("Error: failed to load old update city")
            self.log.logging.exception(e)
            return None

    def merge_update_city(self, new_city_list, old_city_list):
        final_result = []
        old_city = {x['city']: x for x in old_city_list}
        new_city = {x['city']: x for x in new_city_list}

        for city in new_city_list:
            if city['city'] in old_city:
                city['n_confirm'] += old_city[city['city']]['n_confirm']
                city['n_suspect'] += old_city[city['city']]['n_suspect']
                city['n_dead'] += old_city[city['city']]['n_dead']
                city['n_heal'] += old_city[city['city']]['n_heal']
                final_result.append(city)
            else:
                final_result.append(city)

        for city in old_city_list:
            if city['city'] not in new_city:
                final_result.append(city)
        return final_result

    def get_state_all_url(self):
        url = 'https://view.inews.qq.com/g2/getOnsInfo?name=wuwei_ww_global_vars'
        return url

    def get_state_all(self):
        """
        获取全国数据
        :return:
        """
        res = self.req.get(url=self.get_state_all_url(), headers=self.get_tx_header())
        if res.status_code != 200:
            self.log.logging.error("获取全国数据失败")
        data = json.loads(json.loads(res.content.decode("utf-8"))['data'])[0]
        state_dict = {}
        state_dict['confirm'] = data['confirmCount']
        state_dict['dead'] = data['deadCount']
        state_dict['heal'] = data['cure']
        state_dict['suspect'] = data['suspectCount']
        state_dict['area'] = '全国'
        state_dict['country'] = '全国'
        state_dict['city'] = '全国'
        return {'全国': state_dict}

    def get_tx_header(self):
        return {
            'host': 'view.inews.qq.com',
            'user-agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1',
            'sec-fetch-mode': 'no-cors',
            'sec-fetch-site': 'same-site',
            'referer': 'https://news.qq.com/zt2020/page/feiyan.htm'
        }

    def get_real_time_url(self):
        base_url = 'https://view.inews.qq.com/g2/getOnsInfo?'
        # 旧接口
        # params = {
        #     'name': 'wuwei_ww_area_counts'
        # }
        params = {
            'name': 'disease_h5'
        }
        return base_url + parse.urlencode(params)

    def get_raw_real_time_info(self):
        """
        从腾讯新闻获取各地病例数量的实时数据
        :return:
        """
        url = self.get_real_time_url()
        header = self.get_tx_header()
        res = self.req.get(url=url, headers=header)
        if res.status_code != 200:
            self.log.logging.error("Failed to get info")
            raise ConnectionError
        content = json.loads(res.content.decode("utf-8"))
        data = json.loads(content['data'])
        return data

    def change_raw_data_format_new(self, data):
        data_dict = {}
        for area in data:
            if area['name'] == '待确认':
                # print(area)
                continue
            # 区分辽宁朝阳市和北京朝阳区
            if area['name'] == '朝阳':
                area_key = '朝阳区'
                area['name'] = '朝阳区'
            elif area['name'] == '中国':
                area_key = '全国'
                area['name'] ='全国'
            else:
                area_key = area['name']
            data_dict[area_key] = area['total']
            data_dict[area_key]['city'] = area['name']
            data_dict[area_key]['area'] = area['name']
            data_dict[area_key]['t_confirm'] = area['today']['confirm']
            data_dict[area_key]['t_suspect'] = area['today']['suspect']
            data_dict[area_key]['t_dead'] = area['today']['dead']
            data_dict[area_key]['t_heal'] = area['today']['heal']
            if 'children' in area:
                data_dict.update(self.change_raw_data_format_new(area['children']))
        return data_dict

    def fill_unknow(self, data):
        for item in data:
            if 'city' not in item or item['city'] == '':
                if 'area' not in item or item['area'] == '':
                    item['city'] = item['country']
                    item['area'] = item['country']
                else:
                    item['city'] = item['area']
        return data

    def save_all_area(self, data_dict):
        """
        保存所有地区的名称，供分词用
        :param data_dict:
        :return:
        """
        all_area = set(data_dict.keys())
        if USE_REDIS:
            for area in all_area:
                short = re.subn(AREA_TAIL, '', area)[0]
                self.re.sadd(ALL_AREA_KEY, short)
                self.re.sadd(ALL_AREA_KEY, area)
        else:
            now_area = set(self.sqlc.get_all_area())
            new_area = all_area.difference(now_area)
            for area in new_area:
                self.sqlc.add_area_list(area)
            pass

    def parse_increase_info(self, now_data, last_data):
        # 计算有更新的城市/省份/国家
        update_city = []
        for index, value in now_data.items():
            if index in last_data:
                last_value = last_data[index]
                now_data[index]['n_confirm'] = value['confirm'] - last_value['confirm']
                now_data[index]['n_suspect'] = value['suspect'] - last_value['suspect']
                now_data[index]['n_dead'] = value['dead'] - last_value['dead']
                now_data[index]['n_heal'] = value['heal'] - last_value['heal']
            else:
                now_data[index]['n_confirm'] = value['confirm']
                now_data[index]['n_suspect'] = value['suspect']
                now_data[index]['n_dead'] = value['dead']
                now_data[index]['n_heal'] = value['heal']
            if self.check_whether_update(now_data[index]):
                update_city.append(now_data[index])
        return update_city

    def check_whether_update(self, item):
        return item['n_confirm'] > 0 or item['n_suspect'] > 0 or item['n_dead'] > 0 or item['n_heal'] > 0


if __name__=='__main__':
    tx = TXSpider()
    tx.main()


