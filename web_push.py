#!/usr/bin/env python
# coding: utf-8

import BeautifulSoup as bs
import requests
import re
import json
import cPickle as pickle
import multiprocessing
import time
import threading
import Queue

from tgbot import TgBot as tgbot

class WebPusher(object):
    def __init__(self, token, fname="ded_nuaa.dat"):
        self.message_queue = Queue.Queue()                      # 命令队列
        self.news_queue = Queue.Queue()                         # 新闻队列，用于传输更新的新闻

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
            return
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

    def update_news(self):
        """\
        定时刷新新闻
        """
        while True:
            new_news = self.get_news()
            for news in new_news:
                self.news_queue.put(news)                      # 用news_queue传递消息
            time.sleep(300)                                    # 定时刷新

        print "News updated"

    def push_news(self, title, href):
        """\
        将新闻推送至tg账号
        """
        # TODO: 建立一个订阅号，可能要建立数据库
        self.bot.send_message(90625935, '\n'.join([title, href]))

    def update_messages(self):
        """\
        获取bot收到的信息
        """
        result = self.bot.get_updates()
        if result:
            messages = result["result"]
            for message in messages:
                self.message_queue.put(message["message"])
        print "Message updated"


    # TODO: 进行定时刷新
    # TODO: 接收来自用户的命令，比如/getlatest
    # TODO: 做成一个订阅号

    # TODO: 在定时刷新的同时接收并处理用户命令，要用多线程

    def execute_message(message):
        if message["text"] == "/test":
            name = ' '.join(message["from"]["first_name"], message["from"]["last_name"])
            bot.send_message(messgae["chat"]["id"], name+time.ctime())

    def listening(self):
        print "Start listening"
        while True:
            try:
                while True:
                    message = self.message_queue.get_nowait()
                    self.execute_message(message)
            except Queue.Empty:
                pass
            
            while True:
                try:
                    news_list = []
                    while True:
                        news = self.news_queue.get_nowait()
                        news_list.append(news)
                except Queue.Empty:
                    for news in news_list:
                        self.push_news(news)             

    def start(self):
        """\
        主函数
        """
        message_thread = threading.Thread(target=self.update_messages)
        news_thread = threading.Thread(target=self.update_news)
        listen_thread = threading.Thread(target=self.listening)
        # news_thread = threading.Thread
        map(lambda x:x.start(), [message_thread, news_thread, listen_thread])
        listen_thread.join()
        # pass

    def __del__(self):
        pickle.dump(self.news_list, file(self.fname, 'wb'))


if __name__ == '__main__':
    a = WebPusher('70292863:AAEzdiMxmhzT52xYsL6L8FbPi20lXU6WEpc')
    a.start()
    # for title, href in news_list:
    #     print title, href
