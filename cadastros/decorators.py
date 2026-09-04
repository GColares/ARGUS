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
    
    Suporta dois cenários de validação:
    1. Cenário Canônico (Novo): request.user.pessoa_fisica.perfil_servidor com SIAPE
    2. Cenário Legado (Fallback): request.user.perfil (almoxarifado) com SIAPE
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # 1. Verifica se está logado
        if not request.user.is_authenticated:
            return redirect('login')
        
        # 2. Cenário Canônico (Novo): Valida via PessoaFisica
        if hasattr(request.user, 'pessoa_fisica') and request.user.pessoa_fisica:
            pessoa_fisica = request.user.pessoa_fisica
            if pessoa_fisica.is_servidor and bool(pessoa_fisica.siape):
                return view_func(request, *args, **kwargs)
        
        # 3. Cenário Legado (Fallback): Valida via PerfilUsuario (almoxarifado)
        perfil = getattr(request.user, 'perfil', None)
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