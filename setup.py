from setuptools import setup, find_packages

setup(
    name="grooming-prep",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    package_data={
        "grooming_prep": ["templates/*.html"],
    },
    install_requires=[
        "click>=8.1.0",
        "groq>=0.9.0",
        "requests>=2.31.0",
        "jinja2>=3.1.0",
        "python-dotenv>=1.0.0",
        "httpx>=0.27.0",
    ],
    entry_points={
        "console_scripts": [
            "grooming-prep=grooming_prep.main:cli",
        ],
    },
    python_requires=">=3.11",
)
