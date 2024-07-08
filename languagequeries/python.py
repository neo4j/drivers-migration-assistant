import re

class PythonQueries:

    def function(self, name):
        return f"""
            (call
              function: (identifier) @function_name
              {self.match_var('function_name', name)}
            )
        """

    def method(self, name):
        return f"""
            (call
              function: (attribute
                attribute: (identifier) @method_name
                {self.match_var('method_name', name)}
              )
            )
        """

    def property(self, name):
        return f"""
            (attribute
              attribute: (identifier) @property_name
              {self.match_var('property_name', name)}
            )
        """

    def type(self, name):
        return f"""
            (
              (type) @type_name
              {self.match_var('type_name', name)}
            )
        """

    def import_from_statement__module_name(self, name):
        return f"""
            (import_from_statement
              module_name: (dotted_name) @module_name
              {self.match_var('module_name', name)}
            )
        """

    def import_from_statement__name(self, module_name, name):
        return f"""
            (import_from_statement
              module_name: (dotted_name) @module_name
              (#eq? @module_name "{module_name}")
              name: (dotted_name) @name
              {self.match_var('name', name)}
            )
        """

    def import_statement__name(self, name):
        return f"""
            (import_statement
              name: (dotted_name) @name
              {self.match_var('name', name)}
            )
        """

    def method__kwarg(self, method_name, kwarg_name):
        return f"""
            (call
              function: (attribute
                attribute: (identifier) @method_name
                {self.match_var('method_name', method_name)}
              )
              arguments: (argument_list
                (keyword_argument
                  name: (identifier) @kwarg_name
                  {self.match_var('kwarg_name', kwarg_name)}
                )
              )
            )
        """

    def function__kwarg(self, function_name, kwarg_name):
        return f"""
            (call
              function: (identifier) @function_name
              {self.match_var('function_name', function_name)}
              arguments: (argument_list
                (keyword_argument
                  name: (identifier) @kwarg_name
                  {self.match_var('kwarg_name', kwarg_name)}
                )
              )
            )
        """

    def function__kwarg__type(self, function_name, kwarg_name, type_name):
        return f"""
            (call
              function: (identifier) @function_name
              {self.match_var('function_name', function_name)}
              arguments: (argument_list
                (keyword_argument
                  name: (identifier) @kwarg_name
                  {self.match_var('kwarg_name', kwarg_name)}
                  value: (_) @type_name
                  {self.match_var('type_name', type_name)}
                )
              )
            )
        """

    def match_var(self, var_name, value):
        re.compile(value)
        return f'(#match? @{var_name} "{value}")'
