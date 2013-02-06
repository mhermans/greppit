start n=node:Submissions("id:*")
match n-[r?]->m
where r is null
return n

q = 'START n=node(*) MATCH n-[r?]-() where ID(n) <> 0 DELETE n, r;'
py2neo.cypher.execute(gdb, q)
