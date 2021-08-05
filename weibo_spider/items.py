# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

# import scrapy
#
#
# class WeiboSpiderItem(scrapy.Item):
#     # define the fields for your item here like:
#     # name = scrapy.Field()
#     pass



import scrapy

from typing import Optional
from dataclasses import dataclass, field


@dataclass
class WeiboItem:
    id: int  # user_id
    name: str  #user_name
    post_time: str
    weibo_id: int
    attitudes_count: Optional[int]  # 点赞数
    comments_count: Optional[int]  # 评论数
    repost_count: Optional[int]   # 转发数

    text: Optional[str] = field(default=None)  # 正文
    pic_url: Optional[str] = field(default=None)  # 图片url
    article_url: Optional[str] = field(default=None)  # 头条文章url
    video_url: Optional[str] = field(default=None)  # video_url

    post_tool: Optional[str] = field(default=None)  # 发布工具

    topics: Optional[str] = field(default=None)  # 话题
    at_user: Optional[str] = field(default=None)  # @用户

    weibo_url: Optional[str] = field(default=None)  # 对应某一条微博的url

    repost: Optional[dict] = field(default=None)  # 转发的微博

    comments: Optional[list] = field(default=None) #评论（评论,点赞数)
    # comments_attitudes: Optional[int] = field(default=None)
