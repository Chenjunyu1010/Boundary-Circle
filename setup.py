from setuptools import setup, find_packages

setup(
    name="boundary-circle",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.104.0",
        "uvicorn>=0.24.0",
        "sqlmodel>=0.0.22",
        "python-multipart>=0.0.6",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "httpx>=0.24.0",
        ],
        "frontend": [
            "streamlit>=1.28.0",
            "requests>=2.31.0",
        ],
    },
    python_requires=">=3.9",
)
