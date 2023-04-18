from setuptools import setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="tiff-inspector",
    version="0.1.0",
    package_dir={"tiffinspector": "tiffinspector"},
    packages=['tiffinspector'],
    install_requires=[
        "importlib_metadata; python_version<'3.8'",
        "tifffile>=2021.1.1",
        "imagecodecs"
    ],
    package_data={
        "tiffinspector":["../schemas/*.json"]
    },
    author="Jason L Weirather",
    author_email="jason.weirather@gmail.com",
    description="A package for examining the structure and contents of the metadata contained within tiff files",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jason-weirather/tiff-inspector",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    python_requires=">=3.6",
)
