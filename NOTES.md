start n=node:Submissions("id:*")
match n-[r?]->m
where r is null
return n
