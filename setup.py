from setuptools import setup, find_packages

setup(
    name="batchmark",
    version="0.1.0",
    description="Benchmark shell commands across multiple input sizes and output structured reports.",
    author="batchmark contributors",
    python_requires=">=3.8",
    packages=find_packages(exclude=["tests*"]),
    entry_points={
        "console_scripts": [
            "batchmark=batchmark.cli:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Environment :: Console",
        "Topic :: Utilities",
    ],
)
