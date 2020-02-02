# -*- coding: utf-8 -*-

"""
Created by Wang Han on 2020/1/28 17:35.
E-mail address is hanwang.0501@gmail.com.
Copyright © 2018 Wang Han. SCU. All Rights Reserved.
"""
import json
import re


def loads_jsonp(jsonp):
    """
    解析jsonp数据格式为json
    :return:
    """
    try:
        return json.loads(re.match(".*?({.*}).*", jsonp, re.S).group(1))
    except:
        raise ValueError('Invalid Input')
