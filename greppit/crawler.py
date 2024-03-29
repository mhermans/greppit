import datetime, py2neo
from greppit import RedditGraph as Reddit
from greppit import log

class RedditCrawler(object):
    def __init__(self, reddit_user_name=None, reddit_password=None,
            graph_uri="http://localhost:7474/db/data/"):
        """docstring for __init__"""

        self.gdb = py2neo.neo4j.GraphDatabaseService("http://localhost:7474/db/data/")
        self.reddit_api = Reddit(
                user_agent='neo4reddit crawler || misbehaving?:/u/mhermans')

    def crawl_subreddit(self, name, limit=100, full=True, resume=True):
        """docstring for crawl_subreddits"""
        sr = self.reddit_api.get_subreddit(name)
        for i, sub in enumerate(sr.get_hot(limit=limit)):
            log.info('Parsing submission nr.%s' % i)
            subm_node = self.gdb.get_indexed_node('Submissions', 'id', sub.id)
            print subm_node
            if not subm_node:
                sub.save()
                [c.save() for c in sub.all_flat_comments()]

    def clear_db(self):
        """WARNING: clears the entire graph!"""

        q = 'START n=node(*) MATCH n-[r?]-() where ID(n) <> 0 DELETE n, r;'
        py2neo.cypher.execute(self.gdb, q)
