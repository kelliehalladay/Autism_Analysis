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
import nltk
nltk.download('punkt')
import contractions

reddit_autism = pd.read_csv('reddit_autism.csv')
reddit_autisminwomen = pd.read_csv('reddit_autisminwomen.csv')
reddit_autism_parenting = pd.read_csv('reddit_autism_parenting.csv')

reddit_autism['autism_sub'] = [1 for x in range(len(reddit_autism))]
reddit_autisminwomen['autism_sub'] = [1 for x in range(len(reddit_autisminwomen))]
reddit_autism_parenting['autism_sub'] = [0 for x in range(len(reddit_autism_parenting))]

autism_df = pd.concat([reddit_autism,reddit_autisminwomen,reddit_autism_parenting])

with open('reddit_autism_replies_json.json','r') as file:
    autism_replies = json.load(file)

with open('reddit_autisminwomen_replies_json.json','r') as file:
    autisminwomen_replies = json.load(file)

with open('reddit_autism_parenting_replies_json.json','r') as file:
    autism_parenting_replies = json.load(file)

autism_reply_df = pd.DataFrame(columns=['comment_author','comment_body','reply_author','reply_body','autism_sub'])
for k in autism_replies.keys():
    for v in autism_replies[k]:
        comment_author = k.split(':',1)[0]
        comment_body = k.split(':',1)[1]
        reply_author = v.split(':',1)[0]
        reply_body = v.split(':',1)[1]
        autism_sub = 1
        autism_reply_df.loc[len(autism_reply_df)] = [comment_author,comment_body,reply_author,reply_body,autism_sub]
for k in autisminwomen_replies.keys():
    for v in autisminwomen_replies[k]:
        comment_author = k.split(':',1)[0]
        comment_body = k.split(':',1)[1]
        reply_author = v.split(':',1)[0]
        reply_body = v.split(':',1)[1]
        autism_sub = 1
        autism_reply_df.loc[len(autism_reply_df)] = [comment_author,comment_body,reply_author,reply_body,autism_sub]
for k in autism_parenting_replies.keys():
    for v in autism_parenting_replies[k]:
        comment_author = k.split(':',1)[0]
        comment_body = k.split(':',1)[1]
        reply_author = v.split(':',1)[0]
        reply_body = v.split(':',1)[1]
        autism_sub = 0
        autism_reply_df.loc[len(autism_reply_df)] = [comment_author,comment_body,reply_author,reply_body,autism_sub]


autism_reply_df_full = pd.concat([autism_df[['comment_author','comment_body','reply_author','reply_body','autism_sub']],autism_reply_df]).reset_index().drop(columns=['index'])

autism_df_new = autism_df.reset_index().drop(columns=['index'])
autism_post_small = pd.DataFrame()
autism_post_small['author'] = autism_df_new['post_author']
body = []
for i in range(len(autism_df_new)):
    body += [f"{autism_df_new.loc[i]['post_title']} {autism_df_new.loc[i]['post_body']}"]
autism_post_small['body'] = body
autism_post_small['autism_sub'] = autism_df_new['autism_sub']

autism_comment_small = autism_reply_df_full[['comment_author','comment_body','autism_sub']].rename(columns={'comment_author':'author','comment_body':'body'})
autism_reply_small = autism_reply_df_full[['reply_author','reply_body','autism_sub']].rename(columns={'reply_author':'author','reply_body':'body'})
autism_small = pd.concat([autism_post_small,autism_comment_small,autism_reply_small]).drop_duplicates().reset_index().drop(columns=['index'])

autism_words = []
for row in range(len(autism_small)):
    ex = nltk.word_tokenize(contractions.fix(autism_small.loc[row]['body']))
    autism_words_row = []
    for i,word in enumerate(ex):
        if word in ['Autistic','Autism','autistic','autism']:
            if i <= 2:
                autism_words_row += [ex[i-2:i+4]]
            elif i >= len(ex)-3:
                autism_words_row += [ex[i-3:]]
            else:
                autism_words_row += [ex[i-3:i+4]]
    autism_words += [autism_words_row]
autism_small['autism_words'] = autism_words 

others = ['mother','Mother','mom','Mom','father','Father','dad','Dad','son','Son','daughter','Daughter','sister','Sister','brother','Brother','friend','Friend','he','He','she','She','his','His','her','Her','Husband','husband','Wife','wife','girlfriend','Girlfriend','gf','GF','boyfriend','Boyfriend','bf','BF']
autism_ind = []
for i in range(len(autism_small)):
    autism_ind_list = []
    if autism_small.loc[i]['autism_words'] == []:
        autism_ind_list += [0]
    else:
        for list in autism_small.loc[i]['autism_words']:
            if ('I' in list or 'i' in list) and ('am' in list or 'have' in list) and ('not' not in list and 'Not' not in list):
                autism_ind_list += [1]
            if ('I' in list or 'i' in list) and ('am' in list or 'have' in list) and ('not' in list or 'Not' in list):
                autism_ind_list += [0]
            elif 'my' in list and list.index('my') in ['autism','Autism']:
                autism_ind_list += [1]
            elif 'My' in list and list.index('My') in ['autism','Autism']:
                autism_ind_list += [1]
            else:
                autism_ind_list += [0]
    autism_ind += [max(autism_ind_list)]
autism_small['autism_ind'] = autism_ind
ally_ind = []
for j in range(len(autism_small)):
    ally_ind_list = []
    if autism_small.loc[j]['autism_words'] == [] or autism_small.loc[j]['autism_ind'] == 1:
        ally_ind_list += [0]
    else:
        for list in autism_small.loc[j]['autism_words']:
            for word in others:
                if word in list:
                    ally_ind_list += [1]
            else: 
                ally_ind_list += [0]
    ally_ind += [max(ally_ind_list)] 
autism_small['ally_ind'] = ally_ind
unspec = []
for k in range(len(autism_small)):
    if autism_small.loc[k]['autism_ind'] == 1 or autism_small.loc[k]['ally_ind'] == 1:
        unspec += [0]
    else:
        unspec += [1]
autism_small['unspec'] = unspec

user_flags = autism_small.drop(columns=['body','autism_words']).drop_duplicates().reset_index().drop(columns=['index'])

autism_sub = user_flags['autism_sub'].groupby(user_flags['author']).min()
autism_ind = user_flags['autism_ind'].groupby(user_flags['author']).max()
ally_ind = user_flags['ally_ind'].groupby(user_flags['author']).max()
unspec = user_flags['unspec'].groupby(user_flags['author']).max()

user_flag_calc = pd.concat([autism_sub,autism_ind,ally_ind,unspec],axis=1).reset_index()
ally = []
unsp = []
final_autism_ind = []
for row in range(len(user_flag_calc)):
    if user_flag_calc.loc[row]['autism_ind'] == 1:
        ally += [0]
    else:
        ally += [user_flag_calc.loc[row]['ally_ind']]
    if user_flag_calc.loc[row]['autism_ind'] == 1 or user_flag_calc.loc[row]['ally_ind'] == 1:
        unsp += [0]
    else:
        unsp += [1]
user_flag_calc['ally_ind'] = ally
user_flag_calc["unspec"] = unsp
for row in range(len(user_flag_calc)):
    if user_flag_calc.loc[row]['autism_ind'] == 1:
        final_autism_ind += [1]
    elif user_flag_calc.loc[row]['ally_ind'] == 1:
        final_autism_ind += [0]
    elif user_flag_calc.loc[row]['unspec'] == 1 and user_flag_calc.loc[row]['autism_sub'] == 1:
        final_autism_ind += [1]
    else:
        final_autism_ind += [0]
user_flag_calc['final_autism_ind'] = final_autism_ind

print(user_flag_calc)
user_flag_calc.to_csv('user_autism_indicator.csv')