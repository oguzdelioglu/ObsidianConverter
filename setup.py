"""
Setup script for ObsidianConverter
"""
from setuptools import setup, find_packages
from obsidian_converter import __version__

setup(
    name="obsidian-converter",
    version=__version__,
    description="Convert plain text files to Obsidian notes",
    author="ObsidianConverter Team",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "langchain",
        "langchain-community",
        "langchain-ollama",
        "scikit-learn",
        "tqdm",
        "python-dotenv"
    ],
    scripts=["bin/obsidian-converter"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Text Processing :: Markup",
        "Topic :: Utilities"
    ],
    python_requires=">=3.8",
)