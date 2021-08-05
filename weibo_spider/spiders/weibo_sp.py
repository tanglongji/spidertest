import scrapy

import json

import sys

import os

import pprint

import re

import datetime

import collections

from lxml import etree

import parsel

from datetime import date, datetime, timedelta

from weibo_spider.items import WeiboItem

# today = date.today()
# last_year = date(today.year-1,today.month,today.day)

def get_config():
    """
    获取爬虫相关的配置信息，
    :return: dict_config
    """
    config_path = os.path.split(os.path.realpath(__file__))[0] + os.sep + 'configure.json'

    try:
        with open(config_path, encoding='utf-8') as f:
            config = json.loads(f.read())
            # print('config')
            # print('_' * 30)
            # print(config)
            # print('_' * 30)
            return config
    except Exception as e:
        # print(e.__traceback__)
        sys.exit()

# cookie = 'SINAGLOBAL=9335271419770.348.1618145465990; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9WFqinPqOpH2mEMEkX4WU88h5JpX5KMhUgL.FoM0ShM4eh2fe0B2dJLoI0nLxKBLB.2LBKBLxK-L1hMLB.2LxKnL1hMLB-BLxKnLBo2L1hqLxKnL1h-L1K5LxKnL1-zL12ikM7tt; wvr=6; ALF=1659058879; SSOLoginState=1627522879; SCF=AuySD0bBzNOYKpAtz7M9HjkyH4XhG6cWjOi38AAEJInEHodqPTkHaOCuz8JiVRDEuFRJbUjFRW92aS_dDf2wpHc.; SUB=_2A25MBncQDeRhGeFN71UY8C_JyDiIHXVvcu_YrDV8PUNbmtAKLRjBkW9NQA7feBB437j6JznClLaTztvPjZmNeAh1; _s_tentry=login.sina.com.cn; Apache=1451682088435.2666.1627522887538; ULV=1627522887721:356:99:18:1451682088435.2666.1627522887538:1627516380930; wb_view_log_7347901534=1280*7201.5&3440*14401; UOR=www.baidu.com,s.weibo.com,teams.microsoft.com; webim_unReadCount={"time":1627550987107,"dm_pub_total":0,"chat_group_client":0,"chat_group_notice":0,"allcountNum":0,"msgbox":0}'

class T11Spider(scrapy.Spider):
    name = 'weibo_sp'
    allowed_domains = ['m.weibo.cn','weibo.com']
    # start_urls = ['https://m.weibo.cn/api/container/getIndex?containerid=100505{0}'.format(user_id) for user_id in config['user_id_list']]
    # start_urls = ['https://weibo.com/igaming?refer_flag=0000015010_&from=feed&loc=nickname&is_all=1']
    # start_urls = ['https://m.weibo.cn/api/container/getIndex?containerid=107603{0}&page=1'.format(user_id)
    #               for user_id in config['user_id_list']]
    def start_requests(self):
        # url = 'https://weibo.com/sportschannel?from=page_100505_profile&wvr=6&mod=myfollowhisfan&refer_flag=1005050010_&is_all=1'
        # url = 'https://weibo.com/PANDORAChina?is_all=1'
        # url = 'https://weibo.com/apmmc?nick=APM_MONACO&is_hot=1'
        # url = 'https://weibo.com/swarovskicom?is_all=1'
        config = get_config()
        if not config:
            print('配置读取失败,请检查是否有configure.json文件')
            sys.exit()

        headers = config['headers']
        headers['cookie'] = config['cookie']

        for url in config['url_list']:
            yield scrapy.Request(url=url, headers=headers, callback=self.parse)

    def parse(self,response):
        print('*'*25, 'start', '*'*25)
        html = response.text
        # print(html)
        # print(response.url)
        result = re.search("uid=(\d+)", html)
        print(result.group())
        user_id = result.group()[4:]
        print('user_id', user_id)
        return scrapy.Request(url='https://m.weibo.cn/api/container/getIndex?containerid=100505{0}'.format(user_id), callback=self.w_parse)


    def w_parse(self, response):
        print('++++++++++++++++++++++++++++++++++++')
        # js = json.loads(response.text)
        js = response.json()
        # print(js)
        user_info = js['data']['userInfo']
        print('微博条数', user_info['statuses_count'], '用户id', user_info['id'])
        for page in range(1, user_info['statuses_count']//10+1):
        # for page in range(44, 45):
            yield scrapy.Request(url='https://m.weibo.cn/api/container/getIndex?containerid=107603{0}&page={1}'.format(user_info['id'], page), callback=self.parse_page)

    def parse_page(self, response):
        
        js = response.json()
        # pprint.pprint(js)
        # print('*****************S****************page**************************************')
        # # pprint.pprint(js)
        # print('*********************************page**************************************')
        if js['ok']:
            weibos = js['data']['cards']
            for w in weibos:
                weibo_info = w['mblog']
                if weibo_info['pic_num'] > 9 or weibo_info.get('isLongText'):
                    yield scrapy.Request(url='https://m.weibo.cn/detail/{}'.format(weibo_info['id']), callback=self.parse_long_weibo)
                else:
                    weibo_info['url'] = w['scheme']
                    # print('108')
                    wb = self.get_one_weibo(weibo_info)
                    if wb:
                        self.print_weibo(wb)
                        weibo_item = WeiboItem(wb['user_id'],wb['screen_name'],wb['created_at'],wb['id'],wb['attitudes_count'],wb['comments_count'],wb['reposts_count'])
                        weibo_item.text = wb['text']
                        weibo_item.pic_url = wb['pics']
                        weibo_item.article_url = wb['article_url']
                        weibo_item.video_url = wb['video_url']
                        weibo_item.post_tool = wb['source']
                        weibo_item.topics = wb['topics']
                        weibo_item.at_user = wb['at_users']
                        weibo_item.weibo_url = wb['url']
                        weibo_item.repost = wb['retweet']
                        yield scrapy.Request(url='https://m.weibo.cn/comments/hotflow?max_id_type=0&mid={}'.format(wb['id']), 
                        callback= self.parse_weibo_with_comments, cb_kwargs={'weibo_item':weibo_item})
                        # yield weibo_item

    def parse_weibo_with_comments(self, reponse, weibo_item):
        """
        解析微博评论
        """

        comment_json = reponse.json()
        # print("\033[1;32m *\033[0m"*60)
        # pprint.pprint(comment_json)
        # print("\033[1;32m *\033[0m" * 60)
        comments = []
        # try:
        if comment_json['ok']:
            comments_data = comment_json['data']
            comments_data = comments_data['data']

            for com_d in comments_data:
                print(type(com_d),com_d)
                if com_d['text'].find('<')>=0:
                    comment = parsel.Selector(com_d['text']).xpath('string(.)').get()
                else:
                    comment = com_d['text']
                comments.append((comment+' 点赞数：'+str(com_d['like_count'])))    
        else:
            print("\033[1;32m *\033[0m"*60)
            print("\033[1;31m get_on_weibo_error,没有评论\033[0m")
            print("\033[1;32m *\033[0m" * 60)

        weibo_item.comments = comments
        yield weibo_item

    def get_one_weibo(self,weibo_info):
        try:
            # weibo_id = weibo_info['id']
            retweeted_status = weibo_info.get('retweeted_status')

            weibo = self.parse_weibo(weibo_info)
            weibo['retweet'] = None
            if retweeted_status and retweeted_status.get('id'):  # 转发
                # print('转发')
                # pprint.pprint(retweeted_status)

                retweeted_status['url'] = 'https://m.weibo.cn/detail/{0}'.format(retweeted_status['id'])
                retweet = self.parse_weibo(retweeted_status)
                retweet['created_at'] = self.standardize_date(
                    retweeted_status['created_at'])
                weibo['retweet'] = retweet

            weibo['created_at'] = self.standardize_date(
                weibo_info['created_at'])
            return weibo
        except Exception as e:
            print("\033[1;32m *\033[0m"*60)
            print("\033[1;31m get_on_weibo_error,获取一条微博出错\033[0m")
            print(e.__traceback__)
            print("\033[1;31m get_on_weibo_error,获取一条微博出错\033[0m")
            print("\033[1;32m *\033[0m" * 60)

    def parse_weibo(self, weibo_info):
        weibo = collections.OrderedDict()
        if weibo_info['user']:
            weibo['user_id'] = weibo_info['user']['id']
            weibo['screen_name'] = weibo_info['user']['screen_name']
        else:
            weibo['user_id'] = ''
            weibo['screen_name'] = ''
        weibo['id'] = int(weibo_info['id'])
        weibo['bid'] = weibo_info['bid']
        text_body = weibo_info['text']
        selector = etree.HTML(text_body)  # 某条微博的html代码

        if not selector:
            
            weibo['text'] = text_body
            weibo['topics'] = ''
            weibo['at_users'] = ''
            weibo['location'] = ''
            weibo['article_url'] = ''
        else:
            weibo['text'] = selector.xpath('string(.)')
            weibo['article_url'] = self.get_article_url(selector)
            weibo['topics'] = self.get_topics(selector)
            weibo['at_users'] = self.get_at_users(selector)
            weibo['location'] = self.get_location(selector)

        weibo['pics'] = self.get_pics(weibo_info)
        weibo['video_url'] = self.get_video_url(weibo_info)

        weibo['created_at'] = weibo_info['created_at']
        weibo['source'] = weibo_info['source']
        weibo['attitudes_count'] = self.string_to_int(
            weibo_info.get('attitudes_count', 0))
        weibo['comments_count'] = self.string_to_int(
            weibo_info.get('comments_count', 0))
        weibo['reposts_count'] = self.string_to_int(
            weibo_info.get('reposts_count', 0))

        weibo['url'] = weibo_info['url']
        weibo = self.standardize_info(weibo)
        # pprint.pprint(weibo)
        return weibo

    def parse_long_weibo(self, response):
        """
        长微博解析
        """

        html = response.text
        # print('******************************************************************************************')
        # print('parse_long_weibo')
        # print('******************************************************************************************')
        # print(html)

        html = html[html.find('"status":'):]
        html = html[:html.rfind('"hotScheme"')]
        html = html[:html.rfind(',')]
        html = '{' + html + '}'
        js = json.loads(html, strict=False)
        weibo_info = js.get('status')
        if weibo_info:
            weibo_info['url'] = response.url
            weibo = self.parse_weibo(weibo_info)
            weibo['created_at'] = self.standardize_date(
                weibo_info['created_at'])

            self.print_weibo(weibo)
            try:
                weibo_item = WeiboItem(weibo['user_id'], weibo['screen_name'], weibo['created_at'], weibo['id'], weibo['attitudes_count'],
                                       weibo['comments_count'], weibo['reposts_count'])
                
                weibo_item.text = weibo['text']
                weibo_item.pic_url = weibo['pics']
                weibo_item.arctile_url = weibo['article_url']
                weibo_item.video_url = weibo['video_url']
                weibo_item.post_tool = weibo['source']
                weibo_item.topics = weibo['topics']
                weibo_item.at_user = weibo['at_users']
                weibo_item.weibo_url = weibo['url']
                weibo_item.repost = weibo.get('retweet',None)
                # post_year, post_month, post_day = list(map(int, weibo_item.post_time.split('-')))
                
                yield scrapy.Request(url='https://m.weibo.cn/comments/hotflow?max_id_type=0&mid={}'.format(weibo['id']), 
                callback=self.parse_weibo_with_comments, cb_kwargs={'weibo_item':weibo_item})
                # yield weibo_item
            except Exception as e:
                print()
                print("\033[1;32m *\033[0m"*60)
                print('parse_long weibo 出错')
                print(e.__traceback__)
                print("\033[1;32m *\033[0m"*60)
                print()

    def string_to_int(self, string):
        """字符串转换为整数"""
        if isinstance(string, int):
            return string
        elif string.endswith(u'万+'):
            string = int(string[:-2] + '0000')
        elif string.endswith(u'万'):
            string = int(string[:-1] + '0000')
        return int(string)

    def get_topics(self, selector):
        """获取参与的微博话题"""
        span_list = selector.xpath("//span[@class='surl-text']")
        topics = ''
        topic_list = []
        for span in span_list:
            text = span.xpath('string(.)')
            if len(text) > 2 and text[0] == '#' and text[-1] == '#':
                topic_list.append(text[1:-1])
        if topic_list:
            topics = ','.join(topic_list)
        return topics

    def get_article_url(self, selector):
        """获取微博中头条文章的url"""
        article_url = ''
        text = selector.xpath('string(.)')
        if text.startswith(u'发布了头条文章'):
            url = selector.xpath('//a/@data-url')
            if url and url[0].startswith('http://t.cn'):
                article_url = url[0]
        return article_url

    def get_at_users(self, selector):
        """获取@用户"""
        a_list = selector.xpath('//a')
        at_users = ''
        at_list = []
        for a in a_list:
            if '@' + a.xpath('@href')[0][3:] == a.xpath('string(.)'):
                at_list.append(a.xpath('string(.)')[1:])
        if at_list:
            at_users = ','.join(at_list)
        return at_users

    def get_pics(self, weibo_info):
        """获取微博原始图片url"""
        if weibo_info.get('pics'):
            pic_info = weibo_info['pics']
            pic_list = [pic['large']['url'] for pic in pic_info]
            pics = ','.join(pic_list)
        else:
            pics = ''
        return pics

    def get_video_url(self, weibo_info):
        """获取微博视频url"""
        video_url = ''
        video_url_list = []
        if weibo_info.get('page_info'):
            if ((weibo_info['page_info'].get('urls')
                 or weibo_info['page_info'].get('media_info'))
                    and weibo_info['page_info'].get('type') == 'video'):
                media_info = weibo_info['page_info']['urls']
                if not media_info:
                    media_info = weibo_info['page_info']['media_info']
                video_url = media_info.get('mp4_720p_mp4')
                if not video_url:
                    video_url = media_info.get('mp4_hd_url')
                if not video_url:
                    video_url = media_info.get('hevc_mp4_hd')
                if not video_url:
                    video_url = media_info.get('mp4_sd_url')
                if not video_url:
                    video_url = media_info.get('mp4_ld_mp4')
                if not video_url:
                    video_url = media_info.get('stream_url_hd')
                if not video_url:
                    video_url = media_info.get('stream_url')
        if video_url:
            video_url_list.append(video_url)
        live_photo_list = self.get_live_photo(weibo_info)
        if live_photo_list:
            video_url_list += live_photo_list
        return ';'.join(video_url_list)

    def get_live_photo(self, weibo_info):
        """获取live photo中的视频url"""
        live_photo_list = []
        live_photo = weibo_info.get('pic_video')
        if live_photo:
            prefix = 'https://video.weibo.com/media/play?livephoto=//us.sinaimg.cn/'
            for i in live_photo.split(','):
                if len(i.split(':')) == 2:
                    url = prefix + i.split(':')[1] + '.mov'
                    live_photo_list.append(url)
            return live_photo_list

    def get_location(self, selector):
        """获取微博发布位置"""
        location_icon = 'timeline_card_small_location_default.png'
        span_list = selector.xpath('//span')
        location = ''
        for i, span in enumerate(span_list):
            if span.xpath('img/@src'):
                if location_icon in span.xpath('img/@src')[0]:
                    location = span_list[i + 1].xpath('string(.)')
                    break
        return location

    def standardize_info(self, weibo):
        """标准化信息，去除乱码"""
        for k, v in weibo.items():
            if 'bool' not in str(type(v)) and 'int' not in str(
                    type(v)) and 'list' not in str(
                        type(v)) and 'long' not in str(type(v)):
                weibo[k] = v.replace(u'\u200b', '').encode(
                    sys.stdout.encoding, 'ignore').decode(sys.stdout.encoding)
        return weibo

    def standardize_date(self, created_at):
        """标准化微博发布时间"""
        if u'刚刚' in created_at:
            created_at = datetime.now().strftime('%Y-%m-%d')
        elif u'分钟' in created_at:
            minute = created_at[:created_at.find(u'分钟')]
            minute = timedelta(minutes=int(minute))
            created_at = (datetime.now() - minute).strftime('%Y-%m-%d')
        elif u'小时' in created_at:
            hour = created_at[:created_at.find(u'小时')]
            hour = timedelta(hours=int(hour))
            created_at = (datetime.now() - hour).strftime('%Y-%m-%d')
        elif u'昨天' in created_at:
            day = timedelta(days=1)
            created_at = (datetime.now() - day).strftime('%Y-%m-%d')
        else:
            created_at = created_at.replace('+0800 ', '')
            temp = datetime.strptime(created_at, '%c')
            created_at = datetime.strftime(temp, '%Y-%m-%d')
        return created_at

    def print_weibo(self, weibo):
        """打印微博，若为转发微博，会同时打印原创和转发部分"""
        pass 

        # print('*'*25,'weibo_print','*'*25)
        # if weibo.get('retweet'):
        #     print('*' * 100)
        #     print(u'转发部分：')
        #     self.print_one_weibo(weibo['retweet'])
        #     print('*' * 100)
        #     print(u'原创部分：')
        # self.print_one_weibo(weibo)
        # print('-' * 120)

    def print_one_weibo(self, weibo):
        """打印一条微博"""
        pass 
        # try:
        #     print(u'微博id：%d', weibo['id'])
        #     print(u'微博正文：%s', weibo['text'])
        #     print(u'原始图片url：%s', weibo['pics'])
        #     print(u'微博位置：%s', weibo['location'])
        #     print(u'发布时间：%s', weibo['created_at'])
        #     print(u'发布工具：%s', weibo['source'])
        #     print(u'点赞数：%d', weibo['attitudes_count'])
        #     print(u'评论数：%d', weibo['comments_count'])
        #     print(u'转发数：%d', weibo['reposts_count'])
        #     print(u'话题：%s', weibo['topics'])
        #     print(u'@用户：%s', weibo['at_users'])
        #     print('source', weibo['source'])
        #     print(u'微博链接url：{0}'.format(weibo['url']))
        # except Exception as e:
        #     print("\033[1;32m *\033[0m"*60)
        #     print('print_error')
        #     print(e.__traceback__)
        #     print("\033[1;32m *\033[0m" * 60)





















