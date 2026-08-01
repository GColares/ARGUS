import os
import sys
import glob
import django

# Carrega o contexto do Django automaticamente
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
settings_files = glob.glob('**/settings.py', recursive=True)
settings_dir = os.path.dirname(settings_files[0])
settings_module = f"{settings_dir.replace(os.sep, '.')}.settings" if settings_dir else "settings"

os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings_module)
django.setup()

from django.contrib.auth.models import User
from cadastros.models import ProjetoPDI, MembroEquipe

def aplicar_permissoes():
    # Recupera o seu usuário administrador
    usuario = User.objects.filter(is_superuser=True).first()
    if not usuario:
        print("Erro: Nenhum superusuário encontrado no banco de dados.")
        return

    projetos = ProjetoPDI.objects.all()
    vinculos_criados = 0

    for projeto in projetos:
        _, criado = MembroEquipe.objects.get_or_create(
            usuario=usuario, 
            projeto=projeto
        )
        if criado:
            vinculos_criados += 1

    print(f"Sucesso: Usuário '{usuario.username}' vinculado a {vinculos_criados} projeto(s).")
    print("A trava RBAC agora reconhecerá suas credenciais de gestão.")

if __name__ == '__main__':
    aplicar_permissoes()