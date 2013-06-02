import datetime, logging
from py2neo import neo4j, rest

from praw.objects import Subreddit, Comment, Submission, Redditor, RedditContentObject
import praw

log = logging.getLogger('reddit crawler')
log.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
log.addHandler(ch)

def utc_now_timestamp():
    return (datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds()

# [X] make sure indexes are existing get_or_create_index()
# [X] store updated timestamp utc->timestamp code
# [X] accessable initialiser for gdb uri
# [X] store labels for every object
# [X] initialize reddit root node
# [ ] consistent solution for gdb & index access.
# [ ] store type/fullname (fullname() is a praw object function)
# [ ] solution for restoring praw objects based on stored data?


# Monkeypatching praw objects

# subclass Reddit object to take graph uri on init
class RedditGraph(praw.Reddit):
    def __init__(self, user_agent, backend=None,
            site_name=None, disable_update_check=False):

        super(praw.Reddit, self).__init__(user_agent,
                site_name=None, disable_update_check=False)

        # link to Neo4j REST API
        if type(backend) == neo4j.GraphDatabaseService:
            #self.gdb = neo4j.GraphDatabaseService("http://localhost:7474/db/data/")
            self.gdb = backend

            # get or initialize indexes
            self.subreddits = self.gdb.get_or_create_index(neo4j.Node, 'Subreddits')
            self.submissions = self.gdb.get_or_create_index(neo4j.Node, 'Submissions')
            self.comments = self.gdb.get_or_create_index(neo4j.Node, 'Comments')
            self.users = self.gdb.get_or_create_index(neo4j.Node, 'Users')
            self.structure = self.gdb.get_or_create_index(neo4j.Node, 'Structure')

            self.has_subreddit = self.gdb.get_or_create_index(neo4j.Relationship, 'HasSubreddit')

        # link to RDF store
        # TODO

# SUBREDDIT #
# ========= #

def _get_subreddit_data(self):

    # if data is not already fetched, do so
    if not self._populated:
        # TODO this is always fetched?
        log.info('Not populated, insert JSON for subreddit')
        self._populate(json_dict=None, fetch=True)

    # filter properties
    sr_props = ['accounts_active', 'created', 'created_utc', 'description',
            'display_name', 'id', 'name', 'over18', 'subscribers',
            'title', 'url']

    data = self.__dict__
    subreddit_data = {key : value for key, value in data.items() if key in sr_props }

    return subreddit_data

def _save_subreddit(self):

    # get/create reddit root node
    reddit_props = {'label':'Reddit', 'type':'rootnode', 'id':'reddit'}
    reddit_node = self.reddit_session.structure.get_or_create('root', 'reddit', reddit_props)

    # set subreddit node properties
    sr_props = self.data() # overwritten function!
    sr_props.update({'updated' : utc_now_timestamp(),
            'label' : sr_props['url'], 'type' : 'subreddit'})

    # create subreddit node if it does not exist
    log.info('Get or create node for subreddit %s' % sr_props['label'])
    sr_node = self.reddit_session.subreddits.get_or_create(
            'name', sr_props['display_name'], sr_props) # index on display_name

    # add relationship if it does not exist
    self.reddit_session.has_subreddit.create_if_none(
            'id', '-'.join([reddit_node['id'], sr_node['id']]),
                (reddit_node, 'has_subreddit', sr_node,
                {'updated' : utc_now_timestamp()}))

    return sr_node

Subreddit.data = _get_subreddit_data
Subreddit.save = _save_subreddit

# SUBMISSION #
# ========== #

def _get_submission_data(self):

    # TODO always populated?

    # filter properties
    sm_props = ['created', 'created_utc', 'id', 'domain',
        'downs', 'is_self', 'name', 'num_comments', 'permalink',
        'score', 'selftext', 'subreddit_id', 'ups', 'url', 'permalink', 'title']
    data = self.__dict__
    submission_data = {key : value for key, value in data.items() if key in sm_props }

    if self.author: submission_data['author_name'] = self.author.name

    return submission_data

def _get_all_comments(self):

    try: # check if comments have been parsed already
        return self.all_comments
    except AttributeError:
        self.replace_more_comments()
        self.all_comments = praw.helpers.flatten_tree(self.comments)
        return self.all_comments

def _save_submission(self, full=True, comments=False, update=False):

    # TODO always populated?

    sm_props = self.data()
    lbl = '[S] ' + ''.join(sm_props['title'][0:15].split())
    sm_props.update({'updated' : utc_now_timestamp(),
        'label' : lbl, 'type' : 'submission'})

    log.info('Saving node for submission "%s..."' % sm_props['label'])
    subm_node = self.reddit_session.gdb.get_or_create_indexed_node(
            'Submissions', 'id', sm_props['id'], sm_props)

    if full:
        # fetch sr name from dict to not trigger (remote) fetch
        sr_name = self.subreddit.__dict__.get('display_name')

        # retrieve or create subreddit node object
        sr_node = self.reddit_session.gdb.get_indexed_node(
                'Subreddits', 'name', sr_name)
        if not sr_node: sr_node = self.subreddit.save()

        self.reddit_session.gdb.get_or_create_relationships(
            (sr_node, "has_submission", subm_node, {'updated' : utc_now_timestamp() })
        )

        # get full author object, and save that with rel
        if self.author:
            author_node = self.reddit_session.gdb.get_indexed_node(
                    'Users', 'name', self.author.name)
            if not author_node: author_node = self.author.save()

            self.reddit_session.gdb.get_or_create_relationships(
                (subm_node, "has_author", author_node, {'updated' : utc_now_timestamp() })
            )

    if comments:
        [c.save() for c in self.all_flat_comments()]

    return subm_node


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
    u_props = self.data()
    u_props.update({'label' : '/u/' + u_props['name'],
        'updated' : utc_now_timestamp(), 'type' : 'user'})

    # Users are indexed on name (should be unique), not id
    # as unpopulated user objects do not have an id
    log.info('Get/create node for user %s' % u_props['label'])
    n = self.reddit_session.gdb.get_or_create_indexed_node(
            'Users', 'name', u_props['name'], u_props)

    return n

Redditor.data = _get_user_data
Redditor.save = _save_user

# COMMENT #
# ======= #

def _get_comment_data(self):

    if not self._populated:
        self._populate(json_dict=None, fetch=True)

    c_props = ['body', 'body_html', 'created', 'created_utc', 'downs', 'edited', 'gilded','id',
            'link_id', 'name', 'parent_id', 'subreddit_id', 'ups']

    data = self.__dict__.copy()
    comment_data = {key : value for key, value in data.items() if key in c_props}

    comment_data['permalink'] = self.permalink
    if self.__dict__.get('_replies'):
        comment_data['num_replies'] = len(self.__dict__.get('_replies'))

    #del data['reddit_session'], data['author'], data['_submission']
    #del data['_replies'], data['subreddit']

    # TODO suffiencient plain text info on submission?
    # TODO store nesting structure for comments?
    # TODO what with deleted comments?

    if self.author:
        comment_data['author_name'] = self.author.name

    return comment_data

def _save_comment(self, full=True, update=False):

    c_props = self.data()
    lbl = '[C] ' + ''.join(c_props['body'][0:15].split())
    c_props.update({'label' : lbl, 'updated' : utc_now_timestamp(), 'type': 'comment'})

    log.info('Get/create node for comment "%s..."' % c_props['label'])
    comment_node = self.reddit_session.gdb.get_or_create_indexed_node(
            'Comments', 'id', c_props['id'], c_props)

    if full:
        subm_node = self.reddit_session.gdb.get_indexed_node(
                'Submissions', 'id', self.submission.id)
        if not subm_node: subm_node = self.submission.save()

        self.reddit_session.gdb.get_or_create_relationships(
            (subm_node, "has_comment", comment_node, {'updated' : utc_now_timestamp() })
        )

        # get full author object, and save that with rel
        if self.author:
            author_node = self.reddit_session.gdb.get_indexed_node(
                    'Users', 'name', self.author.name)
            if not author_node: author_node = self.author.save()

            self.reddit_session.gdb.get_or_create_relationships(
                (comment_node, "has_author", author_node, {'updated' : utc_now_timestamp()})
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
