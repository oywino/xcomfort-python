import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="xcomfort",
    version="0.7.3",
    author="Jan Kristian Bjerke",
    author_email="jan.bjerke@gmail.com",
    maintainer="oyvind overby",
    maintainer_email="oyvind.overby@oywin.com",
    description="Integration with Eaton xComfort Bridge (forked from Jankrib's original library with minor updates)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/oywino/xcomfort-python",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 2 - Pre-Alpha",
    ],
    python_requires='>=3.7',
    install_requires=[
        "aiohttp",
        "rx",
        "pycryptodome"
    ],
)
