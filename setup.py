from setuptools import setup, find_packages

setup(
    name="shitcoin",
    version="4.2.0",
    author="Bartolomeə",
    author_email="barton@bmorphism.xyz",
    description="Changing the world, one DAO at a time.",
    url="https://github.com/bmorphism/shitcoin",
    project_urls={
        "Bug Tracker": "https://github.com/bmorphism/shitcoin/issues",
    },
    license="The Unlicense",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: The Unlicense (Unlicense)",
        "Intended Audience :: Developers",
        "Intended Audience :: Financial and Insurance Industry",
        "Intended Audience :: Legal Industry",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Religion",
        "Intended Audience :: Other Audience",
        "Topic :: Internet",
        "Topic :: Games/Entertainment :: Simulation",
        "Development Status :: 3 - Alpha",
    ],
    keywords="shitcoin, degen, blockchain, dao, cw20, ibc, defi, denom, permissionless, token, anarchy",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.6",
)
