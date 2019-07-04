from setuptools import setup, find_packages

description = "Tooling for generation of API clients using openapi-generator"

def get_requirements(file):
    res = []
    with open(file) as f:
        for l in f.readlines():
            l = l.strip()
            if l and not l.startswith("#"):
                res.append(l)
    return res

install_requires = get_requirements("requirements.txt")
tests_require = get_requirements("requirements-tests.txt")


setup(
    name="apigentools",
    version="0.1.0.dev1",
    description=description,
    long_description=description,
    keywords="openapi,api,client,openapi-generator",
    author="Slavek Kabrda",
    author_email="slavek.kabrda@datadoghq.com",
    url="https://github.com/DataDog/apigentools",
    license="BSD 3-clause",
    packages=find_packages(exclude=["tests"]),
    include_package_data=True,
    test_suite="tests",
    entry_points={
        "console_scripts": ["apigentools=apigentools.cli:cli"]
    },
    scripts=["container-apigentools"],
    platforms="any",
    install_requires=install_requires,
    tests_require=tests_require,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
    ]
)
