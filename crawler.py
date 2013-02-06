import datetime
import py2neo, pandas
from mpatch import Reddit, Subreddit, Submission, Comment, Redditor

class RedditCrawler(object):
    def __init__(self, reddit_user_name=None, reddit_password=None,
            neo4j_uri="http://localhost:7474/db/data/"):
        """docstring for __init__"""

        self.gdb = neo4j.GraphDatabaseService("http://localhost:7474/db/data/")
        self.reddit_api = praw.Reddit(
                user_agent='neo4reddit crawler || misbehaving?:/u/mhermans')

    def crawl_subreddit(self, name, limit=100, full=True, resume=True):
        """docstring for crawl_subreddits"""
        pass

    def clear_db(self):
        """WARNING: clears the entire graph!"""

        q = 'START n=node(*) MATCH n-[r?]-() where ID(n) <> 0 DELETE n, r;'
        py2neo.cypher.execute(self.gdb, q)
