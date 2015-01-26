#! /usr/bin/python2.7
# -*-coding:utf-8-*-


import json
import os
import glob
import urllib2

from bs4 import BeautifulSoup
from datetime import datetime, timedelta

REPLY_URLBASE = 'http://m.blog.naver.com/CommentList.nhn?blogId=%s&logNo=%s'

get_today = lambda : datetime.now()

def get_reply(url):
    page = urllib2.urlopen(url)
    doc  = BeautifulSoup(page.read())
    return doc.find_all("li", {"class": "persc"})

def make_structure(blog_id, log_no, written_time, replies, encoding='utf-8'):
    extract_crawlerTime  = lambda: get_today().strftime("%Y-%m-%d %H:%M")
  
    def reply_json(reply):
        if reply.find("p") != None and reply.find("div", {"class":"dsc_id"}) != None:
            return {u"content": reply.find("p").get_text(),
                    u"date": reply.find("span").get_text().encode("utf"),
                    u"blogId": reply.find("div", {"class":"dsc_id"}).find("a")["href"].rsplit("blogId=", 1)[1]}

    def extract_reply(replies):
        all_replies = []
        for reply in range(0, len(replies)):
            tmp = reply_json(replies[reply])
            if tmp != None:
                retmp = replies[reply].find_all("ul", {"class":"lst_repl_sub"})
                re_replies = []
                for re in range(0, len(retmp)):
                    if reply_json(retmp[re]) != None:
                        re_replies.append(reply_json(retmp[re]))
                if re_replies != []:
                    tmp["reReply"] = re_replies
                all_replies.append(tmp)
        return all_replies

    return {u"blogId": blog_id,
            u"logNo": log_no,
            u"writtenTime": written_time,
            u"comments": extract_reply(replies),
            u"commentCrawledTime": extract_crawlerTime()}

def make_json(blog, blog_id, log_no, date, directory_seq, basedir, seconddir = "comments"):
    PATH = '%s/%02d/%02d' % (int(date[0:4]), int(date[5:7]), int(date[8:10]))
    targetpath = '%s/%s/%02d/%s' % (basedir, seconddir, directory_seq, PATH)
    if not os.path.exists(targetpath):
        os.makedirs(targetpath)
    filename = '%s/%s-%s.json' % (targetpath, blog_id, log_no)
    f        = open(filename, 'w')
    jsonstr  = json.dumps(blog, sort_keys=True, indent=4, encoding='utf-8')
    f.write(jsonstr)
    f.close()

def error_log_url(blog_id, log_no, date, directory_seq, basedir, seconddir = "logs"):
    targetpath = '%s/%s' % (basedir, seconddir)
    if not os.path.exists(targetpath):
        os.makedirs(targetpath)
    filename = '%s/error_url_comment_%s-%02d-%02d.txt' % (targetpath, int(date[0:4]), int(date[5:7]), int(date[8:10]))
    f   = open(filename, 'a')
    url = '%s, http://m.blog.naver.com/%s/%s, access denied\n' % (directory_seq, blog_id, log_no)
    f.write(url)
    f.close()

def comment_crawl(blog_id, log_no, written_time, date, directory_seq, basedir):
    reply_doc = get_reply(REPLY_URLBASE % (blog_id, log_no))
    if reply_doc != None:
        blog = make_structure(blog_id, log_no, written_time, reply_doc)
        make_json(blog, blog_id, log_no, date, directory_seq, basedir)
    else:
        error_log_url(blog_id, log_no, date, directory_seq, basedir)

def file_read(filename):
   json_data = open(filename)
   data = json.load(json_data)
   return data

def return_information(directory_seq, basedir, date, seconddir ="lists", thirddir="comments"):
    directory_seq = int(directory_seq)
    targetpath = '%s/%s/%02d/%s/%02d/%02d'\
                         % (basedir, seconddir, directory_seq,\
                            int(date[0:4]), int(date[5:7]), int(date[8:10]))
   
    filenames = glob.glob('%s/*.json' % targetpath)
    for filename in reversed(filenames):
        items = file_read(filename)
        for i, blog in enumerate(items):
            check_targetpath = '%s/%s/%02d/%s/%02d/%02d'\
                            % (basedir, thirddir, directory_seq,\
                               int(date[0:4]), int(date[5:7]), int(date[8:10]))
            check_filename = '%s-%s.json' % (items[i]['blogId'], items[i]['logNo'])
            if not os.path.isfile('%s/%s' % (check_targetpath, check_filename)):
                comment_crawl(items[i]['blogId'], 
                              items[i]['logNo'],
                              items[i]['writtenTime'],
                              date, directory_seq, basedir)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Get input parameters.',
                        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-c', '--category', required=True, dest='directory_seq',
                         help='assign target category to crawl')
    parser.add_argument('-p', '--path', dest='basedir',
                         help='assign data path')
    parser.add_argument('-d', '--date', dest='date',
                         help='assign date to crawl')
    args = parser.parse_args()

    if not args.basedir:
        args.basedir = './data'

    return_information(args.directory_seq, args.basedir, args.date)
