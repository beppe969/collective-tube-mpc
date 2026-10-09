# Optional convenience environment. The local validation did not execute Docker.
FROM python:3.13.5-slim-bookworm
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 MPLBACKEND=Agg
COPY requirements.txt .
RUN python -m pip install --no-cache-dir --only-binary=:all: -r requirements.txt
COPY . .
ENTRYPOINT ["python", "reproduce.py"]
CMD ["run", "--study", "all", "--output", "/output/paper"]
