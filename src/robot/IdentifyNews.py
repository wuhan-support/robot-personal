from urllib import parse
import requests

from src.util.log import LogSupport
import json

from src.util.util import parse_identify_res

ls = LogSupport()
def get_identify_url(title):
    url = 'https://vp.fact.qq.com/searchresult?'
    params = {
        'title': title,
        'num': 0
    }
    return url + parse.urlencode(params)

def get_headers():
    return {
        'host': 'vp.fact.qq.com',
        'user-agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1',
        'sec-fetch-mode': 'no-cors',
        'sec-fetch-site': 'same-origin',
        'referer': 'https://vp.fact.qq.com/home?state=2'
    }

def get_identify_result(text_list):
    """
    需要鉴别的一串文字，因为是提取摘要后的结果，一段文字可能有多个摘要
    :param text_list:
    :return:如果是谣言则返回辟谣文字，否则返回None
    """
    req = requests.Session()
    for text in text_list:
        res = req.get(url=get_identify_url(text), headers=get_headers())
        if res.status_code != 200:
            ls.logging.error("查询较真平台出错，状态码：{}".format(res.status_code))
            return None
        content = res.content.decode("utf-8")
        if content:
            content = json.loads(content)
        else:
            continue
        if content['total'] == 0:
            continue
        else:
            source = content['content']
            for item in source:
                if item['_source']['result'] != '真-确实如此':
                    source = item['_source']
                    reply = parse_identify_res(text, source)
                    # 发送消息
                    ls.logging.info("谣言：{}，来源:{}".format(text, source['oriurl']))
                    return reply
        ls.logging.info("非谣言：{}".format(text))
        return None