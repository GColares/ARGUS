import os

models = [
    ("Predio", "predio", "Prédio", "Prédios"),
    ("Andar", "andar", "Andar", "Andares"),
    ("Sala", "sala", "Sala", "Salas"),
    ("AtivoPredial", "ativopredial", "Ativo Predial", "Ativos Prediais"),
    ("CategoriaServico", "categoriaservico", "Categoria de Serviço", "Categorias de Serviço"),
    ("OrdemServico", "ordemservico", "Ordem de Serviço", "Ordens de Serviço"),
    ("MaterialUtilizado", "materialutilizado", "Material Utilizado", "Materiais Utilizados")
]

APP_DIR = r"c:\Projetos\ARGUS\manutencao_predial"
TPL_DIR = os.path.join(APP_DIR, "templates", "manutencao_predial")

os.makedirs(TPL_DIR, exist_ok=True)

# 1. FORMS.PY
forms_code = """from django import forms
from .models import Predio, Andar, Sala, AtivoPredial, CategoriaServico, OrdemServico, MaterialUtilizado

class BaseBootstrapForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-check-input'
            else:
                field.widget.attrs['class'] = 'form-control'

"""
for m, ml, name, name_pl in models:
    forms_code += f"""class {m}Form(BaseBootstrapForm):
    class Meta:
        model = {m}
        fields = '__all__'

"""
with open(os.path.join(APP_DIR, "forms.py"), "w", encoding="utf-8") as f:
    f.write(forms_code)

# 2. VIEWS.PY (Append)
views_code = """
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import PredioForm, AndarForm, SalaForm, AtivoPredialForm, CategoriaServicoForm, OrdemServicoForm, MaterialUtilizadoForm
from .models import Predio, Andar, Sala, AtivoPredial, CategoriaServico, OrdemServico, MaterialUtilizado

"""
for m, ml, name, name_pl in models:
    views_code += f"""
class {m}ListView(LoginRequiredMixin, ListView):
    model = {m}
    template_name = 'manutencao_predial/{ml}_list.html'
    context_object_name = 'objects'

class {m}CreateView(LoginRequiredMixin, CreateView):
    model = {m}
    form_class = {m}Form
    template_name = 'manutencao_predial/{ml}_form.html'
    success_url = reverse_lazy('home_manutencao_predial:{ml}_list')

class {m}UpdateView(LoginRequiredMixin, UpdateView):
    model = {m}
    form_class = {m}Form
    template_name = 'manutencao_predial/{ml}_form.html'
    success_url = reverse_lazy('home_manutencao_predial:{ml}_list')

class {m}DeleteView(LoginRequiredMixin, DeleteView):
    model = {m}
    template_name = 'manutencao_predial/{ml}_confirm_delete.html'
    success_url = reverse_lazy('home_manutencao_predial:{ml}_list')
"""
with open(os.path.join(APP_DIR, "views.py"), "a", encoding="utf-8") as f:
    f.write(views_code)

# 3. URLS.PY (Replace completely)
urls_code = """from django.urls import path
from . import views

app_name = 'home_manutencao_predial'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
"""
for m, ml, name, name_pl in models:
    urls_code += f"""
    path('{ml}/', views.{m}ListView.as_view(), name='{ml}_list'),
    path('{ml}/novo/', views.{m}CreateView.as_view(), name='{ml}_create'),
    path('{ml}/<int:pk>/editar/', views.{m}UpdateView.as_view(), name='{ml}_update'),
    path('{ml}/<int:pk>/excluir/', views.{m}DeleteView.as_view(), name='{ml}_delete'),
"""
urls_code += "]\n"
with open(os.path.join(APP_DIR, "urls.py"), "w", encoding="utf-8") as f:
    f.write(urls_code)

# 4. TEMPLATES
for m, ml, name, name_pl in models:
    # List
    list_html = f"""{{% extends 'base.html' %}}
{{% block title %}}{name_pl}{{% endblock %}}
{{% block content %}}
<div class="d-flex justify-content-between align-items-center mb-4">
    <h2 class="mb-0 text-institucional"><i class="fas fa-list me-2"></i> Lista de {name_pl}</h2>
    <div>
        <a href="{{% url 'home_manutencao_predial:dashboard' %}}" class="btn btn-outline-secondary me-2">Voltar</a>
        <a href="{{% url 'home_manutencao_predial:{ml}_create' %}}" class="btn btn-success fw-bold">Novo {name}</a>
    </div>
</div>
<div class="card shadow-sm border-0">
    <div class="card-body p-0">
        <div class="table-responsive">
            <table class="table table-hover align-middle mb-0">
                <thead class="table-light">
                    <tr>
                        <th class="ps-3">ID / Nome</th>
                        <th class="text-end pe-3">Ações</th>
                    </tr>
                </thead>
                <tbody>
                    {{% for obj in objects %}}
                    <tr>
                        <td class="ps-3">{{{{ obj }}}}</td>
                        <td class="text-end pe-3">
                            <a href="{{% url 'home_manutencao_predial:{ml}_update' obj.pk %}}" class="btn btn-sm btn-primary"><i class="fas fa-edit"></i></a>
                            <a href="{{% url 'home_manutencao_predial:{ml}_delete' obj.pk %}}" class="btn btn-sm btn-danger"><i class="fas fa-trash"></i></a>
                        </td>
                    </tr>
                    {{% empty %}}
                    <tr>
                        <td colspan="2" class="text-center py-4 text-muted">Nenhum registro encontrado.</td>
                    </tr>
                    {{% endfor %}}
                </tbody>
            </table>
        </div>
    </div>
</div>
{{% endblock %}}
"""
    with open(os.path.join(TPL_DIR, f"{ml}_list.html"), "w", encoding="utf-8") as f:
        f.write(list_html)

    # Form
    form_html = f"""{{% extends 'base.html' %}}
{{% block title %}}{name}{{% endblock %}}
{{% block content %}}
<div class="row justify-content-center">
    <div class="col-md-8">
        <div class="card shadow-sm border-0">
            <div class="card-header bg-white py-3">
                <h5 class="mb-0 fw-bold text-secondary">{{% if object %}}Editar{{% else %}}Novo{{% endif %}} {name}</h5>
            </div>
            <div class="card-body">
                <form method="post">
                    {{% csrf_token %}}
                    {{% for field in form %}}
                    <div class="mb-3">
                        <label class="form-label fw-bold">{{{{ field.label }}}}</label>
                        {{{{ field }}}}
                        {{% if field.help_text %}}
                        <div class="form-text">{{{{ field.help_text }}}}</div>
                        {{% endif %}}
                        {{% for error in field.errors %}}
                        <div class="text-danger small">{{{{ error }}}}</div>
                        {{% endfor %}}
                    </div>
                    {{% endfor %}}
                    <div class="d-flex justify-content-end mt-4">
                        <a href="{{% url 'home_manutencao_predial:{ml}_list' %}}" class="btn btn-outline-secondary me-2">Cancelar</a>
                        <button type="submit" class="btn btn-success fw-bold">Salvar</button>
                    </div>
                </form>
            </div>
        </div>
    </div>
</div>
{{% endblock %}}
"""
    with open(os.path.join(TPL_DIR, f"{ml}_form.html"), "w", encoding="utf-8") as f:
        f.write(form_html)

    # Confirm Delete
    delete_html = f"""{{% extends 'base.html' %}}
{{% block title %}}Excluir {name}{{% endblock %}}
{{% block content %}}
<div class="row justify-content-center">
    <div class="col-md-6">
        <div class="card shadow-sm border-0 border-danger">
            <div class="card-header bg-danger text-white py-3">
                <h5 class="mb-0 fw-bold"><i class="fas fa-exclamation-triangle me-2"></i> Confirmar Exclusão</h5>
            </div>
            <div class="card-body text-center py-5">
                <h4>Tem certeza que deseja excluir?</h4>
                <p class="text-muted fs-5 mb-4"><strong>{{{{ object }}}}</strong></p>
                <form method="post">
                    {{% csrf_token %}}
                    <a href="{{% url 'home_manutencao_predial:{ml}_list' %}}" class="btn btn-outline-secondary me-2 px-4">Cancelar</a>
                    <button type="submit" class="btn btn-danger fw-bold px-4">Excluir Definitivamente</button>
                </form>
            </div>
        </div>
    </div>
</div>
{{% endblock %}}
"""
    with open(os.path.join(TPL_DIR, f"{ml}_confirm_delete.html"), "w", encoding="utf-8") as f:
        f.write(delete_html)

print("CRUD generated successfully!")
