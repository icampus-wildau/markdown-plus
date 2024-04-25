from __future__ import annotations
import logging
import os
import re
import ast

from mdplus.core.documents.definitions import CommentDefinition

logger = logging.getLogger(__name__)


class MdpBlock:
    def __init__(self, match: re.Match):
        self.match = match
        self.command: str = match.group(2)
        self.arguments_str: str = match.group(3)

    @property
    def arguments(self) -> dict[str, str]:
        return self.parse_arguments(self.arguments_str)

    @staticmethod
    def get_pattern(comment_definition: CommentDefinition):
        # print(comment_definition.multi_line_start)
        # print('|'.join(comment_definition.multi_line_start))
        start = f"({'|'.join(re.escape(s) for s in comment_definition.multi_line_start)})"
        end = f"({'|'.join(re.escape(s) for s in comment_definition.multi_line_end)})"
        whitespace = r"[\s\n]*?"

        pattern_str = start + whitespace + r"MD\+:([^\s\n-]*)(.*?)(" + end + r")"
        # print(pattern_str)

        # Group 1: Multi line comment start
        # Group 2: Command
        # Group 3: Arguments

        return re.compile(pattern_str, re.MULTILINE | re.DOTALL)

    @staticmethod
    def get_fin_pattern(command: str, comment_definition: CommentDefinition):

        start = f"({'|'.join(re.escape(s) for s in comment_definition.multi_line_start)})"
        end = f"({'|'.join(re.escape(s) for s in comment_definition.multi_line_end)})"
        whitespace = r"[\s\n]*?"
        pattern_str = start + whitespace + r"MD\+FIN:" + command + whitespace + r"(" + end + r")"
        return re.compile(pattern_str, re.MULTILINE | re.DOTALL)

    @staticmethod
    def parse_arguments(arguments: str) -> dict[str, str]:
        """Parse the arguments of the generator from the string representation.

        Parameters
        ----------
        arguments : str
            The string representation of the arguments in the markdown text.

        Returns
        -------
        dict[str, str]
            Dictionary containing the arguments.
        """

        if arguments.strip() == "":
            return {}

        # Remove leading and trailing whitespaces from lines based on intend on the first line
        lines = arguments.split("\n")
        first_none_empty_line = next((i for i, line in enumerate(lines) if line.strip() != ""), None)
        first_none_empty_line = lines[first_none_empty_line] if first_none_empty_line is not None else None
        if first_none_empty_line is not None:
            intend = len(first_none_empty_line) - len(first_none_empty_line.lstrip())
            lines = [line[intend:] for line in lines]
            arguments = "\n".join(lines)
        # print(arguments)

        parsed_dict = {}
        parsed_ast = ast.parse(arguments)

        global_vars = {}

        for node in parsed_ast.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        var_name = target.id
                        var_value = node.value

                        # Evaluate the expression if it's not a simple value assignment
                        if isinstance(var_value, ast.Expr):
                            var_value = ast.literal_eval(var_value.value)
                        else:
                            try:
                                var_value = eval(
                                    compile(ast.Expression(var_value), "", "eval"), global_vars, parsed_dict
                                )
                            except Exception as _:
                                string_of_expression = ast.get_source_segment(arguments, node.value)
                                logger.error("Error evaluating expression '%s'", string_of_expression)
                                var_value = None
                        parsed_dict[var_name] = var_value
                    else:
                        logger.warning("Unsupported target type %s", target)
            else:
                logger.warning("Unsupported node type %s", node)
        return parsed_dict
