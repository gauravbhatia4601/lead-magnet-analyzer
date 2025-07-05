from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="lead-magnet-analyzer",
    version="1.0.0",
    author="Lead Magnet Analyzer Team",
    author_email="support@example.com",
    description="A powerful web scraping and analysis tool that evaluates websites for lead magnet effectiveness",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/lead-magnet-analyzer",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Marketing",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Internet :: WWW/HTTP :: Browsers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: Markup :: HTML",
    ],
    python_requires=">=3.7",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "flake8>=3.8",
            "mypy>=0.800",
        ],
    },
    entry_points={
        "console_scripts": [
            "lead-magnet-analyzer=main:main",
        ],
    },
    keywords="web scraping, lead magnets, marketing, analysis, playwright, beautifulsoup",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/lead-magnet-analyzer/issues",
        "Source": "https://github.com/yourusername/lead-magnet-analyzer",
        "Documentation": "https://github.com/yourusername/lead-magnet-analyzer#readme",
    },
) 