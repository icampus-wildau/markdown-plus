#!/usr/bin/env python
import setuptools
from distutils.util import convert_path

PACK_NAME = "mdplus"

main_ns = {}
ver_path = convert_path(f'{PACK_NAME}/_version.py')
with open(ver_path) as ver_file:
    exec(ver_file.read(), main_ns)


with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name=PACK_NAME,
    version=main_ns['__version__'],
    author="Valentin Schröter",
    author_email="vasc9380@th-wildau.com",
    description="Markdown Plus generator",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://icampusnet.th-wildau.de/ros-e/software/infrastructure/markdown-plus",
    project_urls={
        "Bug Tracker": "https://icampusnet.th-wildau.de/ros-e/software/infrastructure/markdown-plus/-/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    # package_dir={"flint": "flint"},
    # packages=setuptools.find_packages(where="flint"),
    packages=setuptools.find_packages(),
    include_package_data=True,
    python_requires=">=3.6",
    install_requires=[
        "click",
        "click-aliases",
        "GitPython",
        "mistletoe",
        "pandas",
        "py-markdown-table",
        "rich"
    ],
    entry_points={
        "console_scripts": [
            "mdplus = mdplus.cli:execute",
        ]
    }
)