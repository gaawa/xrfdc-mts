#   Copyright (c) 2019, Xilinx, Inc.
#   SPDX-License-Identifier: BSD-3-Clause


from setuptools import setup


with open("README.md", encoding='utf-8') as fh:
    readme_lines = fh.readlines()[:]
long_description = (''.join(readme_lines))


setup(
    name="xrfdc-mts",
    version='1.0',
    description="Driver for the RFSoC RF Data Converter IP extended with MTS functionality",
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='',
    license='BSD 3-Clause',
    author="Gaawa",
    author_email="",
    packages=['xrfdc-mts'],
    package_data={
        '': ['*.py', '*.c'],
    },
    install_requires=[]
)

