import os, codecs

templates_dir = r'c:\Projetos\ARGUS\central_servicos\templates\central_servicos'
os.makedirs(templates_dir, exist_ok=True)

models = {
    'andar': {'title': 'Andar', 'plural': 'Andares', 'var': 'andares'},
    'sala': {'title': 'Sala', 'plural': 'Salas', 'var': 'salas'},
    'ativopredial': {'title': 'Ativo Predial', 'plural': 'Ativos Prediais', 'var': 'ativos'},
    'categoriaservico': {'title': 'Categoria de Serviço', 'plural': 'Categorias de Serviço', 'var': 'categorias'},
    'finalidade': {'title': 'Finalidade', 'plural': 'Finalidades', 'var': 'finalidades'},
}

for model_name, data in models.items():
    title = data['title']
    plural = data['plural']
    var_list = data['var']

    list_html = f'''{{% extends 'base.html' %}}
{{% block title %}}{plural} - Central de Serviços{{% endblock %}}
{{% block content %}}
<div class=\"container-fluid px-4 py-4\">
    <div class=\"d-flex justify-content-between align-items-center mb-4\">
        <h2><i class=\"fas fa-list text-primary me-2\"></i> Gestão de {plural}</h2>
        <a href=\"{{% url 'central_servicos:{model_name}_novo' %}}\" class=\"btn btn-primary shadow-sm\">
            <i class=\"fas fa-plus me-1\"></i> Novo {title}
        </a>
    </div>
    <div class=\"card shadow-sm border-0 rounded-3\">
        <div class=\"card-body p-0\">
            <div class=\"table-responsive\">
                <table class=\"table table-hover align-middle mb-0\">
                    <thead class=\"table-light\">
                        <tr>
                            <th class=\"text-center px-4\">ID</th>
                            <th class=\"text-center\">Nome</th>
                            <th class=\"text-center px-4\">Ações</th>
                        </tr>
                    </thead>
                    <tbody>
                        {{% for obj in {var_list} %}}
                        <tr>
                            <td class=\"text-center text-muted\">#{{{{ obj.id }}}}</td>
                            <td class=\"text-center fw-semibold\">{{{{ obj.nome }}}}</td>
                            <td class=\"text-center\">
                                <a href=\"{{% url 'central_servicos:{model_name}_editar' obj.pk %}}\" class=\"btn btn-sm btn-outline-secondary me-2\" title=\"Editar\">
                                    <i class=\"fas fa-edit\"></i>
                                </a>
                                <a href=\"{{% url 'central_servicos:{model_name}_excluir' obj.pk %}}\" class=\"btn btn-sm btn-outline-danger\" title=\"Excluir\">
                                    <i class=\"fas fa-trash-alt\"></i>
                                </a>
                            </td>
                        </tr>
                        {{% empty %}}
                        <tr>
                            <td colspan=\"3\" class=\"text-center text-muted py-4\">
                                <i class=\"fas fa-inbox fa-3x mb-3 text-light\"></i>
                                <p class=\"mb-0\">Nenhum registro encontrado.</p>
                            </td>
                        </tr>
                        {{% endfor %}}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</div>
{{% endblock %}}
'''

    form_html = f'''{{% extends 'base.html' %}}
{{% block title %}}{{{{% if object %}}}}Editar{{{{% else %}}}}Novo{{{{% endif %}}}} {title} - Central de Serviços{{% endblock %}}
{{% block content %}}
<div class=\"container-fluid px-4 py-4\">
    <div class=\"row justify-content-center\">
        <div class=\"col-lg-8\">
            <div class=\"card shadow-sm border-0 rounded-4\">
                <div class=\"card-header bg-white border-0 pt-4 pb-0\">
                    <h3 class=\"fw-bold text-primary mb-0\">
                        <i class=\"fas fa-edit me-2\"></i>
                        {{{{% if object %}}}}Editar {title}{{{{% else %}}}}Novo {title}{{{{% endif %}}}}
                    </h3>
                </div>
                <div class=\"card-body p-4\">
                    <form method=\"post\">
                        {{% csrf_token %}}
                        <div class=\"row g-3\">
                            {{% for field in form %}}
                            <div class=\"col-md-12\">
                                <label class=\"form-label fw-semibold text-muted small\">{{{{ field.label }}}}</label>
                                {{{{ field }}}}
                                {{{{% if field.help_text %}}}}
                                <div class=\"form-text\">{{{{ field.help_text }}}}</div>
                                {{{{% endif %}}}}
                                {{{{% if field.errors %}}}}
                                <div class=\"invalid-feedback d-block\">
                                    {{% for error in field.errors %}}{{{{ error }}}}{{% endfor %}}
                                </div>
                                {{{{% endif %}}}}
                            </div>
                            {{% endfor %}}
                        </div>
                        <hr class=\"my-4 text-muted\">
                        <div class=\"d-flex justify-content-end gap-2\">
                            <a href=\"{{% url 'central_servicos:{model_name}_list' %}}\" class=\"btn btn-light px-4\">Cancelar</a>
                            <button type=\"submit\" class=\"btn btn-primary px-4 shadow-sm\">
                                <i class=\"fas fa-save me-1\"></i> Salvar
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </div>
</div>
{{% endblock %}}
'''

    delete_html = f'''{{% extends 'base.html' %}}
{{% block title %}}Excluir {title}{{% endblock %}}
{{% block content %}}
<div class=\"container-fluid px-4 py-5\">
    <div class=\"row justify-content-center\">
        <div class=\"col-md-6\">
            <div class=\"card shadow border-0 rounded-4\">
                <div class=\"card-body p-5 text-center\">
                    <div class=\"mb-4\">
                        <i class=\"fas fa-exclamation-triangle fa-4x text-warning\"></i>
                    </div>
                    <h3 class=\"fw-bold text-dark mb-3\">Confirmar Exclusão</h3>
                    <p class=\"lead text-muted mb-4\">Tem certeza que deseja excluir o registro <strong>\"{{{{ object.nome }}}}\"</strong>?</p>
                    <div class=\"alert alert-danger border-0\" role=\"alert\">
                        <i class=\"fas fa-info-circle me-2\"></i> Esta ação não pode ser desfeita.
                    </div>
                    <form method=\"post\" class=\"mt-4\">
                        {{% csrf_token %}}
                        <div class=\"d-flex justify-content-center gap-3\">
                            <a href=\"{{% url 'central_servicos:{model_name}_list' %}}\" class=\"btn btn-light btn-lg px-4\">Cancelar</a>
                            <button type=\"submit\" class=\"btn btn-danger btn-lg px-4 shadow-sm\">
                                <i class=\"fas fa-trash-alt me-2\"></i> Sim, Excluir
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </div>
</div>
{{% endblock %}}
'''

    with codecs.open(os.path.join(templates_dir, f'{model_name}_list.html'), 'w', 'utf-8') as f:
        f.write(list_html)
    with codecs.open(os.path.join(templates_dir, f'{model_name}_form.html'), 'w', 'utf-8') as f:
        f.write(form_html)
    with codecs.open(os.path.join(templates_dir, f'{model_name}_confirm_delete.html'), 'w', 'utf-8') as f:
        f.write(delete_html)

print('15 templates gerados com sucesso!')
