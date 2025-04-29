import setuptools

setuptools.setup(
    name="API_Viewer",
    version="0.1.0",
    author="Björn",
    author_email="bjorn@schrammel.dev",
    description="A Python package for API Viewer.",
    long_description_content_type="text/markdown",
    url="",
    packages=setuptools.find_packages(),
    install_requires=[
        "PyQt6~=6.8.1"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7"
)