#!/usr/bin/env python
# coding: utf-8

import BeautifulSoup as bs
import requests
import re
import cPickle as pickle
import multiprocessing
import time

from tgbot import TgBot as tgbot

class WebPusher(object):
    def __init__(self, token, fname="ded_nuaa.dat"):
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
                new_news.append(title, href)
                self.news_list.append((title, href))

        return self.news_list,new_news()

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
        return self.news_list, new_news

    def push_news(self, title, href):
        """\
        将新闻推送至tg账号
        """
        # TODO: 建立一个订阅号，可能要建立数据库
        self.bot.send_message(90625935, '\n'.join([title, href]))

    # TODO: 进行定时刷新
    # TODO: 接收来自用户的命令，比如/getlatest
    # TODO: 在定时刷新的同时接收并处理用户命令，要用多线程
    # TODO: 做成一个订阅号

    def get_command(self):
        """\
        接收来自用户的命令或信息
        """
        pass

    def listening_news(self):
        while True:
            sleep(1800)
            newl, new_news = self.get_news_appinn()
            if new_news:
                pass

    def start():
        """\
        主函数
        """
        pass

    def __del__(self):
        pickle.dump(self.news_list, file(self.fname, 'wb'))


if __name__ == '__main__':
    a = WebPusher('70292863:AAEzdiMxmhzT52xYsL6L8FbPi20lXU6WEpc')
    news_list = a.get_news_appinn()
    # for title, href in news_list:
    #     print title, href
