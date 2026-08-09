FROM python:3.13-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml ./

RUN uv sync --no-dev

COPY analysis.py .

CMD ["uv", "run", "python", "analysis.py"]