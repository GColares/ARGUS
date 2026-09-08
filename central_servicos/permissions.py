from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import AccessMixin

def is_administrador(user):
    return user.is_authenticated and (user.is_superuser or user.groups.filter(name='Administrador do Sistema').exists())

def is_gestor_infraestrutura(user):
    return is_administrador(user) or (user.is_authenticated and user.groups.filter(name='Gestão de Infraestrutura').exists())

def is_operador_infraestrutura(user):
    return is_gestor_infraestrutura(user) or (user.is_authenticated and user.groups.filter(name='Operador de Infraestrutura').exists())

class AdministradorRequiredMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not is_administrador(request.user):
            raise PermissionDenied("Acesso restrito a Administradores do Sistema.")
        return super().dispatch(request, *args, **kwargs)

class GestorInfraRequiredMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not is_gestor_infraestrutura(request.user):
            raise PermissionDenied("Acesso restrito à Gestão de Infraestrutura.")
        return super().dispatch(request, *args, **kwargs)

class OperadorInfraRequiredMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not is_operador_infraestrutura(request.user):
            raise PermissionDenied("Acesso restrito a Operadores e Gestores de Infraestrutura.")
        return super().dispatch(request, *args, **kwargs)
