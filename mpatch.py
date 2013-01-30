import datetime
from py2neo import neo4j

from praw.objects import Subreddit, Comment, Submission, Redditor, RedditContentObject
from praw import Reddit


# Monkeypatching praw objects

# subclass Reddit object to take graph uri on init?
#class NeoReddit(Reddit):
#    def __init__(self, neo4j_uri):
#        super(Reddit, self).__init__

# alternative atm:
RedditContentObject.gdb = neo4j.GraphDatabaseService("http://localhost:7474/db/data/")

# SUBREDDIT #
# ========= #

def _get_subreddit_data(self):
    props = ['accounts_active', 'created', 'created_utc', 'description',
            'display_name', 'header_img', 'id', 'name', 'over18', 'subscribers',
            'title', 'url']

    if not self._populated:
        self._populate(json_dict=None, fetch=True)
    data = self.__dict__

    subreddit_data = {key : value for key, value in data.items() if key in props }

    return subreddit_data

def _save_subreddit(self):
    props = self.data()
    props['updated'] = 'now'
    sr_node = self.gdb.get_or_create_indexed_node('Subreddit', 'id', props['id'], props)

    reddit_node = self.gdb.get_node(0)
    self.gdb.get_or_create_relationships(
        (reddit_node, "CONTAINS", sr_node, props)
    )

    return sr_node

Subreddit.data = _get_subreddit_data
Subreddit.save = _save_subreddit

# SUBMISSION #
# ========== #

def _get_submission_data(self):
    props = ['created', 'created_utc', 'id', 'domain',
        'downs', 'is_self', 'name', 'num_comments', 'permalink',
        'score', 'selftext', 'subreddit_id', 'ups', 'url']
    data = self.__dict__
    submission_data = {key : value for key, value in data.items() if key in props }
    if self.author:
        submission_data['author_name'] = self.author.name

    return submission_data

def _save_submission(self, full=True, update=False):
    props = self.data()
    #props['updated'] = datetime.datetime.now()
    subm_node = self.gdb.get_or_create_indexed_node('Submissions', 'id', props['id'], props)

    if full:
        # get full subreddit object and save that with rel
        props = {'created' : 'now' } #TODO
        sr_node = self.subreddit.save()
        self.gdb.get_or_create_relationships(
            (sr_node, "CONTAINS", subm_node, props)
        )

        # get full author object, and save that with rel
        if self.author:
            props = {'created' : 'now' } #TODO
            author_node = self.author.save()
            self.gdb.get_or_create_relationships(
                (subm_node, "AUTHOR", author_node, props)
            )
    return subm_node

Submission.data = _get_submission_data
Submission.save = _save_submission

# USER #
# ==== #

def _get_user_data(self):
    user_props = ['comment_karma', 'created', 'created_utc',
            'id', 'link_karma', 'name']

    if not self._populated:
        self._populate(json_dict=None, fetch=True)
    data = self.__dict__
    user_data = {key : value for key, value in data.items() if key in user_props}

    return user_data

def _save_user(self):
    props = self.data()
    print props
    #props['updated'] = datetime.datetime.now()
    n = self.gdb.get_or_create_indexed_node('Users', 'id', props['id'], props)

    return n

Redditor.data = _get_user_data
Redditor.save = _save_user

if __name__ == '__main__':
    r = Reddit('rest')
    s = r.get_submission('http://www.reddit.com/r/programming/comments/17j839/curiosity_the_gnu_foundation_does_not_consider/')
    u = s.author
    c = s.comments[0]
    sr = s.subreddit

    s2 = r.get_submission('http://www.reddit.com/r/politics/comments/178763/congressman_obama_is_upholding_a_soviet/')
    #print s.data()
    #s.save()
