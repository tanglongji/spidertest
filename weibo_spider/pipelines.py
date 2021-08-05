# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import json

from openpyxl import Workbook


class WeiboSpiderPipeline:
    def __init__(self):
        self.wb = Workbook()
        self.ws = self.wb.active
        self.ws.append(['用户id', '微博名', '微博的id：一条微博的id', '正文', '头条文章的url', '图片的url', '视频的url',
                        '创建时间', ' 点赞数', '评论数', '转发数', '主题', '@用户', '微博的url：一条微博的url', '发布工具', '微博热评',
                        '转发的微博的用户id', '转发的微博的用户名', '转发的正文', '转发的图片url', '转发的头条文章的url', '转发的视频的url', '转发的微博的发布时间'
                                                                                                    '转发的微博的发布工具',
                        '转发的微博的@用户', '转发的微博的点赞数', '转发的微博的评论数', '转发的微博的转发数', '转发的微博的主题', '转发的微博的url'])

    def process_item(self, item, spider):
        line = [item.id, item.name, item.weibo_id, item.text, item.article_url, item.pic_url, item.video_url,
                item.post_time, item.attitudes_count, item.comments_count, item.repost_count, item.topics,
                item.at_user, item.weibo_url, item.post_tool, ',\n'.join(item.comments),
                item.repost['user_id'] if item.repost else '', item.repost['screen_name'] if item.repost else '',
                item.repost['text'] if item.repost else '', item.repost['pics'] if item.repost else '',
                item.repost['article_url'] if item.repost else '', item.repost['video_url'] if item.repost else '',
                item.repost['created_at'] if item.repost else '', item.repost['source'] if item.repost else '',
                item.repost['at_users'] if item.repost else '', item.repost['attitudes_count'] if item.repost else '',
                item.repost['comments_count'] if item.repost else '',
                item.repost['reposts_count'] if item.repost else '', item.repost['topics'] if item.repost else '',
                item.repost['url'] if item.repost else '']
        self.ws.append(line)
        self.wb.save('result.xlsx')
        return item
