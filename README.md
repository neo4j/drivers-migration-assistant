# Neo4j Drivers Migration Assistent

The migration assistent for Neo4j language libraries (drivers) scans your codebase and raises issues you should address before upgrading to a more recent version.
It doesn't automatically rewrite your code; it only points at where action is needed, providing in-context information on how each hit should be addressed.

Be aware that:
- The assistant can detect the largest majority of the changes you need to do in your code, but there is a small percentage of changelog entries that can't be surfaced in this form. For a thorough list of changes across versions, see the migration page for [language libraries](https://neo4j.com/docs/create-applications/).
- Some of the hits may be false positives, so evaluate each hit.
- Implicit function calls and other hard to parse expressions will not be surfaced by the default parser. See [Accuracy](#accuracy).
- Your Cypher queries may also need changing, but this tool doesn't analyze them. See [Cypher -> Deprecations, additions, and compatibility](https://neo4j.com/docs/cypher-manual/current/deprecations-additions-removals-compatibility/).

# Usage

```bash
python -m venv virtualenvs/neomigration
source virtualenvs/migration/bin/activate
pip install -r requirements.txt
```

The basic invocation looks like:

```bash
python main.py <path-to-your-codebase> -l <codebase-language>
```

For example, for a python application,

```bash
python main.py example-projects/python/movies.py -l python
```

# Accuracy
## Tree-sitter parser
By default, the assistent works on an AST of your source, relying on [tree-sitter](https://tree-sitter.github.io/) to generate it. 
This makes the deprecation/removal hits fairly accurate (although not perfect: there's no type checking in most cases). 
However, invocations that materialize in their entirety only at runtime can't be surfaced. 

Here are a few examples containing deprecated usage that would not be raised by the tree-sitter parser:

```python
method_name = 'read_transaction'
locals()['method_name']()
```

```python
config = {
    'session_connection_timeout': 10,
    'update_routing_table_timeout': 4
}
driver = GraphDatabase.driver(url, auth=auth, **config)
```

```python
def tx_func(type):
    if type == 'read':
        return 'read_transanction'
    elif type == 'write':
        return 'write_transanction'

getattr(session, tx_func())(callback, args)
```

## Rough parser
There is another parser, which works with regexes on the raw source code rather that on its AST. To enable the rough parser, use `--rough-parsing`.

This parser is coarser and thus likely to return more false positives, so the best course of action is to run the assistant with the default parser, fix all the surfaced hits, and then run it again with the rough parser.

Example of false positive from the rough parser:

```log
>> `Node.id` and `Relationship.id` were deprecated and have been superseded by `Node.element_id` and
`Relationship.element_id`. Old identifiers were integers, wereas new elementIds are strings.
This also affects Graph objects as indexing graph.nodes[...] and graph.relationships[...] with integers
has been deprecated in favor of indexing them with strings.

  102 
  103 def serialize_movie(movie):
  104     return {
  105         "id": movie["id"],
  106         "title": movie["title"],
  107         "summary": movie["summary"],
  108         "released": movie["released"],

  Deprecated in: 5.0
  Docs: https://neo4j.com/docs/cypher-manual/current/functions/scalar/#functions-elementid
```
