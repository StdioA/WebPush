#!/usr/bin/env python
# coding: utf-8

import BeautifulSoup as bs
import requests
import cPickle as pickle
import time
import threading
import Queue
import sys

from tgbot import TgBot as tgbot

reload(sys)
sys.setdefaultencoding('utf-8')


class WebPusher(object):
    def __init__(self, token, fname="ded_nuaa.dat"):
        self.__message_queue = Queue.Queue()                      # 命令队列
        self.__news_queue = Queue.Queue()                         # 新闻队列，用于传输更新的新闻
        self.run = True                                           # 判定是否需要结束程序

        self.news_getter = self.get_news_ded                      # 新闻抓取函数，配置单独提出来
        self.fname = fname
        try:
            self.news_list = pickle.load(file(fname, 'rb'))
        except IOError:
            self.news_list = []

        try:
            self.subscriber = pickle.load(file("subscriber.dat", 'rb'))
        except IOError:
            self.subscriber = []

        # del self.news_list[0]
        self.bot = tgbot(token)
        print "Bot start:", self.bot.offset

    def get_news_ded(self):
        """\
        获取最新的教务处新闻
        """
        new_news = []
        url = 'http://ded.nuaa.edu.cn/HomePage/articles/'
        hr = requests.get(url)
        if hr.status_code != 200:
            return []

        html = bs.BeautifulSoup(hr.text)
        news_l = html.findAll('td', attrs={'class': 'tit1'})

        for news in reversed(news_l):
            link = news.findChild('a')
            href = url+link.attrs[0][1]
            title = link.text
            if not (title, href) in self.news_list:
                new_news.append((title, href))
                self.news_list.append((title, href))

        return new_news
        # TODO: 添加新闻发布日期

    def get_news_linux_cn(self):
        """\
        linux.cn新闻获取函数
        """
        new_news = []
        url = "https://linux.cn/"
        hr = requests.get(url)
        if hr.status_code != 200:
            return []

        html = bs.BeautifulSoup(hr.text)
        nl = html.findAll("ul", attrs={"class": "article-list leftpic"})
        for mod in reversed(nl):
            news_l = mod.findAll("a", attrs={"target": "_blank"})
            for news in reversed(news_l):
                attrs = dict(news.attrs)
                title = attrs.get("title", None)
                href = attrs.get("href", None)
                if (title and href) and ((title, href) not in self.news_list):
                    new_news.append((title, href))
                    self.news_list.append((title, href))

        return new_news

    def push_news(self, news):
        """\
        将新闻推送至tg账号
        """
        title, href = news
        try:
            print "Push news:", title
        except UnicodeEncodeError:
            print "Push news:", href

        for user in self.subscriber:
            self.bot.send_message(user, '\n'.join([title, href]))

    def update_news(self):
        """\
        定时刷新新闻
        """
        print "Start updating news"

        while True:
            new_news = self.news_getter()
            for news in new_news:
                self.__news_queue.put(news)

            pickle.dump(self.news_list, file(self.fname, 'wb')) # 定时将新闻列表写回，防止出现程序意外停止重启后推送一堆新闻的情况

            for i in range(300):
                if not self.run:
                    print "Stop updating news"
                    return
                time.sleep(1)

    def listen_news(self):
        """\
        接收新闻并进行处理（推送）
        """
        print "Start listening to news"

        while self.run or (not self.__news_queue.empty()):    # 若run变为0，则将消息处理完再退出线程
            try:
                while True:
                    news = self.__news_queue.get(timeout=1)   # 阻塞方式刷新，最长时间为1s
                    self.push_news(news)
            except Queue.Empty:
                pass

        print "Stop listening to news"

    def update_messages(self):
        """\
        获取bot收到的信息
        """
        print "Start updating messages"

        while self.run:
            result = self.bot.get_updates()
            if result:
                messages = result["result"]
                for message in messages:
                    self.__message_queue.put(message["message"])

        print "Stop updating messages"

    def listen_messages(self):
        """\
        监听收到的消息并按顺序进行处理
        """
        print "Start listening to messages"

        while self.run or (not self.__news_queue.empty()):  # 若run变为0，则处理完待处理的消息再结束线程
            try:
                message = self.__message_queue.get(timeout=1)
                self.execute_message(message)
            except Queue.Empty:
                pass

        print "Stop listening to messages"

    def execute_message(self, message):
        """\
        处理收到的消息
        """
        welcome = u"欢迎使用linux.cn非官方新闻推送bot！\n"

        help_str = u"""命令列表：
        /getlatest   -  获取最近新闻
        /subscribe   -  进行新闻订阅
        /unsubscribe -  取消新闻订阅
        /help        -  获取帮助信息"""

        fn = message["from"].get("first_name", "")
        ln = message["from"].get("last_name", "")
        if len(fn) > 10:                                                    # 避免出现名字特别长导致刷屏的情况
            fn = fn[:9]+"…"
        if len(ln) > 10:
            ln = ln[:9]+"…"
        name = " ".join([fn, ln])

        print "{text} from {name}".format(text=message["text"], name=name)

        text = message["text"]
        userid = message["from"]["id"]

        if text == "/start":
            self.bot.send_message(message["from"]["id"], welcome+help_str)

        elif text == "/help":
            self.bot.send_message(message["from"]["id"], help_str)

        elif text == "/subscribe":
            if userid not in self.subscriber:
                self.subscriber.append(userid)
                self.bot.send_message(userid, u"订阅成功！")
            else:
                self.bot.send_message(userid, u"您已订阅该服务！")

        elif text == "/unsubscribe":
            if userid not in self.subscriber:
                self.bot.send_message(userid, u"您未订阅该服务！")
            else:
                self.subscriber.remove(userid)
                self.bot.send_message(userid, u"已取消订阅！")

        elif text == "/getlatest":
            title, href = self.news_list[-1]
            self.bot.send_message(message["chat"]["id"], '\n'.join([title, href]))

        elif text == "/test":
            name = ' '.join([message["from"]["first_name"], message["from"]["last_name"]])
            self.bot.send_message(message["chat"]["id"], name+" "+time.ctime())

        elif text == "/kill" and message["chat"]["id"] == 90625935:
            self.run = False

    def start(self):
        """\
        主函数
        """
        func_list = [self.update_messages, self.update_news, self.listen_messages, self.listen_news]

        thread_list = [threading.Thread(target=f) for f in func_list]                                   # 创建线程
        # map(lambda x: x.setDaemon(True), [thread_list[1]])
        map(lambda x: x.start(), thread_list)                                                           # 启动线程
        map(lambda x: x.join(), thread_list)

        # 自己进行结束工作要比写在__del__里更稳妥！
        pickle.dump(self.news_list, file(self.fname, 'wb'))
        pickle.dump(self.subscriber, file("subscriber.dat", 'wb'))
        print "Bot stop:", self.bot.offset

if __name__ == '__main__':
    pusher = WebPusher('70292863:AAEzdiMxmhzT52xYsL6L8FbPi20lXU6WEpc', fname="ded_nuaa.dat")
    pusher.start()
    del pusher

# TODO: 添加一些常用命令
# TODO: 做成一个订阅号
# TODO: 考虑用multiprocessing解决问题（如果CPU是单核，多线程就可以了，不过可以考虑使用multiprocessing.dummy）
# TODO: 用logging记录调试信息(可以用tail -f实时查看)
