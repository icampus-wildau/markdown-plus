#!/bin/python3

import enum
import os
from os import listdir
from os.path import isfile, join, isdir
import sys
import threading
import time
import random
import string
import re
import json
import ast

import logging

from typing import List, Set, Dict, Tuple, Optional
from enum import Enum

# from markdowngenerator import markdowngenerator


import mdplus.util.file_utils as file_utils
from mdplus.generators.flags import Flags
from mdplus.util.parser.py_parser import PyParserInplace, get_doc_string_content, PyParser

logger = logging.getLogger(__name__)


class MessageType:
    def __init__(self, package: "Package", msg_file_path: str):

        self.package = package
        self.msg_file_path = msg_file_path
        self.name = os.path.basename(self.msg_file_path).replace(".msg", "")

        with open(self.msg_file_path) as file:
            lines = file.readlines()
            self.content_original = "\n".join(lines)
            lines = [line.strip() for line in lines]

            splittedLines = []

            # Skip Copyright / Licence block
            init_comment_lines = []
            for l in lines:
                if l.startswith("#"):
                    init_comment_lines.append(l)
                else:
                    break

            if len(init_comment_lines) > 0:
                s = "\n".join(init_comment_lines).lower()
                if "license" in s or "copyright" in s:
                    lines = lines[len(init_comment_lines) :]

            # Skip the first lines if they are empty
            while len(lines) > 0 and lines[0] == "":
                lines.pop(0)

            for l in lines:
                if l.startswith("#"):
                    splittedLines.append(l)
                else:
                    splits = [a.strip() for a in l.split("#", 1)]
                    if len(splits) == 1:
                        splittedLines.append(l)
                    else:
                        splittedLines.append("# " + splits[1])
                        splittedLines.append(splits[0])

            self.content = "\n".join(splittedLines)

    def get_wiki_entry(self, header_level: int, replace_root: str = "", as_code_block=True):
        self.wikiEntry = ""
        self.wikiEntry += header_level * "#"

        relative_path = self.msg_file_path
        if replace_root != "":
            relative_path = file_utils.get_relative_path(relative_path, replace_root)

        # self.wikiEntry += f" [`{self.name}`]({relative_path})\n"
        self.wikiEntry += f" `{self.name}`\n"
        self.wikiEntry += "\n"
        if as_code_block: 
            self.wikiEntry += "```python\n"
        self.wikiEntry += self.content
        self.wikiEntry += "\n"
        if as_code_block: 
            self.wikiEntry += "```\n"
            self.wikiEntry += "\n"
        self.wikiEntry += f"Source: [{relative_path.lstrip('./')}]({relative_path})"

        return self.wikiEntry

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return self.wikiEntry if self.wikiEntry is not None and len(self.wikiEntry) > 0 else self.get_wiki_entry()


class ServiceType:
    def __init__(self, package: "Package", srv_file_path: str):

        self.package = package
        self.srv_file_path = srv_file_path
        self.name = os.path.basename(self.srv_file_path).replace(".srv", "")

        with open(self.srv_file_path) as file:
            lines = file.readlines()
            self.content_original = "\n".join(lines)
            lines = [line.strip() for line in lines]

            splittedLines = []

            # Skip Copyright / Licence block
            init_comment_lines = []
            for l in lines:
                if l.startswith("#"):
                    init_comment_lines.append(l)
                else:
                    break

            if len(init_comment_lines) > 0:
                s = "\n".join(init_comment_lines).lower()
                if "license" in s or "copyright" in s:
                    lines = lines[len(init_comment_lines) :]

            # Skip the first lines if they are empty
            while len(lines) > 0 and lines[0] == "":
                lines.pop(0)

            for l in lines:
                if l.startswith("#"):
                    splittedLines.append(l)
                else:
                    splits = [a.strip() for a in l.split("#", 1)]
                    if len(splits) == 1:
                        splittedLines.append(l)
                    else:
                        splittedLines.append("# " + splits[1])
                        splittedLines.append(splits[0])

            self.content = "\n".join(splittedLines)

    def get_wiki_entry(self, header_level: int, replace_root: str = "", as_code_block=True):
        self.wikiEntry = ""
        self.wikiEntry += header_level * "#"

        relative_path = self.srv_file_path
        if replace_root != "":
            relative_path = file_utils.get_relative_path(relative_path, replace_root)

        # self.wikiEntry += f" [`{self.name}`]({relative_path})\n"
        self.wikiEntry += f" `{self.name}`\n"
        self.wikiEntry += "\n"
        if as_code_block: 
            self.wikiEntry += "```python\n"
        self.wikiEntry += self.content
        self.wikiEntry += "\n"
        if as_code_block: 
            self.wikiEntry += "```\n"
            self.wikiEntry += "\n"
        self.wikiEntry += f"Source: [{relative_path.lstrip('./')}]({relative_path})"

        return self.wikiEntry

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return self.wikiEntry if self.wikiEntry is not None and len(self.wikiEntry) > 0 else self.get_wiki_entry()


class LaunchScript:
    def __init__(self, package: "Package", launch_file_path: str):
        self.package = package
        self.launch_file_path = launch_file_path
        self.name = os.path.basename(self.launch_file_path).replace(".launch.py", "")

        self.info = "..."

        with open(self.launch_file_path) as file:
            content = file.read()
            # self.info = get_doc_string_content(content, r"def generate_launch_description\(.*?\):",
            #                                    only_first_line=False)

            parser = PyParserInplace(content)
            m = parser.go_method("generate_launch_description").current_item
            self.info = PyParser.get_doc_string(m)


class Topic:
    def __init__(self, topic_name):
        self.topic_name = topic_name


class Publisher(Topic):
    def __init__(self, msg_type: str, topic: str, comment: str = ""):
        super().__init__(topic)
        self.msg_type = msg_type
        self.comment = comment


class Subscription(Topic):
    def __init__(self, msg_type: str, topic: str, comment: str = ""):
        super().__init__(topic)
        self.msg_type = msg_type
        self.comment = comment


class Service(Topic):
    def __init__(self, service_type: str, topic: str, comment: str = ""):
        super().__init__(topic)
        self.service_type = service_type
        self.comment = comment


class Parameter:
    def __init__(self, name: str, value: str, comment: str = ""):
        self.name = name
        self.value = value
        self.comment = comment


class Node:
    def __init__(self, package: "Package", name: str, script: str, entry_point: str):
        self.package = package
        self.name = name
        self.script = script
        self.script_path = os.path.join(self.package.path, *self.script.split(".")) + ".py"
        self.entry_point = entry_point
        self.info = "..."

        self.file_content = None
        if os.path.isfile(self.script_path):
            with open(self.script_path, "r") as f:
                self.file_content = f.read()
        else:
            logger.error(f"Node script not found: {self.script_path}")

        self.doc_string = self._parse_doc_string()
        self.doc_string_without_header = self._get_doc_string_without_header(self.doc_string)
        self.info = self._get_info_from_doc_string(self.doc_string)

        self.services = self._parse_services()
        self.publisher = self._parse_publisher()
        self.subscriptions = self._parse_subscriptions()

        self.parameters = self._parse_parameters()

    def _parse_doc_string(self):
        doc = Flags.NOT_FOUND

        if self.file_content is None:
            return doc

        parser = PyParserInplace(self.file_content)
        c = parser.go_class(bases=["Node"]).current_item
        constants = PyParser.get_elements_where_value_is_of_type(c, ast.Constant, return_value=True)
        constants = {c.lineno: c for c in constants}

        if not hasattr(c, "lineno"):
            return doc

        if c.lineno + 1 in constants:
            doc = PyParser.get_doc_string(constants[c.lineno + 1], only_first_line=False, remove_indentation=True)
        else:
            t = parser.tree
            constants = PyParser.get_elements_where_value_is_of_type(t, ast.Constant, return_value=False)
            if len(t.body) > 0 and len(constants) > 0 and t.body[0] == constants[0]:
                doc = PyParser.get_doc_string(constants[0], only_first_line=False, remove_indentation=True)

        return doc

    @staticmethod
    def _get_doc_string_without_header(doc_string: str):
        parts = doc_string.split("\n\n")
        while len(parts) > 0 and parts[0].startswith("# "):
            parts.pop(0)

        return "\n\n".join(parts)

    @staticmethod
    def _get_info_from_doc_string(doc_string: str):
        parts = Node._get_doc_string_without_header(doc_string).split("\n\n")
        if len(parts) > 0:
            info = parts.pop(0)
            info = info.replace("\n", " ")
            return info
        return Flags.NOT_FOUND

    def _parse_publisher(self) -> list[Publisher]:
        publisher: list[Publisher] = []

        if self.file_content is None:
            return publisher

        parser = PyParserInplace(self.file_content)
        m = parser.go_class(bases=["Node"]).go_method("__init__").current_item
        if m is None:
            return publisher

        calls = PyParser.get_elements_where_value_is_of_type(m, ast.Call, return_value=True)
        constants = PyParser.get_elements_where_value_is_of_type(m, ast.Constant, return_value=True)
        constants = {e.lineno: e for e in constants}
        filtered = PyParser.filter_calls(calls, "create_publisher")

        for call in filtered:
            args = PyParser.get_args(call, ["msg_type", "topic", "qos_profile"])
            msg_type, topic, qos_profile = args
            s_msg_type = PyParser.get_name_or_value(msg_type)
            s_topic = PyParser.get_name_or_value(topic)
            # s_qos_profile = PyParser.get_name_or_value(qos_profile, include_origin_for_attributes=False)
            doc = Flags.NOT_FOUND
            if call.end_lineno + 1 in constants:
                e = constants[call.end_lineno + 1]
                doc = PyParser.get_doc_string(e)

            publisher.append(Publisher(s_msg_type, s_topic, doc))

        return publisher

    def _parse_subscriptions(self) -> list[Subscription]:
        subscriptions: list[Subscription] = []

        if self.file_content is None:
            return subscriptions

        parser = PyParserInplace(self.file_content)

        c = parser.go_class(bases=["Node"]).current_item
        m = parser.go_method("__init__").current_item
        if m is None:
            return subscriptions

        calls = PyParser.get_elements_where_value_is_of_type(m, ast.Call, return_value=True)
        constants = PyParser.get_elements_where_value_is_of_type(m, ast.Constant, return_value=True)
        constants = {e.lineno: e for e in constants}
        filtered = PyParser.filter_calls(calls, "create_subscription")

        for call in filtered:
            args = PyParser.get_args(call, ["msg_type", "topic", "callback"])
            msg_type, topic, callback = args
            s_msg_type = PyParser.get_name_or_value(msg_type)
            s_topic = PyParser.get_name_or_value(topic)
            s_callback = PyParser.get_name_or_value(callback, include_origin_for_attributes=False)

            if (call.end_lineno + 1) in constants:
                e = constants[call.end_lineno + 1]
                doc = PyParser.get_doc_string(e)
            else:
                parser.reset()
                m = parser.go_method(s_callback, recursive=True).current_item
                doc = PyParser.get_doc_string(m, only_first_line=False, remove_indentation=True)

            subscriptions.append(Subscription(s_msg_type, s_topic, doc))

        return subscriptions

    def _parse_services(self) -> list[Service]:
        services: list[Service] = []

        if self.file_content is None:
            return services

        parser = PyParserInplace(self.file_content)

        c = parser.go_class(bases=["Node"]).current_item
        m = parser.go_method("__init__").current_item
        if m is None:
            return services

        calls = PyParser.get_elements_where_value_is_of_type(m, ast.Call, return_value=True)
        constants = PyParser.get_elements_where_value_is_of_type(m, ast.Constant, return_value=True)
        constants = {e.lineno: e for e in constants}
        filtered = PyParser.filter_calls(calls, "create_service")
        for call in filtered:
            args = PyParser.get_args(call, ["srv_type", "srv_name", "callback"])
            srv_type, srv_name, callback = args
            s_srv_type = PyParser.get_name_or_value(srv_type)
            s_srv_name = PyParser.get_name_or_value(srv_name)
            s_callback = PyParser.get_name_or_value(callback, include_origin_for_attributes=False)

            doc = ""
            if (call.end_lineno + 1) in constants:
                e = constants[call.end_lineno + 1]
                doc = PyParser.get_doc_string(e)
            else:
                parser.reset()
                m = parser.go_method(s_callback, recursive=True).current_item
                doc = PyParser.get_doc_string(m, only_first_line=False, remove_indentation=True)

            services.append(Service(s_srv_type, s_srv_name, doc))

        return services

    def _parse_parameters(self) -> list[Parameter]:
        parameters: list[Parameter] = []

        if self.file_content is None:
            return parameters

        parser = PyParserInplace(self.file_content)

        c = parser.go_class(bases=["Node"]).current_item
        m = parser.go_method("__init__").current_item
        if m is None:
            return parameters

        all_calls = PyParser.get_all_elements_of_type(m, ast.Call)
        filtered = PyParser.filter_calls(all_calls, "declare_parameter")

        for call in filtered:
            args = PyParser.get_args(call, ["name", "value", "descriptor"])
            name, value, descriptor = args
            s_name = PyParser.get_name_or_value(name)
            s_value = PyParser.get_name_or_value(value)
            s_description = Flags.NOT_FOUND
            if descriptor is not None:
                if isinstance(descriptor, ast.Call):
                    description = PyParser.get_args(descriptor, ["description"])[0]
                    s_description = PyParser.get_name_or_value(description)

            parameter = Parameter(s_name, s_value, s_description)
            parameters.append(parameter)

        return parameters

    def __str__(self) -> str:
        return f"[NODE] {self.name} ({self.script}:{self.entry_point})"  # @ {self.script_path}

    def __repr__(self) -> str:
        return self.__str__()

    @staticmethod
    def from_console_scripts(parent_package: "Package", console_script_entry: str):
        m = re.match("(.*?) = (.*?):(.*)", console_script_entry)
        name = m.group(1)
        script = m.group(2)
        main_method = m.group(3)

        return Node(parent_package, name, script, main_method)


class PackageType(enum.Enum):
    NONE = "NONE"
    PYTHON = "python"
    CMAKE = "cmake"


class Package:
    def __init__(self, package_path):
        self.path = package_path
        self.name = os.path.basename(os.path.normpath(self.path))

        logger.debug(f"Parsing PACKAGE at {self.path}")

        self.nodes: List[Node] = []
        self.launch_scripts: List[LaunchScript] = []
        self.messages: List[MessageType] = []
        self.services: List[ServiceType] = []

        self.package_type = PackageType.NONE

        if Package.isPythonPackage(self.path):
            self.package_type = PackageType.PYTHON

            setupPath = os.path.join(self.path, "setup.py")
            launchPath = os.path.join(self.path, "launch")

            parser = PyParserInplace(setupPath)
            if parser.exists():
                # Parse the defined ros nodes from the setup.py
                entry_points = parser.go_method("setup").go_keyword("entry_points").go_value().eval()
                console_scripts = entry_points["console_scripts"]

                for script in console_scripts:
                    self.nodes.append(Node.from_console_scripts(self, script))

                # Parse the defined launch scripts
                if os.path.isdir(launchPath):
                    for launchFile in os.listdir(launchPath):
                        if launchFile.endswith(".launch.py"):
                            self.launch_scripts.append(LaunchScript(self, os.path.join(launchPath, launchFile)))

            else:
                logger.warning(f"SETUP PY DOES NOT EXIST FOR {self.path}")

        elif Package.isCMakePackage(self.path):
            self.package_type = PackageType.CMAKE

            # TODO: Parse CMakeList to get the actually generated Messages
            message_path = os.path.join(self.path, "msg")
            service_path = os.path.join(self.path, "srv")
            message_files = (
                [f for f in listdir(message_path) if isfile(join(message_path, f))]
                if os.path.exists(message_path)
                else []
            )
            message_files = [f for f in message_files if f.endswith(".msg")]

            service_files = (
                [f for f in listdir(service_path) if isfile(join(service_path, f))]
                if os.path.exists(service_path)
                else []
            )
            service_files = [f for f in service_files if f.endswith(".srv")]

            message_files.sort()
            service_files.sort()

            if len(message_files) > 0:
                logger.debug(f"Extracting message types from: {message_path}")
                for f in message_files:
                    self.messages.append(MessageType(self, os.path.join(self.path, "msg", f)))

            if len(service_files) > 0:
                logger.debug(f"Extracting service types from: {service_files}")
                for f in service_files:
                    self.services.append(ServiceType(self, os.path.join(self.path, "srv", f)))

            messages = []

    def __str__(self) -> str:
        s = f"[PACKAGE] {self.name}\t ({self.path})"
        if len(self.nodes) > 0:
            s += "\n\t<<NODES>>"
            for n in self.nodes:
                s += f"\n\t\t {n}"

        if len(self.messages) > 0:
            s += "\n\t<<MESSAGES>>"
            for msg in self.messages:
                s += f"\n\t\t [MSG] {msg.name}"

        if len(self.services) > 0:
            s += "\n\t<<SERVICES>>"
            for srv in self.services:
                s += f"\n\t\t [SRV] {srv.name}"

        return s

    def __repr__(self) -> str:
        return self.__str__()

    @staticmethod
    def isCMakePackage(path) -> bool:
        return file_utils.hasFiles(path, ["CMakeLists.txt", "package.xml"])

    @staticmethod
    def isPythonPackage(path) -> bool:
        return file_utils.hasFiles(path, ["setup.cfg", "setup.py", "package.xml"])

    @staticmethod
    def isPackage(path):
        return Package.isCMakePackage(path) or Package.isPythonPackage(path)

    @staticmethod
    def isIgnored(path):
        if str(os.path.basename(path)).startswith("."):
            return True
        return file_utils.hasFiles(path, ["COLCON_IGNORE"])

    @staticmethod
    def getPackages(directory_path) -> List["Package"]:
        path = directory_path

        logger.debug(f"Get PACKAGES from {path}")

        packages = []
        if Package.isPackage(path):
            packages.append(Package(path))
        else:
            dirs = file_utils.getAllDirs(path)

            while len(dirs) > 0:
                d = dirs[0]
                dirPath = join(path, d)
                if not Package.isIgnored(dirPath):
                    if Package.isPackage(dirPath):
                        packages.append(Package(dirPath))
                    else:
                        newDirs = [join(d, f) for f in file_utils.getAllDirs(dirPath)]
                        # print("### Added", newDirs, f" @ {path}")
                        dirs.extend(newDirs)

                dirs.pop(0)

        return packages


class Workspace:
    def __init__(self, workspacePath):
        self.path = workspacePath

        logger.info(f"Parsing WORKSPACE at {self.path}")

        directories = [f for f in listdir(self.path) if isdir(join(self.path, f))]

        logger.info(f"Got dirs {directories}")

        self.packages: List[Package] = []

        for d in directories:
            newPackages = Package.getPackages(os.path.join(self.path, d))
            self.packages.extend(newPackages)

        self.packages.sort(key=lambda x: x.name)

    def __str__(self) -> str:
        s = f"[WORKSPACE] @ {self.path}"
        for p in self.packages:
            s += f"\n{p}"

        return s

    def __repr__(self) -> str:
        return self.__str__()
