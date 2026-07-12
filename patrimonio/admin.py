from django.contrib import admin
from .models import VerificacaoTermo, ItemVerificacao, BemPatrimonial, FiltroImportacao

# Registrando os modelos definitivos do Patrimônio
admin.site.register(VerificacaoTermo)
admin.site.register(ItemVerificacao)
admin.site.register(BemPatrimonial)
admin.site.register(FiltroImportacao)