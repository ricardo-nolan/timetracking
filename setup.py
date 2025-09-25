#!/usr/bin/env python3
"""
Setup script for Time Tracker
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Read requirements
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="timetracking",
    version="1.0.6",
    author="Ricardo Nolan",
    author_email="ricardo@example.com",
    description="A Python time tracking application with GUI, PDF export, and email functionality",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/ricardo-nolan/timetracking",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Office/Business",
        "Topic :: Utilities",
    ],
    python_requires=">=3.7",
    install_requires=read_requirements(),
    entry_points={
        "console_scripts": [
            "timetracking=timetracking.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "timetracking": ["*.txt", "*.md"],
    },
    keywords="time tracking, productivity, gui, pdf, email, sqlite",
    project_urls={
        "Bug Reports": "https://github.com/ricardo-nolan/timetracking/issues",
        "Source": "https://github.com/ricardo-nolan/timetracking",
    },
)
