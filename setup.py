"""Set up LG Horizon."""

import setuptools
import os
import re
import sys

with open("README.md", "r") as fh:
    long_description = fh.read()


def read(*parts):
    """Read file."""
    filename = os.path.join(os.path.abspath(os.path.dirname(__file__)), *parts)
    sys.stdout.write(filename)
    with open(filename, encoding="utf-8", mode="rt") as fp:
        return fp.read()


setuptools.setup(
    name="lghorizon",
    author="Rudolf Offereins",
    author_email="r.offereins@gmail.com",
    description="Python client for Liberty Global Horizon settop boxes",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/sholofly/LGHorizon-python",
    packages=setuptools.find_packages(include=["lghorizon"]),
    license="MIT license",
    install_requires=["paho-mqtt<2.0.0", "requests>=2.22.0", "backoff>=1.9.0"],
    keywords=["LG", "Horizon", "API", "Settop box"],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Natural Language :: English",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.9",
    zip_safe=False,
    use_scm_version=True,
    setup_requires=["setuptools_scm"],
)
