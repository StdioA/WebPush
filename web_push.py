#!/usr/bin/env python
# coding: utf-8

import BeautifulSoup as bs
import requests
import re
import json
import cPickle as pickle
import time
import threading
import Queue
import sys
import os
import signal

from tgbot import TgBot as tgbot

class WebPusher(object):
    def __init__(self, token, fname="ded_nuaa.dat"):
        self.message_queue = Queue.Queue()                      # 命令队列
        # self.news_queue = Queue.Queue()                       # 新闻队列，用于传输更新的新闻
        self.run = True                                         # 判定是否需要结束程序

        self.fname = fname
        try:
            self.news_list = pickle.load(file(fname, 'rb'))
        except IOError:
            self.news_list = []

        self.bot = tgbot(token)

    def get_news(self):
        """\
        获取最新的教务处新闻，并将其推送至tg账号
        """
        new_news = []
        url = 'http://ded.nuaa.edu.cn/HomePage/articles/'
        hr = requests.get(url)
        if hr.status_code != 200:
            return []
        html = bs.BeautifulSoup(hr.text)
        news_l = html.findAll('td', attrs={'class':'tit1'})
        for news in news_l:
             link = news.findChild('a')
             href = url+link.attrs[0][1]
             title = link.text
             if not (title, href) in self.news_list:
                new_news.append((title, href))
                self.news_list.append((title, href))

        return new_news
        # TODO: 添加新闻发布日期

    def get_news_appinn(self):
        """\
        Get the news from the website.
        存在一定缺陷（比如会把“精彩推荐”当新闻扒下来），懒得改了，弃了
        """
        new_news = []
        html = bs.BeautifulSoup(requests.get('http://www.appinn.com').text)
        links = html.findAll('a', attrs={'rel':'bookmark'})
        for link in links:
            for attr, text in link.attrs:
                if attr == "href":
                    href = text
                elif attr == "title":
                    title = text
            if not (title, href) in self.news_list:
                new_news.append((title, href))
                self.news_list.append((title, href))
        return new_news

    def push_news(self, news):
        """\
        将新闻推送至tg账号
        """
        # TODO: 建立一个订阅号，可能要建立数据库
        title, href = news
        self.bot.send_message(90625935, '\n'.join([title, href]))

    def update_news(self):
        """\
        定时刷新新闻
        """
        print "update_news start"

        while True:
            new_news = self.get_news()
            for news in new_news:
                self.push_news(news)

            time.sleep(300)

        print "update_news stop"

    def update_messages(self):
        """\
        获取bot收到的信息
        """
        print "update_messages start"

        while self.run:
            result = self.bot.get_updates()
            if result:
                messages = result["result"]
                for message in messages:
                    self.message_queue.put(message["message"])

        print "update_messages stop"

    # TODO: 添加一些\户命令，比如/get_latest
    # TODO: 做成一个订阅号
    # TODO: 考虑用multiprocessing解决问题

    def listen_message(self):
        print "Start listening to messages"

        while self.run:
            message = self.message_queue.get()
            self.execute_message(message)

        print "Stop listening to messages"

    def execute_message(self, message):
        print message["text"]
        if message["text"] == "/test":
            name = ' '.join([message["from"]["first_name"], message["from"]["last_name"]])
            self.bot.send_message(message["chat"]["id"], name+" "+time.ctime())
        elif message["text"] == "/kill":
            self.run = False

    def start(self):
        """\
        主函数
        """

        func_list = [self.update_messages, self.update_news, self.listen_message] #, self.listen_news]

        thread_list = [threading.Thread(target=f) for f in func_list]                                   # 创建线程
        map(lambda x: x.setDaemon(True), [thread_list[1]])
        map(lambda x: x.start(), thread_list)                                                           # 启动线程

    def __del__(self):
        pickle.dump(self.news_list, file(self.fname, 'wb'))


if __name__ == '__main__':
    a = WebPusher('70292863:AAEzdiMxmhzT52xYsL6L8FbPi20lXU6WEpc')
    a.start()
    # for title, href in news_list:
    #     print title, href
