import rdflib, datetime
from rdflib import URIRef, Literal, RDF, RDFS
from neo4reddit import RedditGraph, Submission, Comment

SIOC = rdflib.Namespace('http://rdfs.org/sioc/ns#')
SIOCT = rdflib.Namespace('http://rdfs.org/sioc/types#')
DCT = rdflib.Namespace('http://purl.org/dc/terms/')
DC = rdflib.Namespace('http://purl.org/dc/elements/1.1/')
DBP = rdflib.Namespace('http://dbpedia.org/resource/')
XTYPES = rdflib.Namespace('http://purl.org/xtypes/')
BIBO = rdflib.Namespace('http://purl.org/ontology/bibo/')

def _init_graph():
    # TODO available on Reddit objects?
    g = rdflib.Graph()
    g.namespace_manager.bind("sioc", SIOC)
    g.namespace_manager.bind("sioct", SIOCT)
    g.namespace_manager.bind('dcterms', DCT)
    g.namespace_manager.bind('dc', DC)
    g.namespace_manager.bind('dbp', DBP)
    g.namespace_manager.bind('xtypes', XTYPES)
    g.namespace_manager.bind('bibo', BIBO)

    return g

def _get_submission_graph(self):

    g = _init_graph()
    d = self.data()
    print d

    post_uri = URIRef(d['permalink'])
    g.add((post_uri, RDF.type, SIOC.Post))
    g.add((post_uri, SIOC.id, Literal(d.get('id'))))
    g.add((post_uri, SIOC.about, URIRef(d.get('url'))))
    g.add((post_uri, SIOC.num_replies, Literal(d.get('num_comments'))))
    g.add((post_uri, SIOC.name, Literal(d.get('title'))))
    g.add((post_uri, DC.title, Literal(d.get('title'))))
    g.add((post_uri, DCT.created,
        Literal(datetime.datetime.fromtimestamp(d.get('created_utc')))))

    # domain as Website?
    g.add((post_uri, DCT.isPartOf, URIRef(d.get('domain'))))
    g.add((URIRef(d.get('domain')), RDF.type, BIBO.Website))


    g.add((post_uri, SIOC.content, d.get('selftext')))

    # is_self?
    # id <-> name (includes type)

    # no accepted voting properties atm.
    # http://wiki.sioc-project.org/index.php/Ontology/RatingTermsSuggestion#sioc:num_positive_votes
    g.add((post_uri, SIOC.num_positive_votes, Literal(d.get('ups'))))
    g.add((post_uri, SIOC.num_negative_votes, Literal(d.get('downs'))))
    g.add((post_uri, SIOC.score, Literal(d.get('score'))))

    # if self-post:
    if d.get('selftext'):
        g.add((post_uri, SIOC.content, Literal(d.get('selftext'))))

    if d.get('author_name'):
        user_uri = URIRef('/'.join(['http://www.reddit.com/user', d['author_name']]))
        g.add((user_uri, RDF.type, SIOC.UserAccount))
        g.add((post_uri, SIOC.has_creator, user_uri))

    return g

Submission.graph = _get_submission_graph

def _get_comment_graph(self):
    d = self.data()
    g = _init_graph()
    print d
    comment_uri = URIRef(d['permalink'])

    g.add((comment_uri, RDF.type, SIOCT.Comment))
    g.add((comment_uri, SIOC.id, Literal(d.get('id'))))
    g.add((comment_uri, DCT.created,
        Literal(datetime.datetime.fromtimestamp(d.get('created_utc')))))

    # title/name/label for comment?
    #g.add((comment_uri, SIOC.name, Literal(d.get('title'))))

    # no accepted voting properties atm.
    # http://wiki.sioc-project.org/index.php/Ontology/RatingTermsSuggestion#sioc:num_positive_votes
    g.add((comment_uri, SIOC.num_positive_votes, Literal(d.get('ups'))))
    g.add((comment_uri, SIOC.num_negative_votes, Literal(d.get('downs'))))
    #g.add((comment_uri, SIOC.score, Literal(d.get('score')))) # no score for comments?

    # TODO number of child comments
    #g.add((comment_uri, SIOC.num_replies, Literal(d.get('num_comments'))))

    g.add((comment_uri, SIOC.content,
        Literal(d.get('body')))) # plain text version
    g.add((comment_uri, SIOC.content, # html type, add datatype
        Literal(d.get('body_html'), datatype=XTYPES.HTML)))

    if d.get('author_name'):
        user_uri = URIRef('/'.join(['http://www.reddit.com/user', d['author_name']]))
        g.add((user_uri, RDF.type, SIOC.UserAccount))
        g.add((comment_uri, SIOC.has_creator, user_uri))

    #for link in self.links():
    #    g.add((comment_uri, SIOC.links_to, URIRef(link)))

    return g

def _links(self):
    # return links in comment
    html = self.body_html
    # get hrefs
    # return hrefs

def _contains_rdf(self):
    # fast detection
    return ':::turtle' in self.body

def _parse_turtle_block(self):
    pass

Comment.graph = _get_comment_graph
Comment.contains_rdf = _contains_rdf
Comment.links = _links

#TODO generic walk function for comments

# SUBREDDIT
# ---------

def _get_subreddit_graph(self):
    g = _init_graph()
    sr_uri = URIRef(self.url)
    g.add((sr_uri, RDF.type, SIOC.Forum))
    g.add((sr_uri, SIOC.topic, DBP.Semantic_web))

r = RedditGraph('test')
#s = r.get_submission('http://www.reddit.com/r/dataisbeautiful/comments/18e617/the_word_tumultuous/')
s = r.get_submission('http://www.reddit.com/r/semanticweb/comments/197py9/w3c_turtle_now_a_candidate_recommendation/')
c = s.comments[0]
