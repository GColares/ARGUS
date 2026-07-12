# Dockerfile

FROM python:3.14-slim

# Impede a criação de arquivos .pyc e permite que os logs saiam direto no terminal
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instalação de dependências essenciais do sistema para compilar pacotes como psycopg
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copia o manifesto e instala as bibliotecas
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o código-fonte
COPY . /app/

# Cria diretórios vitais e ajusta as permissões institucionais (Rodar sem ser root)
RUN mkdir -p /app/staticfiles /app/media
RUN useradd -u 8481 appuser && chown -R appuser:appuser /app
USER appuser

# Empacota os arquivos estáticos (CSS/JS/Imagens) via WhiteNoise
RUN python manage.py collectstatic --noinput

EXPOSE 8000

# Executa o Gunicorn como servidor de alta performance
CMD ["gunicorn", "argus_core.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]