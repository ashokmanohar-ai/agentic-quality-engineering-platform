FROM mcr.microsoft.com/playwright:v1.62.1-noble

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/opt/venv/bin:$PATH \
    MODEL_PROVIDER=mock \
    DATABASE_URL=sqlite:////data/aqe.db

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 python3-pip python3-venv \
    && python3 -m venv /opt/venv \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY app ./app
COPY prompts ./prompts
COPY datasets ./datasets
COPY scripts ./scripts
COPY automation ./automation

RUN pip install --no-cache-dir . \
    && cd automation/playwright \
    && npm ci --ignore-scripts

RUN useradd --create-home --uid 10001 aqe \
    && mkdir -p /data /app/automation/playwright/generated \
    && chown -R aqe:aqe /data /app

USER aqe
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/health', timeout=3)"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
