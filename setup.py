from setuptools import setup, find_packages

# Read the contents of your README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="qyro",
    version="2.0.0",
    author="Qyro Team",
    author_email="team@qyro.dev",
    description="The Universal Polyglot Runtime - Write Python, C, Rust, Java in one file with shared state",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/qyro-dev/qyro",
    project_urls={
        "Bug Reports": "https://github.com/qyro-dev/qyro/issues",
        "Source": "https://github.com/qyro-dev/qyro",
        "Documentation": "https://qyro.dev/docs",
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Compilers",
        "Topic :: Software Development :: Interpreters",
    ],
    packages=find_packages(include=['qyro*']),
    python_requires=">=3.8",
    install_requires=[
        "click>=8.0",
        "colorama>=0.4",
        "typing-extensions>=4.0",
        "redis>=5.0.0",
        "docker>=7.0",
        "psutil>=5.8.0",
        "confluent-kafka>=2.0.0",  # Added Kafka support
        "fastapi>=0.100",
        "uvicorn>=0.20",
        "websockets>=11.0",
        "pydantic>=2.0",
        "pydantic-settings>=2.0",
        "structlog>=23.0",
        "aiokafka>=0.10.0",  # Async Kafka client
        "PyYAML>=6.0",
        "rich>=13.0",
        "questionary>=2.0",
        "art>=6.0",
        "pyfiglet>=1.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=4.0",
            "black>=23.0",
            "mypy>=1.0",
            "ruff>=0.1",
        ],
        "full": [
            "qyro[redis,gateway,ui,docker]",
        ],
    },
    entry_points={
        "console_scripts": [
            "qyro=qyro.cli.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)