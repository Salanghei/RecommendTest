#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
@author: zhaoyang
@license: (C) Copyright 2001-2019 Python Software Foundation. All rights reserved.
@contact: 1805453683@qq.com
@file: lpm_recommend.py
@time: 2019/12/9 14:29
"""
import pymongo
import time
import pandas as pd
import numpy as np
from scipy.spatial.distance import pdist


def get_cos_dist(data):
    '''
    计算用户间的余弦相似度
    :param data: [用户的兴趣话题及感兴趣程度的字典，用户邻居的兴趣话题及感兴趣程度的字典]
    :return: 余弦相似度
    '''
    data = pd.DataFrame(data)
    data.fillna(0, inplace=True)    # 空值默认为0
    dist = pdist(np.vstack([data]), "cosine")
    return dist


start = time.time()    # 程序运行开始时间
print("正在获取用户信息......")
my_client = pymongo.MongoClient("mongodb://127.0.0.1:27017")
my_collection = my_client.lpmweb.portrait
user = my_collection.find({"studentId": 4})[0]  # 用于推荐的用户
print("用户信息：", user)

print("正在获取邻居列表......")
neighbors = []    # 用户的邻居列表，即与user感兴趣话题有重合部分的用户
neighbor_topics = []    # 用户邻居的感兴趣话题及感兴趣程度的列表
user_topic = {}    # 用户的感兴趣话题及感兴趣程度
for topic in user["topics"]:
    user_topic[topic["topicId"]] = topic["count"]
    query_cell = {
        "topics": {
            "$elemMatch": {"topicId": topic["topicId"], "count": {"$gte": topic["count"]}}
        }
    }
    candidate_user_cursor = my_collection.find(query_cell)
    for candidate_user in candidate_user_cursor:
        if candidate_user["studentId"] != user["studentId"] and candidate_user["studentId"] not in neighbors:
            neighbors.append(candidate_user["studentId"])
            new_neighbor_topic = {}
            for candidate_user_topic in candidate_user["topics"]:
                new_neighbor_topic[candidate_user_topic["topicId"]] = candidate_user_topic["count"]
            neighbor_topics.append(new_neighbor_topic)
print("该用户邻居的数量为：", len(neighbors))

print("正在计算与邻居间的余弦相似度......")
trust_list = []
for index in range(len(neighbors)):
    dist = get_cos_dist([user_topic, neighbor_topics[index]])[0]
    if dist > 0.98:
        trust_list.append([dist, neighbors[index]])
trust_list.sort(reverse=True)
trust_count = len(trust_list)
if trust_count >= 5:
    recommend_list = trust_list[:5]
else:
    recommend_list = trust_list
print("信任用户数量为（余弦相似度 > 0.98）：", len(trust_list))
print("推荐用户为：", recommend_list)

end = time.time()
print("程序运行时间：", end - start, "s")
