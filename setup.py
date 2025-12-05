"""Setup configuration for Finance Chatbot"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="finance-chatbot",
    version="1.0.0",
    author="Pradeep Kumar Tripathy",
    author_email="tripathy.pradeep@gmail.com",
    description="An intelligent document analysis and Q&A system for Santa Clara University Finance Department",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pradeept3/finance-chatbot",
    project_urls={
        "Bug Tracker": "https://github.com/pradeept3/finance-chatbot/issues",
        "Documentation": "https://github.com/pradeept3/finance-chatbot/blob/main/README.md",
        "Source Code": "https://github.com/pradeept3/finance-chatbot",
    },
    packages=find_packages(exclude=["tests", "*.tests", "*.tests.*", "tests.*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Web Environment",
        "Intended Audience :: Education",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Education",
        "Topic :: Office/Business",
    ],
    python_requires=">=3.8",
    install_requires=[
        "streamlit>=1.28.1",
        "streamlit-option-menu>=0.3.6",
        "Flask>=2.3.0",
        "Flask-CORS>=4.0.0",
        "python-dotenv>=1.0.0",
        "chromadb>=1.3.4",
        "sentence-transformers>=2.2.2",
        "unstructured[local-inference]>=0.18.20",
        "python-docx>=1.2.0",
        "pypdf>=6.3.0",
        "openpyxl>=3.1.5",
        "requests>=2.32.0",
        "beautifulsoup4>=4.13.5",
        "google-generativeai>=0.6.0",
        "numpy>=1.24.0",
        "pandas>=2.1.3",
        "scikit-learn>=1.3.2",
        "scipy>=1.11.4",
        "Pillow>=10.1.0",
        "lxml>=4.9.3",
        "Werkzeug>=2.3.7",
        "typing-extensions>=4.8.0",
        "pydantic>=2.5.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=4.0",
            "black>=23.0",
            "flake8>=6.0",
            "mypy>=1.0",
        ],
    },
    include_package_data=True,
    package_data={
        "finance_chatbot": ["static/*", "templates/*"],
    },
    entry_points={
        "console_scripts": [
            "finance-chatbot=finance_chatbot.cli:main",
        ],
    },
    keywords=[
        "chatbot",
        "finance",
        "document-analysis",
        "qa-system",
        "streamlit",
        "flask",
        "generative-ai",
    ],
    license="MIT",
    zip_safe=False,
)