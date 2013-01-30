import datetime
from py2neo import neo4j

# Monkeypatching praw objects

# subclass Reddit object to take graph uri on init?
#from praw import Reddit
#class NeoReddit(Reddit):
#    def __init__(self, neo4j_uri):
#        super(Reddit, self).__init__

# alternative atm:
RedditContentObject.gdb = neo4j.GraphDatabaseService("http://localhost:7474/db/data/")


from praw.objects import Comment, Submission, Redditor, RedditContentObject

def _get_submission_data(self, full=False):
    props = ['created', 'created_utc', 'id', 'domain',
        'downs', 'is_self', 'name', 'num_comments', 'permalink',
        'score', 'selftext', 'subreddit_id', 'ups', 'url']
    data = self.__dict__
    submission_data = {key : value for key, value in data.items() if key in props }
    if self.author:
        submission_data['author_name'] = self.author.name

    if full:
        pass

        # get full subreddit object and save that with rel

        # get full author object, and save that with rel


    return submission_data

def _save_submission(self, update=False):
    props = self.data()
    #props['updated'] = datetime.datetime.now()
    n = self.gdb.get_or_create_indexed_node('Submissions', 'id', props['id'], props)

Submission.data = _get_submission_data
Submission.save = _save_submission

r = Reddit('rest')
s = r.get_submission('http://www.reddit.com/r/programming/comments/17j839/curiosity_the_gnu_foundation_does_not_consider/')

print s.data()
s.save()
