from ._common import match_var


class PythonQueries:

    def function(self, name):
        return f"""
            (call
              function: (identifier) @function_name
              {match_var('function_name', name)}
            )
        """

    def method(self, name):
        return f"""
            (call
              function: (attribute
                attribute: (identifier) @method_name
                {match_var('method_name', name)}
              )
            )
        """

    def property(self, name):
        return f"""
            (attribute
              attribute: (identifier) @property_name
              {match_var('property_name', name)}
            )
        """

    def type(self, name):
        return f"""
            (
              (type) @type_name
              {match_var('type_name', name)}
            )
        """

    def import_from_statement__module_name(self, name):
        return f"""
            (import_from_statement
              module_name: (dotted_name) @module_name
              {match_var('module_name', name)}
            )
        """

    def import_from_statement__name(self, module_name, name):
        return f"""
            (import_from_statement
              module_name: (dotted_name) @module_name
              (#eq? @module_name "{module_name}")
              name: (dotted_name) @name
              {match_var('name', name)}
            )
        """

    def import_statement__name(self, name):
        return f"""
            (import_statement
              name: (dotted_name) @name
              {match_var('name', name)}
            )
        """

    def method__kwarg(self, method_name, kwarg_name):
        return f"""
            (call
              function: (attribute
                attribute: (identifier) @method_name
                {match_var('method_name', method_name)}
              )
              arguments: (argument_list
                (keyword_argument
                  name: (identifier) @kwarg_name
                  {match_var('kwarg_name', kwarg_name)}
                )
              )
            )
        """

    def method__kwarg__type(self, method_name, kwarg_name, type_name):
        return f"""
            (call
              function: (attribute
                attribute: (identifier) @method_name
                {match_var('method_name', method_name)}
              )
              arguments: (argument_list
                (keyword_argument
                  name: (identifier) @kwarg_name
                  {match_var('kwarg_name', kwarg_name)}
                  value: (_) @type_name
                  {match_var('type_name', type_name)}
                )
              )
            )
        """

    def function__kwarg(self, function_name, kwarg_name):
        return f"""
            (call
              function: (identifier) @function_name
              {match_var('function_name', function_name)}
              arguments: (argument_list
                (keyword_argument
                  name: (identifier) @kwarg_name
                  {match_var('kwarg_name', kwarg_name)}
                )
              )
            )
        """

    def function__kwarg__type(self, function_name, kwarg_name, type_name):
        return f"""
            (call
              function: (identifier) @function_name
              {match_var('function_name', function_name)}
              arguments: (argument_list
                (keyword_argument
                  name: (identifier) @kwarg_name
                  {match_var('kwarg_name', kwarg_name)}
                  value: (_) @type_name
                  {match_var('type_name', type_name)}
                )
              )
            )
        """

    def _import_for_namespace(self):
        regex = '\\\\bneo4j\\\\b'
        return f"""
            (import_statement
              name: (aliased_import
                name: (dotted_name) @default_namespace
                {match_var('default_namespace', regex)}
                alias: (identifier) @alias
              )
            ) @root
        """

    def _parse_import_alias(self, match, source_lines):
        line = source_lines[match[1]['root'].range.start_point[0]]
        splitted = line.strip().split(' ')
        pkg_name = splitted[1]
        imported_as = splitted[-1]
        return pkg_name, imported_as
