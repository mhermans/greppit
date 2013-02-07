import datetime
import py2neo, pandas
from mpatch import Subreddit, Submission, Comment, Redditor, log
import praw

class RedditCrawler(object):
    def __init__(self, reddit_user_name=None, reddit_password=None,
            graph_uri="http://localhost:7474/db/data/"):
        """docstring for __init__"""

        self.gdb = py2neo.neo4j.GraphDatabaseService("http://localhost:7474/db/data/")
        self.reddit_api = praw.Reddit(
                user_agent='neo4reddit crawler || misbehaving?:/u/mhermans')

    def crawl_subreddit(self, name, limit=100, full=True, resume=True):
        """docstring for crawl_subreddits"""
        sr = self.reddit_api.get_subreddit(name)
        for i, sub in enumerate(sr.get_hot(limit=limit)):
            log.info('Parsing submission nr.%s' % i)
            sub.save()
            [c.save() for c in sub.all_flat_comments()]

    def clear_db(self):
        """WARNING: clears the entire graph!"""

        q = 'START n=node(*) MATCH n-[r?]-() where ID(n) <> 0 DELETE n, r;'
        py2neo.cypher.execute(self.gdb, q)

rc = RedditCrawler()
rc.crawl_subreddit('Belgium', 1000)
rc.crawl_subreddit('Finland', 1000)
