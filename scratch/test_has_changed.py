import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'argus_core.settings')
django.setup()

from django.test import RequestFactory
from django.forms import modelformset_factory
from gestao_projetos.forms import AtividadePlanoAcaoForm
from cadastros.models import AtividadePlanoAcao

AtividadeFormSet = modelformset_factory(AtividadePlanoAcao, form=AtividadePlanoAcaoForm, extra=1)
initial = [{'numero': '1', 'nome': 'Teste', 'descricao': 'Desc', 'mes_inicio_relativo': 1, 'mes_fim_relativo': 2}]
formset = AtividadeFormSet(initial=initial, queryset=AtividadePlanoAcao.objects.none())

post_data = {'form-TOTAL_FORMS': '1', 'form-INITIAL_FORMS': '0', 'form-MIN_NUM_FORMS': '0', 'form-MAX_NUM_FORMS': '1000'}
for name, field in formset.forms[0].fields.items():
    post_data[f'form-0-{name}'] = formset.forms[0][name].value() if formset.forms[0][name].value() is not None else ''

# DO NOT PASS initial to the POST formset! The view DOES NOT pass initial to POST!
formset_post = AtividadeFormSet(post_data, queryset=AtividadePlanoAcao.objects.none())

print('Is valid?', formset_post.is_valid())
print('Has changed?', formset_post.forms[0].has_changed())
print('Saved objects:', formset_post.save(commit=False))
