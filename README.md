# Neo4j Drivers Migration Assistent

The migration assistent for Neo4j language libraries (drivers) scans your codebase and raises issues you should address before upgrading to a more recent version.
It doesn't automatically rewrite your code; it only points at where action is needed, providing in-context information on how each hit should be addressed.

Be aware that:
- The assistant can detect the largest majority of the changes you need to do in your code, but there is a small percentage of changelog entries that can't be surfaced in this form. For a thorough list of changes across versions, see https://neo4j.com/docs/{language-name}-manual/current/migration/ .
- Some of the hits may be false positives, so evaluate each hit.
- Implicit function calls and other hard to parse expressions will not be surfaced by the default parser. To broaden the search radius, use --rough-parsing. The coarser parser is likely to return more false positives, so the best course of action is to run the assistant with the default parser, fix all the surfaced hits, and then run it again with the rough parser.
- Your Cypher queries may also need changing, but this tool doesn't analyze them. See https://neo4j.com/docs/cypher-manual/current/deprecations-additions-removals-compatibility/ .

Example invocation

```bash
python main.py example-projects/python/movies.py -l python
```

Examples not raised by tree-sitter parser

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
    elif tyoe == 'write':
        return 'write_transanction'

getattr(session, tx_func())(callback, args)
```
