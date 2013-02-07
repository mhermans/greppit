import datetime, logging
from py2neo import neo4j

from praw.objects import Subreddit, Comment, Submission, Redditor, RedditContentObject
import praw
from praw import BaseReddit


log = logging.getLogger('reddit crawler')
log.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
log.addHandler(ch)

def utc_now_timestamp():
    return (datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds()

# [ ] make sure indexes are existing get_or_create_index()
# [ ] store type/fullname (fullname() is a praw object function)
# [ ] store updated timestamp utc->timestamp code
# [ ] accessable initialiser for gdb uri
# [ ] store labels for every object
# [ ] solution for restoring praw objects based on stored data?


# Monkeypatching praw objects

# subclass Reddit object to take graph uri on init?
#class BaseReddit(BaseReddit):
#    def __init__(self, neo4j_uri):
#        super(Reddit, self).__init__

# alternative atm:
RedditContentObject.gdb = neo4j.GraphDatabaseService("http://localhost:7474/db/data/")


# SUBREDDIT #
# ========= #

def _get_subreddit_data(self):
    props = ['accounts_active', 'created', 'created_utc', 'description',
            'display_name', 'id', 'name', 'over18', 'subscribers',
            'title', 'url']

    if not self._populated:
        self._populate(json_dict=None, fetch=True)
    data = self.__dict__

    subreddit_data = {key : value for key, value in data.items() if key in props }

    return subreddit_data

def _save_subreddit(self):
    props = self.data()
    props['updated'] = utc_now_timestamp()
    props['label'] = props['display_name']
    props['type'] = 'subreddit'
    log.info('Saving node for subreddit %s' % props['label'])
    sr_node = self.gdb.get_or_create_indexed_node('Subreddits', 'id', props['id'], props)

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
        'score', 'selftext', 'subreddit_id', 'ups', 'url', 'permalink', 'title']
    data = self.__dict__
    submission_data = {key : value for key, value in data.items() if key in props }
    if self.author:
        submission_data['author_name'] = self.author.name

    return submission_data

def _save_submission(self, full=True, update=False):
    props = self.data()
    props['updated'] = utc_now_timestamp() 
    props['label'] = props['title'][0:15]
    props['type'] = 'submission'
    log.info('Saving node for submission "%s..."' % props['label'])
    subm_node = self.gdb.get_or_create_indexed_node('Submissions', 'id', props['id'], props)

    if full:
        # get full subreddit object and save that with rel
        props = {'created' : utc_now_timestamp() } #TODO
        sr_node = self.subreddit.save()
        self.gdb.get_or_create_relationships(
            (sr_node, "CONTAINS", subm_node, props)
        )

        # get full author object, and save that with rel
        if self.author:
            props = {'created' : utc_now_timestamp() } #TODO
            author_node = self.author.save()
            self.gdb.get_or_create_relationships(
                (subm_node, "AUTHOR", author_node, props)
            )
    return subm_node

def _get_all_comments(self):

    try:
        return self.all_comments
    except AttributeError:
        self.replace_more_comments()
        self.all_comments = praw.helpers.flatten_tree(self.comments)
        return self.all_comments

Submission.data = _get_submission_data
Submission.save = _save_submission
Submission.all_flat_comments = _get_all_comments

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
    props['label'] = props['name']
    props['updated'] = utc_now_timestamp()
    props['type'] = 'user'

    log.info('Saving node for user %s' % props['label'])
    n = self.gdb.get_or_create_indexed_node('Users', 'id', props['id'], props)

    return n

Redditor.data = _get_user_data
Redditor.save = _save_user

# COMMENT #
# ======= #

def _get_comment_data(self):

    if not self._populated:
        self._populate(json_dict=None, fetch=True)
    props = ['body', 'body_html', 'created', 'created_utc', 'downs', 'edited', 'gilded','id',
            'link_id', 'name', 'parent_id', 'subreddit_id', 'ups']
    data = self.__dict__.copy()
    comment_data = {key : value for key, value in data.items() if key in props}

    #del data['reddit_session'], data['author'], data['_submission']
    #del data['_replies'], data['subreddit']

    # TODO suffiencient plain text info on submission?
    # TODO store nesting structure for comments?
    # TODO what with deleted comments?

    if self.author:
        comment_data['author_name'] = self.author.name

    return comment_data

def _save_comment(self, full=True, update=False):
    props = self.data()
    props['label'] = props['body'][0:15]
    props['updated'] = utc_now_timestamp()
    props['type'] = 'comment'
    log.info('Saving node for comment "%s..."' % props['label'])
    comment_node = self.gdb.get_or_create_indexed_node('Comments', 'id', props['id'], props)

    if full:
        # get full submission object and save that with rel
        props = {'created' : utc_now_timestamp() } #TODO
        subm_node = self.submission.save()
        self.gdb.get_or_create_relationships(
            (subm_node, "CONTAINS", comment_node, props)
        )

        # get full author object, and save that with rel
        if self.author:
            props = {'created' : utc_now_timestamp() } #TODO
            author_node = self.author.save()
            self.gdb.get_or_create_relationships(
                (comment_node, "AUTHOR", author_node, props)
            )
    return comment_node

Comment.data = _get_comment_data
Comment.save = _save_comment


if __name__ == '__main__':
    r = praw.Reddit('rest')
    #s = r.get_submission('http://www.reddit.com/r/programming/comments/17j839/curiosity_the_gnu_foundation_does_not_consider/')
    s = r.get_submission('http://www.reddit.com/r/belgium/comments/17y0gy/mobile_vikings_to_give_free_mobile_data/')
    u = s.author
    c = s.comments[0]
    sr = s.subreddit

    s2 = r.get_submission('http://www.reddit.com/r/politics/comments/178763/congressman_obama_is_upholding_a_soviet/')
    #print s.data()
    #s.save()
