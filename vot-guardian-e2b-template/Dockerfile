# Use Python 3.10.11 exactly (user requirement) on a Debian-based slim image.
# This is suitable for local CPU builds; E2B template builds live under `vot-guardian-cpu/`.
FROM python:3.10.11-slim-bullseye

# Ensure UTF-8 and unbuffered output for clearer logs
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1

# Install system dependencies needed by librosa and scientific stack
# - libsndfile1 and ffmpeg are key for audio I/O
# - build tools to compile optional wheels if needed
USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    libsndfile1 \
    ffmpeg \
    build-essential \
    gcc \
    g++ \
    git \
    curl \
    libffi-dev \
    python3-dev \
    pkg-config \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Python 3.10.11 is provided by the base image.

# Create a working dir for app deps
WORKDIR /opt/vot-guardian

# Copy your app requirements (we'll install the heavy ones first to maximize layer caching)
# Provide two files:
#  - sandbox-core-requirements.txt: torch CPU, librosa, mindsdb client(s), and any critical libs
#  - requirements.txt: your project’s requirements from the repo
COPY sandbox-core-requirements.txt /opt/vot-guardian/sandbox-core-requirements.txt
COPY requirements.txt /opt/vot-guardian/requirements.txt

# Install CPU-only PyTorch first (exact 2.1.0 for Python 3.10.11)
# Use PyTorch CPU wheel index for portability
RUN python -m pip install --upgrade "pip<25" setuptools wheel && \
    python -m pip install --no-cache-dir torch==2.1.0 --index-url https://download.pytorch.org/whl/cpu && \
    python -m pip install --no-cache-dir numpy==1.26.4

# Install MindsDB server locally with controlled dependencies
# 1) Preinstall VCS dependency required by older MindsDB versions
RUN python -m pip install --no-cache-dir "git+https://github.com/StpMax/clickhouse-sqlalchemy@5eadc4f"
# 2) Install mindsdb without auto-deps to avoid PyPI VCS restriction
RUN python -m pip install --no-cache-dir --no-deps mindsdb==23.11.4
# 3) Manually install key runtime deps compatible with Python 3.10.11 and torch 2.1.0
RUN python -m pip install --no-cache-dir \
    "sqlalchemy>=2.0.0,<3.0.0" \
    "pandas>=2.0.0,<2.1.0" \
    "protobuf==3.20.3" \
    "flask==2.2.2" \
    "werkzeug==2.2.2" \
    "flask-restx>=1.0.1,<2.0.0" \
    "python-multipart>=0.0.5" \
    "psycopg[binary]" \
    "psycopg2-binary" \
    "pymongo>=4.1.1" \
    "redis>=5.0.0,<6.0.0" \
    "walrus==0.9.3" \
    "duckdb==0.9.1" \
    "dataprep_ml>=0.0.21" \
    "dill==0.3.6" \
    "boto3" \
    "botocore" \
    "gunicorn" \
    "checksumdir>=1.2.0" \
    "flask-compress>=1.0.0" \
    "appdirs>=1.0.0" \
    "pydateinfer==0.3.0" \
    "psutil"

# Then install remaining project core deps (librosa, sdk client)
RUN python -m pip install --no-cache-dir -r /opt/vot-guardian/sandbox-core-requirements.txt

# Finally, install your app’s requirements
RUN python -m pip install --no-cache-dir -r /opt/vot-guardian/requirements.txt

# Optional: sanity check (kept as a build-time no-op; uncomment to validate during build)
# RUN python - << 'PY'
# import torch, librosa
# try:
#     import mindsdb
# except ImportError:
#     import mindsdb_sdk as mindsdb
# print("Torch:", torch.__version__)
# print("Librosa:", librosa.__version__)
# print("MindsDB OK")
# PY

# Using root inside the container for builds; run stage can drop privileges if needed.