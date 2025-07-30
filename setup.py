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
        "pyyaml>=6.0",
        "tqdm>=4.64.0",
        "scikit-learn>=1.2.0", 
        "python-dotenv>=1.0.0",
        "requests>=2.28.0",
        "langchain-ollama>=0.3.0",
    ],
    extras_require={
        "openai": ["openai>=1.0.0"],
        "anthropic": ["anthropic>=0.8.1"],
        "all": ["openai>=1.0.0", "anthropic>=0.8.1"],
        "dev": ["pytest>=7.0.0", "pytest-cov>=4.0.0", "black>=23.0.0", "isort>=5.12.0", "flake8>=6.0.0"],
    },
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