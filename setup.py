# Unless explicitly stated otherwise all files in this repository are licensed
# under the 3-clause BSD style license (see LICENSE).
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2019 Datadog, Inc.
from setuptools import setup, find_packages

description = "Tooling for generation of API clients using openapi-generator"

def get_requirements(file):
    res = []
    with open(file) as f:
        for l in f.readlines():
            l = l.strip()
            if l:
                if l.startswith("-r"):
                    res.extend(get_requirements(l[2:].strip()))
                elif not l.startswith("#"):
                    res.append(l)
    return res

install_requires = get_requirements("requirements.txt")

setup(
    name="apigentools",
    version="0.1.0",
    description=description,
    long_description=description,
    keywords="openapi,api,client,openapi-generator",
    author="Slavek Kabrda",
    author_email="slavek.kabrda@datadoghq.com",
    url="https://github.com/DataDog/apigentools",
    license="BSD 3-clause",
    packages=find_packages(exclude=["tests"]),
    include_package_data=True,
    entry_points={
        "console_scripts": ["apigentools=apigentools.cli:cli"]
    },
    scripts=["container-apigentools"],
    platforms="any",
    install_requires=install_requires,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.7",
    ]
)
