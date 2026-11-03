import re
from flask import Flask, render_template, request
from search import Search

es = Search()
app = Flask(__name__)


@app.get('/')
def index():
    return render_template('index.html')


@app.post('/')
def handle_search():
    query = request.form.get('query', '')
    filters, parsed_query = extract_filters(query)
    from_ = request.form.get('from_', type=int, default=0)

    results = es.search(
        knn={
            'field': 'embedding',
            'query_vector': es.get_embedding(parsed_query),
            'num_candidates': 50,
            'k': 10,
        },
        size=5,
        from_=from_
    )
    return render_template('index.html', results=results['hits']['hits'],
                           query=query, from_=from_,
                           total=results['hits']['total']['value'])

@app.get('/document/<id>')
def get_document(id):
    document = es.retrieve_document(id)
    if document:
        title = document['_source'].get('name', 'Document')
        paragraphs = document['_source'].get('content', '').split('\n')
        return render_template('document.html', title=title,
                               paragraphs=paragraphs)
    else:
        return 'Document not found'

@app.cli.command()
def reindex():
    """Regenerate the Elasticsearch index."""
    response = es.reindex()
    print(f'Index with {len(response["items"])} documents created '
          f'in {response["took"]} milliseconds.')
    
def extract_filters(query):
    filters = []

    filter_regex = r'category:([^\s]+)\s*'
    m = re.search(filter_regex, query)
    if m:
        filters.append({
            'term': {
                'category.keyword': {
                    'value': m.group(1)
                }
            },
        })
        query = re.sub(filter_regex, '', query).strip()

    filter_regex = r'year:([^\s]+)\s*'
    m = re.search(filter_regex, query)
    if m:
        filters.append({
            'range': {
                'updated_at': {
                    'gte': f'{m.group(1)}||/y',
                    'lte': f'{m.group(1)}||/y',
                }
            },
        })
        query = re.sub(filter_regex, '', query).strip()

    return {'filter': filters}, query