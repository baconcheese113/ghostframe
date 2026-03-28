FROM python:3.13-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Create non-root user required by HF Spaces
RUN useradd -m -u 1000 user

WORKDIR /app

# Copy workspace
COPY --chown=user:user . .

# Install all workspace deps (ghostframe + ghostframe-api)
RUN uv sync --package ghostframe-api

# Patch mhcflurry for Python 3.13 (pipes module was removed)
RUN echo "from shlex import quote" > .venv/lib/python3.13/site-packages/pipes.py

# Pre-download MHCflurry models at build time (~400 MB)
# This avoids a cold-start timeout on first request
RUN uv run mhcflurry-downloads fetch models_class1_presentation

# Fix ownership after root-level installs
RUN chown -R user:user /app

USER user

EXPOSE 7860

CMD ["uv", "run", "--package", "ghostframe-api", "uvicorn", \
     "ghostframe_api.app:app", "--host", "0.0.0.0", "--port", "7860"]
