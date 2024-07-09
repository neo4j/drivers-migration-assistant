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
