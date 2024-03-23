#!/bin/python3

import os
from os import listdir
from os.path import isfile, join, isdir
import sys
import threading
import time
import random
import string

from typing import List, Set, Dict, Tuple, Optional
from enum import Enum


def getAllFiles(path, filterSuffixes: List[str] = None):
    files = [f for f in listdir(path) if isfile(join(path, f))]
    if filterSuffixes is not None:
        for s in filterSuffixes:
            files = [f for f in files if f.endswith(s)]

    return files


def getAllDirs(path, ignore_hidden=True):
    dirs = [f for f in listdir(path) if isdir(join(path, f))]
    if ignore_hidden:
        dirs = [d for d in dirs if not d.startswith(".")]
    return dirs


def hasFiles(dirPath, files: List[str]):

    existingCount = 0
    allFiles = getAllFiles(dirPath)

    for f in allFiles:
        if f in files:
            existingCount += 1

    return existingCount == len(files)


def get_relative_path(path, root):
    return "." + path[len(root) :]
    # return os.path.join("./", path[len(root):])


def join_relative_path(root, path):
    if path.startswith("./"):
        path = path[2:]
    return os.path.join(root, path)
