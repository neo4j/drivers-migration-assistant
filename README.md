# Neo4j Drivers Migration Assistent

The migration assistent for Neo4j language libraries (drivers) scans your codebase and raises issues you should address before upgrading to a more recent version.
It doesn't automatically rewrite your code; it only points at where action is needed, providing in-context information on how each hit should be addressed.

The assistent supports codebases in Python and Go. <br>
For further information see the upgrade guide for each language library: [Python](https://neo4j.com/docs/python-manual/5/upgrade/), [Go](https://neo4j.com/docs/go-manual/5/upgrade/), [JavaScript](https://neo4j.com/docs/javascript-manual/5/upgrade/), [Java](https://neo4j.com/docs/java-manual/5/upgrade/), [.NET](https://neo4j.com/docs/dotnet-manual/5/upgrade/).

Points of care:
- The assistent can detect most of the changes you need to do in your code, but a small percentage of changelog entries can't be surfaced in this form. For a thorough list of changes across versions, see each driver's migration page.
- Some of the hits may be false positives, so evaluate each of them.
- Implicit function calls and other hard to parse expressions will not be surfaced by the default parser. See [Accuracy](#accuracy).
- Your Cypher queries may also need changing, but this tool doesn't analyze them. See [Cypher -> Deprecations, additions, and compatibility](https://neo4j.com/docs/cypher-manual/current/deprecations-additions-removals-compatibility/).

Why doesn't it automatically rewrite code? The main reasons are two:

1. In many instances, breaking changes are not simple method renames or things that could easily be automatically rewritten. Sometimes the _behavior_ of a function changed, sometimes a method was deprecated without a 1:1 replacement, sometimes a property containing decimal seconds has been split into two properties containing seconds and microseconds separately. In many cases, you need to _evaluate_ how to address the change depending on what behavior your application expects.
2. We want users to have all the information they need to address changes, and to make it readily available. We also still want the users to be responsible and aware of the changes they make. Automatic rewriting promotes lack of understanding.


# Usage
To set up the environment, assuming `python3` and `pip3` are already installed,

```bash
python3 -m venv virtualenvs/neo-migration
source virtualenvs/neo-migration/bin/activate
pip3 install -r requirements.txt
```

The basic invocation looks like:

```bash
python3 main.py -l <codebase-language> <path-to-codebase>
```

For example, for a python application,

```bash
python3 main.py -l python example-projects/python/movies.py
```

Paths support [globbing](https://www.man7.org/linux/man-pages/man7/glob.7.html).
You can provide multiple paths as positional arguments.
For example (quotes for shell expansion),

```bash
python3 main.py -l python 'example-projects/python/*.py' 'example-projects/python/subdir/**/*.py' '/a/full/dir/'
```

By default the tool runs in interactive mode. To get all the output at once, use `--no-interactive`.
For a list of all options, see `-h`.


# Accuracy
## Tree-sitter parser
By default, the assistent works on an AST of your source, relying on [tree-sitter](https://tree-sitter.github.io/) to generate it.
This makes the deprecation/removal hits fairly accurate (although not perfect: there's no type checking in most cases).
However, invocations that materialize only at runtime can't be surfaced.

Here are a few examples containing deprecated usage that would **not** be raised by the tree-sitter parser:

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

## Regex parser
The regex parser works with regexes on the raw source code rather that on its AST.
To enable it, use `--regex-parser`.

The regex parser has less awareness of code structure and is thus likely to return **more false positives**, but is also capable of raising deprecated usage that only gets surfaced at runtime. 
The best course of action is to run the assistent with the default parser, fix all the surfaced hits, and then run it again with the regex parser.

Example of false positive from the regex parser:

```log
`Node.id` and `Relationship.id` were deprecated and have been superseded by `Node.element_id` and
`Relationship.element_id`. Old identifiers were integers, wereas new elementIds are strings.
This also affects Graph objects as indexing graph.nodes[...] and graph.relationships[...] with integers
has been deprecated in favor of indexing them with strings.

  102
  103 def serialize_movie(movie):
  104     return {
> 105         "id": movie["id"],
  106         "title": movie["title"],
  107         "summary": movie["summary"],
  108         "released": movie["released"],

  Deprecated in: 5.0
  Docs: https://neo4j.com/docs/cypher-manual/current/functions/scalar/#functions-elementid
```
