import rdflib, datetime
from rdflib import URIRef, Literal, RDF, RDFS
from greppit import RedditGraph, Submission, Comment
from lxml import html
import HTMLParser

SIOC = rdflib.Namespace('http://rdfs.org/sioc/ns#')
SIOCT = rdflib.Namespace('http://rdfs.org/sioc/types#')
DCT = rdflib.Namespace('http://purl.org/dc/terms/')
DC = rdflib.Namespace('http://purl.org/dc/elements/1.1/')
DBP = rdflib.Namespace('http://dbpedia.org/resource/')
XTYPES = rdflib.Namespace('http://purl.org/xtypes/')
BIBO = rdflib.Namespace('http://purl.org/ontology/bibo/')
RLDO = rdflib.Namespace('http://purl.org/net/rldo/')

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
    g.namespace_manager.bind('rldo', RLDO)

    return g

def _get_submission_graph(self):

    g = _init_graph()
    d = self.data()

    post_uri = URIRef(d['permalink'])

    # if self-post:
    if d.get('selftext'):
        g.add((post_uri, SIOC.content, Literal(d.get('selftext'))))
        g.add((post_uri, RDF.type, RLDO.SelfPost))

    else:
        g.add((post_uri, RDF.type, SIOC.Post))
        g.add((post_uri, DCT.isPartOf, URIRef(d.get('domain'))))
        g.add((URIRef(d.get('domain')), RDF.type, BIBO.Website))

    g.add((post_uri, SIOC.id, Literal(d.get('id'))))
    g.add((post_uri, SIOC.about, URIRef(d.get('url'))))
    g.add((post_uri, SIOC.num_replies, Literal(d.get('num_comments'))))
    g.add((post_uri, SIOC.name, Literal(d.get('title'))))
    g.add((post_uri, DC.title, Literal(d.get('title'))))
    g.add((post_uri, SIOC.num_replies, Literal(d.get('num_comments'))))
    g.add((post_uri, DCT.created,
        Literal(datetime.datetime.fromtimestamp(d.get('created_utc')))))



    # id <-> name (includes type)

    # TODO containing subreddit?

    # no accepted voting properties atm.
    # http://wiki.sioc-project.org/index.php/Ontology/RatingTermsSuggestion
    # -> use custom properties
    g.add((post_uri, RLDO.upvotes, Literal(d.get('ups'))))
    g.add((post_uri, RLDO.downvotes, Literal(d.get('downs'))))
    g.add((post_uri, RLDO.votes, Literal(d.get('score'))))


    if d.get('author_name'):
        user_uri = URIRef('/'.join(['http://www.reddit.com/user', d['author_name']]))
        g.add((user_uri, RDF.type, SIOC.UserAccount))
        g.add((post_uri, SIOC.has_creator, user_uri))

    return g

Submission.graph = _get_submission_graph

def _get_comment_graph(self):
    d = self.data()
    g = _init_graph()

    comment_uri = URIRef(d['permalink'])

    g.add((comment_uri, RDF.type, SIOCT.Comment))
    g.add((comment_uri, SIOC.id, Literal(d.get('id'))))
    g.add((comment_uri, DCT.created,
        Literal(datetime.datetime.fromtimestamp(d.get('created_utc')))))

    # title/name/label for comment?
    #g.add((comment_uri, SIOC.name, Literal(d.get('title'))))

    g.add((comment_uri, RLDO.upvotes, Literal(d.get('ups'))))
    g.add((comment_uri, RLDO.downvotes, Literal(d.get('downs'))))
    #g.add((comment_uri, SIOC.score, Literal(d.get('score')))) # no score for comments?

    # TODO number of child comments
    g.add((comment_uri, SIOC.num_replies, Literal(d.get('num_replies'))))

    g.add((comment_uri, SIOC.content,
        Literal(d.get('body')))) # plain text version
    g.add((comment_uri, SIOC.content, # html type, add datatype
        Literal(d.get('body_html'), datatype=XTYPES.HTML)))

    if d.get('author_name'):
        user_uri = URIRef('/'.join(['http://www.reddit.com/user', d['author_name']]))
        g.add((user_uri, RDF.type, SIOC.UserAccount))
        g.add((comment_uri, SIOC.has_creator, user_uri))

    for link in self._links():
        g.add((comment_uri, SIOC.links_to, URIRef(link)))


    if self._replies:
        for r in self._replies:
            g.add((comment_uri, SIOC.has_reply, URIRef(r.data().get('permalink'))))

    return g

def _links(self):
    # return links in comment
    parser = HTMLParser.HTMLParser()
    h = html.fromstring(parser.unescape(self.body_html))
    return h.xpath('//a/@href')

def _contains_rdf(self):
    # fast detection
    return ':::turtle' in self.body

# TODO: parse (cached) from http://www.reddit.com/r/semanticweb/wiki/meta/prefixes
PREFIXES = """
@prefix air: <http://www.daml.org/2001/10/html/airport-ont#> .
@prefix cert: <http://www.w3.org/ns/auth/cert#> .
@prefix contact: <http://www.w3.org/2000/10/swap/pim/contact#> .
@prefix dc: <http://purl.org/dc/elements/1.1/> .
@prefix dct: <http://purl.org/dc/terms/> .
@prefix doap: <http://usefulinc.com/ns/doap#> .
@prefix foaf: <http://xmlns.com/foaf/0.1/> .
@prefix geo: <http://www.w3.org/2003/01/geo/wgs84_pos#> .
@prefix mvcb: <http://webns.net/mvcb/> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix rel: <http://purl.org/vocab/relationship/> .
@prefix rss: <http://purl.org/rss/1.0/> .
@prefix session: <http://redfoot.net/2005/session#> .
@prefix sioc: <http://rdfs.org/sioc/ns#> .
@prefix sioct: <http://rdfs.org/sioc/types#> .
@prefix uranai: <http://kota.s12.xrea.com/vocab/uranai#> .
@prefix wn: <http://xmlns.com/wordnet/1.6/> .
"""

def _parse_turtle_block(self):
    if not self._contains_rdf():
        return None

    parser = HTMLParser.HTMLParser()
    h = html.fromstring(parser.unescape(self.body_html))
    turtle = h.xpath('//code')[0].text

    # _:post -> reddit post uri
    # _:article -> about link

    turtle = turtle.strip(':::turtle\n')
    turtle = turtle.replace('_:post', '<' + self.permalink  + '>')
    turtle = turtle.replace('_:article', '<' + self.submission.url + '>')

    # add prefixes from wiki
    turtle = '\n'.join([PREFIXES, turtle])

    g = _init_graph()
    g.parse(data=turtle, format='n3')

    return g

Comment.graph = _get_comment_graph
Comment._links = _links
Comment._contains_rdf = _contains_rdf
Comment._parse_turtle_block = _parse_turtle_block


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
