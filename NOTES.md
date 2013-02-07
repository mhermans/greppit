start n=node:Submissions("id:*")
match n-[r?]->m
where r is null
return n

q = 'START n=node(*) MATCH n-[r?]-() where ID(n) <> 0 DELETE n, r;'
py2neo.cypher.execute(gdb, q)

users = g.get_index(neo4j.Node, 'Users')
users.query('id:*')

#median:

START n=node:Users("id:*") RETURN percentile_cont(n.link_karma, 0.5);

START reddit = node(0) MATCH reddit-[:CONTAINS]->subreddit RETURN subreddit.label;

START reddit = node(0) MATCH reddit-[:CONTAINS]->subreddit-[:CONTAINS]->subm-[:AUTHOR]->author RETURN subreddit.label, author.label, author.link_karma;

START comment=node:Comments("id:*") MATCH subreddit-[:CONTAINS]->submission-[:CONTAINS]->comment-[:AUTHOR]->author RETURN subreddit.label, percentile_cont(author.created_utc, 0.5);


START submission=node:Submissions("id:*") MATCH subreddit-[:CONTAINS]->submission RETURN subreddit.label, count(submission.id);

START comment=node:Comments("id:*") MATCH subreddit-[:CONTAINS]->submission-[:CONTAINS]->comment RETURN subreddit.label, count(comment.id);

START n=node(*) WHERE has(n.url), n.url = '/r/belgium' RETURN n;

gdb.clear() keeps the indexes, and "relationship types"
