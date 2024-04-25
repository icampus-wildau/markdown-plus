import ast
from ast import NodeVisitor
import _ast
from pprint import pprint

import re

import os
from typing import Any, Dict, List, Tuple, TypeVar, Type

from mistletoe import Document

from mdplus.generators.flags import Flags

T = TypeVar("T")


def get_doc_string_content(text: str, search_after_pattern: str = None, only_first_line=True) -> str:
    start_pos = 0
    if search_after_pattern is not None:
        match = re.search(search_after_pattern, text)
        if match is None:
            return ""
        start_pos = match.span()[1]

    pattern = re.compile(r'\s*"""(.*)"""\s*', re.MULTILINE)
    match = pattern.search(text, start_pos)
    if match is not None:
        doc_string = match.group(1)

        splits = doc_string.split("\n")
        splits = [s.strip() for s in splits]
        if only_first_line:
            index = splits.index("") if "" in splits else -1
            if index > 0:
                splits = splits[0:index]

        splits = ["\n" if s == "" else s.replace("\n", "") for s in splits]

        return " ".join(splits)
    else:
        return ""


def get_value(ast_val: ast.Constant):
    """Get the value of a constant node.

    Args:
        ast_val (ast.Constant): AST Constant node

    Raises:
        ValueError: If not known to the function.

    Returns:
        _type_: A number, a string, a bool or None
    """
    if isinstance(ast_val, ast.Num):
        return float(ast_val.n)
    elif isinstance(ast_val, ast.Str):
        return ast_val.s
    elif isinstance(ast_val, ast.NameConstant):
        return ast_val.value

    else:
        raise ValueError(f"Unknown type {type(ast_val)}")


def get_args(function_call: str) -> Tuple[List[Any], Dict[str, Any]]:
    """Get the arguments of a function call.


    Args:
        function_call (str): something like 'foo("bla", 2, test=True)'

    Returns:
        Tuple[List[Any], Dict[str, Any]]: args=["bla", 2], kwargs={'test': True}
    """
    ast_module: ast.Module = ast.parse(function_call)
    ast_call: ast.Call = ast_module.body[0].value
    ast_args: List[ast.Constant] = ast_call.args
    ast_kwargs: List[ast.keyword] = ast_call.keywords

    args = list()
    kwargs = dict()

    for a in ast_args:
        args.append(get_value(a))

    for kw in ast_kwargs:
        kwargs[kw.arg] = get_value(kw.value)

    return args, kwargs


class PyParserInplace:
    """Class to parse a python file and return the class names, methods, etc."""

    def __init__(self, file_path: str) -> None:
        self.file_path = file_path
        self.tree = None

        # Check if file exists and open it
        if self.exists():
            with open(file_path, "r") as f:
                self.tree = ast.parse(f.read())
        else:
            if isinstance(file_path, str):
                self.tree = ast.parse(file_path)
            else:
                raise ValueError(f"{type(file_path)} is no valid file path")

        self.current_item = self.tree
        # print(self.current_item)

    def reset(self):
        self.current_item = self.tree

    def exists(self):
        return self.file_path is not None and os.path.exists(self.file_path) and os.path.isfile(self.file_path)

    def go_class(self, name: str = None, bases: List[str] = None):
        # TODO: was bei mehreren passenden Klassen?
        if self.current_item is not None:
            try:
                for item in self.current_item.body:
                    if isinstance(item, _ast.ClassDef):
                        try:
                            fitting = True
                            if name is not None and item.name != name:
                                fitting = False
                            if bases is not None:
                                item_base_names = [b.id for b in item.bases]
                                for b in bases:
                                    if b not in item_base_names:
                                        fitting = False

                            if fitting:
                                self.current_item = item
                                return self
                        except AttributeError:
                            pass

                return self
            except AttributeError:
                self.current_item = None

        self.current_item = None

        return self

    def go_method(self, name: str, recursive: bool = False):
        if self.current_item is not None:
            try:
                for item in self.current_item.body:
                    if isinstance(item, _ast.Expr):
                        try:
                            if item.value.func.id == name:
                                self.current_item = item.value
                                return self
                        except AttributeError:
                            pass
                    elif isinstance(item, _ast.FunctionDef):
                        if item.name == name:
                            self.current_item = item
                            return self
                    elif isinstance(item, _ast.ClassDef):
                        if recursive:
                            self.current_item = item
                            self.go_method(name, recursive)
                            if self.current_item is not None:
                                return self
            except AttributeError:
                self.current_item = None

        self.current_item = None

        return self

    def go_keyword(self, name: str):
        if self.current_item is not None:
            try:
                for kw in self.current_item.keywords:
                    # if isinstance(item, _ast.keyword):
                    if kw.arg == name:
                        self.current_item = kw
                        return self
            except AttributeError:
                self.current_item = None
        self.current_item = None
        return self

    def go_value(self):
        if self.current_item is not None:
            try:
                self.current_item = self.current_item.value
                return self
            except AttributeError:
                self.current_item = None

        self.current_item = None
        return self

    def eval(self):
        # print(self.current_item)
        e = ast.Expression(self.current_item)
        return eval(compile(e, "<ast expression>", "eval"))


class PyParser:

    @staticmethod
    def get_content_string_from_script(script_content: str, ast_item):

        # Or just use:
        # return ast.unparse(ast_item)

        line = ast_item.lineno
        end_line = ast_item.end_lineno
        col = ast_item.col_offset
        end_col = ast_item.end_col_offset
        lines = script_content.splitlines()
        if line == end_line:
            return lines[line - 1][col:end_col]
        else:
            start = lines[line - 1][col:]
            end = lines[end_line - 1][:end_col]
            middle = lines[line : end_line - 1]
            return "\n".join([start] + middle + [end])

    @staticmethod
    def get_elements_of_type(item: ast.ClassDef | ast.FunctionDef, t: Type[T]) -> list[T]:
        """Get all elements of a certain type from the body of a class or function definition"""
        res = []
        for i in item.body:
            if isinstance(i, t):
                res.append(i)

        return res

    @staticmethod
    def get_all_elements_of_type(item, t: Type[T]) -> list[T]:
        """Get all elements of a certain type in all expressions below the given item
        TODO: Might work for a lot of stuff, but not for all. Needs testing.
        """
        res = []

        if isinstance(item, t):
            res.append(item)

        if isinstance(item, ast.ClassDef) or isinstance(item, ast.FunctionDef):
            for i in item.body:
                res.extend(PyParser.get_all_elements_of_type(i, t))
        elif isinstance(item, ast.Expr):
            res.extend(PyParser.get_all_elements_of_type(item.value, t))
        elif isinstance(item, ast.Call):
            res.extend(PyParser.get_all_elements_of_type(item.func, t))
            for a in item.args:
                res.extend(PyParser.get_all_elements_of_type(a, t))
            for k in item.keywords:
                res.extend(PyParser.get_all_elements_of_type(k, t))
        elif isinstance(item, ast.Assign):
            for tar in item.targets:
                res.extend(PyParser.get_all_elements_of_type(tar, t))
            res.extend(PyParser.get_all_elements_of_type(item.value, t))
        elif isinstance(item, ast.AnnAssign):
            res.extend(PyParser.get_all_elements_of_type(item.target, t))
            res.extend(PyParser.get_all_elements_of_type(item.value, t))
        elif isinstance(item, ast.Attribute):
            res.extend(PyParser.get_all_elements_of_type(item.value, t))

        return res

    @staticmethod
    def get_elements_where_value_is_of_type(
        item: ast.ClassDef | ast.FunctionDef, t: Type[T], return_value=False
    ) -> list[T]:
        res = []
        for i in item.body:
            if hasattr(i, "value"):
                if isinstance(i.value, t):
                    res.append(i.value if return_value else i)

        return res

    @staticmethod
    def filter_calls(calls: List[ast.Call], name: str) -> List[ast.Call]:
        filtered = []

        for c in calls:
            f = c.func
            if isinstance(f, ast.Name):
                if f.id == name:
                    filtered.append(c)
            elif isinstance(f, ast.Attribute):
                if f.attr == name:
                    filtered.append(c)

        return filtered

    @staticmethod
    def get_args(call: ast.Call, arg_names: List[str], include_args=True) -> List[Any]:
        args = []

        i = 0
        if include_args:
            for a in call.args:
                args.append(a)
                i += 1

                if i >= len(arg_names):
                    break

        for j in range(i, len(arg_names)):
            name = arg_names[j]
            for kw in call.keywords:
                if kw.arg == name:
                    args.append(kw.value)
                    break
            else:
                args.append(None)

        return args

    @staticmethod
    def get_name_or_value(item: ast.Constant | ast.Name | ast.Attribute, include_origin_for_attributes=False) -> str:
        if item is None:
            return "None"

        if isinstance(item, ast.Constant):
            return item.value
        elif isinstance(item, ast.Name):
            return item.id
        elif isinstance(item, ast.Attribute):
            if include_origin_for_attributes:
                return f"{item.value.id}.{item.attr}"
            else:
                return item.attr
        elif isinstance(item, ast.Call):
            return ast.unparse(item)
        else:
            # compiled = compile(item, "<ast>", "eval")
            unparsed = ast.unparse(item)
            return unparsed
            # raise ValueError(f"Unknown type {type(item)}")

    @staticmethod
    def get_doc_string(
        item: ast.ClassDef | ast.FunctionDef | ast.Expr | ast.Constant, only_first_line=False, remove_indentation=True
    ) -> str:
        """Gets a doc string from a class or function or a docstring expression"""

        doc: str = None
        elem = item

        if isinstance(item, ast.ClassDef) or isinstance(item, ast.FunctionDef):
            if item.body and len(item.body) > 0:
                elem = item.body[0]
                if isinstance(elem, ast.Expr):
                    if isinstance(elem.value, ast.Constant):
                        doc = elem.value.value
        elif isinstance(item, ast.Expr):
            if isinstance(elem.value, ast.Constant):
                doc = elem.value.value
        elif isinstance(item, ast.Constant):
            doc = item.value

        if doc is not None:
            if only_first_line:
                doc = doc.split("\n\n")[0]

            if remove_indentation:
                ind = elem.col_offset
                parts = doc.split("\n\n")
                new_parts = []
                for part in parts:
                    splits = part.split("\n")
                    splits = [s for s in splits]
                    splits = [(s[ind:] if len(s) >= ind and s[:ind].strip() == "" else s) for s in splits]
                    res = "\n".join(splits)
                    new_parts.append(res)

                doc = "\n\n".join(new_parts)

            if only_first_line:
                doc = " ".join(doc.split("\n"))

            while doc.startswith("\n"):
                doc = doc[1:]
            while doc.endswith("\n"):
                doc = doc[:-1]

            return doc

        return Flags.NOT_FOUND


if __name__ == "__main__":
    import mistletoe
    from mistletoe.ast_renderer import ASTRenderer, get_ast

    file_path = "C:/Users/schoc/Documents/Studium/Git/ROS-E/software/ros2-packages/displays/docs/HOOKS.md"
    with open(file_path, "r") as fin:
        # ast = mistletoe.ast_renderer.get_ast(fin.read())
        d = Document(fin)
        sss = str(d)
        a = get_ast(d)
        rendered = mistletoe.markdown(fin, renderer=ASTRenderer)

        # markdown.Markdown().

    parser = PyParserInplace(file_path)

    c = parser.go_class(bases=["Node"]).current_item
    m = parser.go_method("__init__").current_item

    calls = PyParser.get_elements_where_value_is_of_type(m, ast.Call)
    all_calls = PyParser.get_all_elements_of_type(m, ast.Call)
    expressions = PyParser.get_elements_of_type(m, ast.Expr)
    expressions = {e.lineno: e for e in expressions}
    filtered = PyParser.filter_calls(all_calls, "declare_parameter")

    for call in filtered:
        args = PyParser.get_args(call, ["name", "value", "descriptor"])
        name, value, descriptor = args
        s_name = PyParser.get_name_or_value(name)
        s_value = PyParser.get_name_or_value(value)
        if descriptor is not None:
            if isinstance(descriptor, ast.Call):
                description = PyParser.get_args(descriptor, ["description"])[0]
                s_description = PyParser.get_name_or_value(description)
        # s_qos_profile = PyParser.get_name_or_value(qos_profile, include_origin_for_attributes=False)
        # if call.end_lineno + 1 in expressions:
        #     e = expressions[call.end_lineno + 1]
        #     doc = PyParser.get_doc_string(e)

    # c = parser.go_class(bases=["Node"]).current_item
    # m = parser.go_method("__init__").current_item
    #
    # calls = PyParser.get_elements_where_value_is_of_type(m, ast.Call)
    # filtered = PyParser.filter_calls(calls, "create_service")
    #
    # for call in filtered:
    #     args = PyParser.get_args(call, ["srv_type", "srv_name", "callback"])
    #     srv_type, srv_name, callback = args
    #     s_srv_type = PyParser.get_string_value(srv_type)
    #     s_srv_name = PyParser.get_string_value(srv_name)
    #     s_callback = PyParser.get_string_value(callback, include_origin_for_attributes=False)
    #
    #     parser.reset()
    #     m = parser.go_method(s_callback, recursive=True).current_item
    #     doc = PyParser.get_doc_string(m, only_first_line=False, remove_indentation=True)
    #
    #     x = 5

    x = 5
