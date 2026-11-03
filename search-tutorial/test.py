import json
from search import Search
es = Search()
with open('data.json', 'rt') as f:
    documents = json.loads(f.read())
for document in documents:
    es.insert_document(document)