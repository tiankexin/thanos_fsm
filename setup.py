# -*- coding:utf-8 -*-

from setuptools import setup, find_packages

__VERSION__ = "0.0.1"

setup(
    name='thanos_fsm',
    version=__VERSION__,
    packages=find_packages(),
    package_dir={'thanos_fsm': 'thanos_fsm'},
    description='most pythonic Finite State Machine',
    long_description="This is a pythonic style tool for FSM. Welcome to use it, and star on my Github. Thank you!",
    license="BSD 2-Clause License",
    url="https://github.com/tiankexin/thanos_fsm",
    author="tiankexin",
    author_email="tiankexin123@gmail.com",
    install_requires=[],
    include_package_data=True,
    platforms="any"
)
