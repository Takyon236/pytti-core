from setuptools import setup, find_packages, find_namespace_packages
import logging

p0 = find_packages(where="src")
# p1 = find_namespace_packages(where='vendor.*')
p2 = find_namespace_packages(
    where="src",
    include=["hydra_plugins.*"],
)

setup(
    packages=p0 + p2,
    package_dir={
        "": "src",
    },
    install_requires=[],  # All dependencies in requirements.txt
    extras_require={
        # Optional features - install with: pip install pytti-core[optical-flow]
        "optical-flow": ["pyttitools-gma"],
        "depth": ["pyttitools-adabins"],
        "all": ["pyttitools-gma", "pyttitools-adabins"],
    },
    entry_points={
        "console_scripts": [
            "pytti-webui=pytti.webui.__main__:run_with_checks",
        ],
    },
    python_requires=">=3.10",  # Support Python 3.10, 3.11, 3.12+
)
