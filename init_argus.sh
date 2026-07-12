#!/bin/bash

echo "=== INICIANDO CONSTRUÇÃO DO AMBIENTE ARGUS ==="

# 1. Gerar as migrações do zero
echo "Detectando modelos e gerando arquivos de migração..."
python manage.py makemigrations
#python manage.py makemigrations incorporacao

# 2. Aplicar migrações ao banco novo
echo "Criando tabelas no banco de dados..."
python manage.py migrate

# 3. Criar Superusuário automaticamente
# Nota: Como você está no PowerShell/Bash, essas variáveis garantem o --noinput
echo "Configurando conta de administrador (admin)..."
export DJANGO_SUPERUSER_PASSWORD=admin
python manage.py createsuperuser --noinput --username admin --email ""

# 4. Carregar os dados fixos (Setup Institucional)
echo "Carregando Localizações, Origens e Tipos de Processos..."
python manage.py loaddata cadastros/fixtures/setup_inicial.json

echo "=== ARGUS INICIALIZADO COM SUCESSO ==="
echo "Dica: Use a senha 'admin' para acessar o /admin"

python manage.py runserver
