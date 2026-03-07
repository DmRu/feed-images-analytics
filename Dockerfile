# FROM python:3.13-alpine
FROM python:3.12-slim-trixie

WORKDIR /app

# Install system dependencies for Pillow and uv
# RUN apk add --no-cache \
#     curl \
#     gcc \
#     musl-dev \
#     jpeg-dev \
#     zlib-dev \
#     libjpeg-turbo-dev

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
ENV PATH="/uv/bin:${PATH}"

# Copy project files
COPY . /app

# Install dependencies using uv
RUN uv sync --locked

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["uv", "run", "streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
