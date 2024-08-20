from bs4 import BeautifulSoup as bsoup
import requests
from time import sleep
from selenium import webdriver
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import numpy as np
import pandas as pd
import praw
from praw.models import MoreComments
import json
import gologin
from collections import deque

options = webdriver.ChromeOptions()
options.page_load_strategy="eager"
options.add_argument('--disable-blink-features=AutomationControlled')
driver = webdriver.Chrome(options=options)

reddit = praw.Reddit(
    client_id = "PuOZwoZV9cUQkjJaycIXuw",
    client_secret = "U4HxxsDh37YNREZ346eaGuiQUTFT5Q",
    user_agent = "RedditScraper by Wonderful-Leek-6351",
    username = "Wonderful-Leek-6351",
    password = "*****************" 
)
print(reddit.user.me())
autism = set()

def reply_func(comments):
    replist = []
    for c in comments:
        if isinstance(c,MoreComments):
            continue
        replist += [f"{c.author}:{c.body}"]
    return replist

class MyQueue:
    '''Creates a queue structure
    Elements can be enqueued
    First element to be enqueued in current queue can be dequeued'''
    def __init__(self):   #initialize an emtpy queue
        self.queue = deque()
    def __str__(self):
        return str(self.queue)
    def empty(self):    #Check whether or not queue is empty
        if self.queue == deque([]):
            return True
        else:
            return False
    def enqueue(self,element):  #enqueue an element
        self.element = element
        self.queue.append(self.element)
        return self.queue
    def dequeue(self):    #dequeue first element
        self.queue.popleft()
        return self.queue
    def first(self):    #display first element in queue
        return self.queue[0]

reddit_autism_df = pd.DataFrame(columns=['post_id','post_author','post_title','post_body','comment_id','comment_author','comment_body','reply_id','reply_author','reply_body'])
replydict = dict()
q = MyQueue()
for i,submission in enumerate(reddit.subreddit('AutismInWomen').hot(limit=100)):
    post_id = i
    print(f"post: {i}")
    post_author = submission.author
    post_title = submission.title
    post_body = submission.selftext
    for j,comment in enumerate(submission.comments):
        comment_id = j
        print(f"comment: {j}")
        if isinstance(comment,MoreComments):
            continue
        comment_author = comment.author
        comment_body = comment.body
        replylist = comment.replies
        for k,reply in enumerate(comment.replies):
            reply_id = k
            print(f"reply: {k}")
            if isinstance(reply,MoreComments):
                continue
            reply_author = reply.author
            reply_body = reply.body
            reddit_autism_df.loc[len(reddit_autism_df)] = [post_id,post_author,post_title,post_body,comment_id,comment_author,comment_body,reply_id,reply_author,reply_body]
            replydict[f"{reply.author}:{reply.body}"] = reply_func(reply.replies)
            for r in reply.replies:
                q.enqueue(r)
while q.empty() == False:
    u = q.first()
    q.dequeue()
    if isinstance(u,MoreComments):
        continue
    replydict[f"{u.author}:{u.body}"] = reply_func(u.replies)
    for v in u.replies:
        q.enqueue(v)

reddit_autism_df.to_csv('reddit_autisminwomen.csv')
with open('reddit_autisminwomen_replies_json.json','w') as json_file:
    json.dump(replydict, json_file, indent=4)
