import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

INSTALL_REQUIRES = [
    "urllib3",
    "Jinja2",
    "PyYAML",
    "pandas",
    "openpyxl",
    "acicobra",
    "acimodel"
]

setuptools.setup(
    name="devaci_module",
    version="1.0",
    author="Jorge Riveros",
    author_email="christian.riveros@outlook.com",
    license="MIT",
    description="A Python package to program the Cisco ACI through the APIC using the supported Cobra SDK",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/cocuni80/devaci_module",
    packages=setuptools.find_packages(),
    install_requires=INSTALL_REQUIRES,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9.2",
)
