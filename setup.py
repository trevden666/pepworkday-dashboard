"""Setup configuration for PepWorkday Pipeline."""

from setuptools import setup, find_packages
import os

# Read the contents of README file
this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# Read requirements
with open('requirements.txt') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="pepworkday-pipeline",
    version="1.0.0",
    author="PEP Automation Team",
    author_email="automation@pep.com",
    description="Production-ready data pipeline for dispatch and Samsara report automation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/trevden666/pepworkday",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "pepworkday-pipeline=pepworkday_pipeline.pipeline:main",
        ],
    },
    include_package_data=True,
    package_data={
        "pepworkday_pipeline": ["config/*.yaml", "schemas/*.json"],
    },
)
