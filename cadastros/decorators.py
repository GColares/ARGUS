# cadastros/decorators.py

from functools import wraps
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.shortcuts import redirect

def servidor_efetivo_required(view_func):
    """
    Bloqueio de Segurança Institucional.
    Garante que a view só seja executada se o usuário logado possuir
    um perfil vinculado como 'SERVIDOR' e com uma matrícula 'SIAPE' preenchida.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # 1. Verifica se está logado
        if not request.user.is_authenticated:
            return redirect('login')
        
        # 2. Resgata o perfil do usuário de forma segura
        perfil = getattr(request.user, 'perfil', None)
        
        # 3. Valida a regra de ouro institucional
        if perfil and perfil.vinculo == 'SERVIDOR' and bool(perfil.siape):
            return view_func(request, *args, **kwargs)
        
        # 4. Trava a execução e emite o alerta de auditoria
        messages.error(
            request, 
            "Acesso Negado: Esta operação caracteriza liquidação de despesa ou alteração de patrimônio "
            "e é restrita a Servidores Efetivos com matrícula SIAPE ativa."
        )
        # Retorna o erro HTTP 403 (Proibido)
        raise PermissionDenied 
        
    return _wrapped_view