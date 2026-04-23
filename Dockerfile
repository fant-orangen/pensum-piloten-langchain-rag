FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies against stub package directories so this heavy
# layer stays cached across source edits. `pip install -e .` needs src/ and
# scripts/ to exist (they're the packages declared in pyproject.toml), but it
# does not care about their contents — it only writes a .pth file pointing at
# /app. The real source is copied in a later layer and picked up at runtime.
COPY pyproject.toml ./
RUN mkdir -p src scripts \
    && touch src/__init__.py scripts/__init__.py \
    && pip install --upgrade pip \
    && pip install -e .

COPY src ./src
COPY scripts ./scripts

RUN mkdir -p /app/data/documents /app/data/chroma /app/data/course_materials

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
