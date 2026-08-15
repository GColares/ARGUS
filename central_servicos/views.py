# pyrefly: ignore [untyped-import]
from django.shortcuts import render
# pyrefly: ignore [untyped-import]
from django.contrib.auth.decorators import login_required
# pyrefly: ignore [untyped-import]
from django.contrib.auth.mixins import LoginRequiredMixin
# pyrefly: ignore [untyped-import]
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, View, TemplateView
# pyrefly: ignore [untyped-import]
from django.urls import reverse_lazy
from .models import OrdemServico, Predio, Andar, Ambiente, TipoAmbiente, CategoriaElemento, TipoElemento, ElementoConstrutivo, TipoAtivo, AtivoPredial, CategoriaServico, MaterialUtilizado, Finalidade
from .forms import OrdemServicoForm, OrdemServicoCancelamentoForm, PredioForm, AndarForm, AmbienteForm, TipoAmbienteForm, CategoriaElementoForm, ElementoConstrutivoForm, TipoElementoForm, TipoAtivoForm, AtivoPredialForm, AtivoPredialLoteForm, CategoriaServicoForm, FinalidadeForm
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.http import JsonResponse

@login_required
def home_central_servicos(request):
    # pyrefly: ignore [missing-attribute]
    os_pendentes = OrdemServico.objects.filter(status='PENDENTE').count()
    # pyrefly: ignore [missing-attribute]
    os_programadas = OrdemServico.objects.filter(status='PROGRAMADA').count()
    # pyrefly: ignore [missing-attribute]
    os_iniciadas = OrdemServico.objects.filter(status='INICIADA').count()
    # pyrefly: ignore [missing-attribute]
    os_em_andamento = OrdemServico.objects.filter(status='EM_ANDAMENTO').count()
    # pyrefly: ignore [missing-attribute]
    os_suspensas = OrdemServico.objects.filter(status='SUSPENSA').count()
    # pyrefly: ignore [missing-attribute]
    os_concluidas = OrdemServico.objects.filter(status='CONCLUIDA').count()
    
    context = {
        'os_pendentes': os_pendentes,
        'os_programadas': os_programadas,
        'os_iniciadas': os_iniciadas,
        'os_em_andamento': os_em_andamento,
        'os_suspensas': os_suspensas,
        'os_concluidas': os_concluidas,
        'total_predios': Predio.objects.count(),
        'total_andares': Andar.objects.count(),
        'total_ambientes': Ambiente.objects.count(),
        'total_elementos': ElementoConstrutivo.objects.count(),
        'total_ativos': AtivoPredial.objects.count(),
        'total_tipos_ambiente': TipoAmbiente.objects.count(),
        'total_tipos_ativo': TipoAtivo.objects.count(),
    }
    return render(request, 'central_servicos/home_central_servicos.html', context)


class OrdemServicoCreateView(LoginRequiredMixin, CreateView):
    model = OrdemServico
    form_class = OrdemServicoForm
    template_name = 'central_servicos/os_form.html'
    success_url = reverse_lazy('central_servicos:home_central_servicos')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Injeta a estrutura hierárquica completa para a interface em árvore
        context['predios_hierarquia'] = Predio.objects.prefetch_related('andares__ambientes').all()
        return context

    def form_valid(self, form):
        ambientes = form.cleaned_data.get('ambientes')
        categoria = form.cleaned_data.get('categoria')
        descricao_problema = form.cleaned_data.get('descricao_problema')
        ativo_predial = form.cleaned_data.get('ativo_predial')
        solicitante = self.request.user

        # Se houver mais de uma sala, ignoramos o ativo predial (manutenção geral)
        if ambientes.count() > 1:
            ativo_predial = None

        os_criadas = 0
        for ambiente in ambientes:
            OrdemServico.objects.create(
                ambiente=ambiente,
                categoria=categoria,
                descricao_problema=descricao_problema,
                ativo_predial=ativo_predial,
                solicitante=solicitante
            )
            os_criadas += 1

        messages.success(self.request, f'{os_criadas} Ordem(ns) de Serviço gerada(s) com sucesso.')
        from django.http import JsonResponse, HttpResponseRedirect
        return HttpResponseRedirect(self.success_url)

class RelatorioOSView(LoginRequiredMixin, ListView):
    model = OrdemServico
    template_name = 'central_servicos/relatorio_os.html'
    context_object_name = 'ordens'

    def get_queryset(self):
        status = self.kwargs.get('status')
        return OrdemServico.objects.filter(status=status).order_by('-data_abertura')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        status = self.kwargs.get('status')
        # Obter o nome amigável do status para exibir no título
        status_dict = dict(OrdemServico.STATUS_CHOICES)
        # pyrefly: ignore [no-matching-overload]
        context['status_display'] = status_dict.get(status, status)
        return context

class OrdemServicoHistoricoView(LoginRequiredMixin, ListView):
    model = OrdemServico
    template_name = 'central_servicos/historico_ordem_servico.html'
    context_object_name = 'ordens'

    def get_queryset(self):
        # pyrefly: ignore [missing-attribute]
        return OrdemServico.objects.all().order_by('-data_abertura')

class OrdemServicoCancelarView(LoginRequiredMixin, UpdateView):
    model = OrdemServico
    form_class = OrdemServicoCancelamentoForm
    template_name = 'central_servicos/cancelar_ordem_servico.html'
    success_url = reverse_lazy('central_servicos:historico_os')

    def dispatch(self, request, *args, **kwargs):
        os = self.get_object()
        
        # Se já concluída ou cancelada, não pode cancelar
        if os.status in ['CONCLUIDA', 'CANCELADA']:
            messages.error(request, 'Esta Ordem de Serviço não pode ser cancelada pois já está concluída ou cancelada.')
            raise PermissionDenied("OS não pode ser cancelada.")

        # Se Pendente ou Programada, Solicitante ou Gestor pode cancelar
        if os.status in ['PENDENTE', 'PROGRAMADA']:
            if os.solicitante != request.user and not request.user.is_staff:
                messages.error(request, 'Você não tem permissão para cancelar esta Ordem de Serviço.')
                raise PermissionDenied("Sem permissão.")
                
        # Se Iniciada ou Em Andamento, APENAS Gestor pode cancelar
        if os.status in ['INICIADA', 'EM_ANDAMENTO', 'SUSPENSA']:
            if not request.user.is_staff:
                messages.error(request, 'Apenas gestores podem cancelar uma Ordem de Serviço em andamento.')
                raise PermissionDenied("Apenas gestores.")
                
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.status = 'CANCELADA'
        messages.success(self.request, 'Ordem de Serviço cancelada com sucesso.')
        return super().form_valid(form)

# ==========================================
# GESTÃO DE PRÉDIOS
# ==========================================
class PredioListView(LoginRequiredMixin, ListView):
    model = Predio
    template_name = 'central_servicos/predio_list.html'
    context_object_name = 'predios'
    
    def get_queryset(self):
        # pyrefly: ignore [missing-attribute]
        return Predio.objects.all().order_by('nome')

class PredioCreateView(LoginRequiredMixin, CreateView):
    model = Predio
    form_class = PredioForm
    template_name = 'central_servicos/predio_form.html'
    success_url = reverse_lazy('central_servicos:predio_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Prédio cadastrado com sucesso.')
        return super().form_valid(form)

class PredioUpdateView(LoginRequiredMixin, UpdateView):
    model = Predio
    form_class = PredioForm
    template_name = 'central_servicos/predio_form.html'
    success_url = reverse_lazy('central_servicos:predio_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Prédio atualizado com sucesso.')
        return super().form_valid(form)

class PredioDeleteView(LoginRequiredMixin, DeleteView):
    model = Predio
    template_name = 'central_servicos/predio_confirm_delete.html'
    success_url = reverse_lazy('central_servicos:predio_list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Prédio excluído com sucesso.")
        return super().delete(request, *args, **kwargs)

# ==========================================
# GESTÃO DE ANDARES
# ==========================================
class AndarListView(LoginRequiredMixin, ListView):
    model = Andar
    template_name = 'central_servicos/andar_list.html'
    context_object_name = 'andares'

class AndarCreateView(LoginRequiredMixin, CreateView):
    model = Andar
    form_class = AndarForm
    template_name = 'central_servicos/andar_form.html'
    success_url = reverse_lazy('central_servicos:andar_list')
    def form_valid(self, form):
        messages.success(self.request, 'Andar cadastrado com sucesso.')
        return super().form_valid(form)

class AndarUpdateView(LoginRequiredMixin, UpdateView):
    model = Andar
    form_class = AndarForm
    template_name = 'central_servicos/andar_form.html'
    success_url = reverse_lazy('central_servicos:andar_list')
    def form_valid(self, form):
        messages.success(self.request, 'Andar atualizado com sucesso.')
        return super().form_valid(form)

class AndarDeleteView(LoginRequiredMixin, DeleteView):
    model = Andar
    template_name = 'central_servicos/andar_confirm_delete.html'
    success_url = reverse_lazy('central_servicos:andar_list')
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Andar excluído com sucesso.')
        return super().delete(request, *args, **kwargs)

# ==========================================
# GESTÃO DE AMBIENTES
# ==========================================
class AmbienteListView(LoginRequiredMixin, ListView):
    model = Ambiente
    template_name = 'central_servicos/ambiente_list.html'
    context_object_name = 'ambientes'

class AmbienteCreateView(LoginRequiredMixin, CreateView):
    model = Ambiente
    form_class = AmbienteForm
    template_name = 'central_servicos/ambiente_form.html'
    success_url = reverse_lazy('central_servicos:ambiente_list')

    def get_initial(self):
        initial = super().get_initial()
        if self.request.GET.get('predio'):
            initial['predio'] = self.request.GET.get('predio')
        if self.request.GET.get('andar'):
            initial['andar'] = self.request.GET.get('andar')
        return initial

    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, 'Ambiente cadastrado com sucesso.')
        if self.request.POST.get('fixar_predio_andar') == 'on':
            from django.urls import reverse
            from django.http import HttpResponseRedirect
            url = reverse('central_servicos:ambiente_novo')
            query = f"?predio={self.object.predio_id}"
            if self.object.andar_id:
                query += f"&andar={self.object.andar_id}"
            return HttpResponseRedirect(url + query)
        return super().form_valid(form)

class AmbienteUpdateView(LoginRequiredMixin, UpdateView):
    model = Ambiente
    form_class = AmbienteForm
    template_name = 'central_servicos/ambiente_form.html'
    success_url = reverse_lazy('central_servicos:ambiente_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.object:
            context['historico_ambiente'] = self.object.history.all()
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Ambiente atualizado com sucesso.')
        return super().form_valid(form)

class AmbienteDeleteView(LoginRequiredMixin, DeleteView):
    model = Ambiente
    template_name = 'central_servicos/ambiente_confirm_delete.html'
    success_url = reverse_lazy('central_servicos:ambiente_list')
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Sala excluída com sucesso.')
        return super().delete(request, *args, **kwargs)

# ==========================================
# GESTÃO DE ATIVOS PREDIAIS
# ==========================================
class AtivoPredialListView(LoginRequiredMixin, ListView):
    model = AtivoPredial
    template_name = 'central_servicos/ativopredial_list.html'
    context_object_name = 'ativos'

    def get_queryset(self):
        qs = super().get_queryset()
        
        busca = self.request.GET.get('q', '').strip()
        filtro_tipo = self.request.GET.get('tipo', '')
        filtro_predio = self.request.GET.get('predio', '')
        filtro_ambiente = self.request.GET.get('ambiente', '')
        sort_param = self.request.GET.get('sort', '')

        from django.db.models import Q
        
        if busca:
            qs = qs.filter(
                Q(nome_apelido__icontains=busca) |
                Q(patrimonio__icontains=busca) |
                Q(tipo__nome__icontains=busca) |
                Q(ambiente__nome__icontains=busca)
            ).distinct()
            
        if filtro_tipo:
            qs = qs.filter(tipo_id=filtro_tipo)
        if filtro_ambiente:
            qs = qs.filter(ambiente_id=filtro_ambiente)
        elif filtro_predio:
            qs = qs.filter(ambiente__andar__predio_id=filtro_predio)
            
        if sort_param:
            qs = qs.order_by(sort_param)
            
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Injeta a estrutura hierárquica completa para a interface em árvore
        context['predios_hierarquia'] = Predio.objects.prefetch_related('andares__ambientes').all()
        
        context['tipos_ativos'] = TipoAtivo.objects.all()
        context['predios'] = Predio.objects.all()
        context['ambientes_list'] = Ambiente.objects.all()
        
        context['busca'] = self.request.GET.get('q', '').strip()
        context['filtro_tipo'] = self.request.GET.get('tipo', '')
        context['filtro_predio'] = self.request.GET.get('predio', '')
        context['filtro_ambiente'] = self.request.GET.get('ambiente', '')
        context['current_sort'] = self.request.GET.get('sort', '')
        
        context['filtros_ativos'] = bool(context['filtro_tipo'] or context['filtro_predio'] or context['filtro_ambiente'])
        
        return context

from django.views.generic import TemplateView
from django.views import View
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.urls import reverse

class AmbienteAtivosOffcanvasView(LoginRequiredMixin, TemplateView):
    template_name = 'central_servicos/_ambiente_ativos_offcanvas.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ambiente_id = self.kwargs.get('ambiente_id')
        ambiente = get_object_or_404(Ambiente, pk=ambiente_id)
        context['ambiente'] = ambiente
        context['ativos'] = AtivoPredial.objects.filter(ambiente=ambiente).select_related('tipo')
        context['tipos_ativos'] = TipoAtivo.objects.all()
        return context

class AtivoPredialRapidoCreateView(LoginRequiredMixin, View):
    def post(self, request, ambiente_id):
        ambiente = get_object_or_404(Ambiente, pk=ambiente_id)
        tipo_id = request.POST.get('tipo')
        nome_apelido = request.POST.get('nome_apelido')
        patrimonio = request.POST.get('patrimonio')
        
        if tipo_id:
            tipo = get_object_or_404(TipoAtivo, pk=tipo_id)
            AtivoPredial.objects.create(
                ambiente=ambiente,
                tipo=tipo,
                nome_apelido=nome_apelido,
                patrimonio=patrimonio
            )
            messages.success(request, 'Ativo adicionado com sucesso!')
        else:
            messages.error(request, 'Erro: Tipo de ativo não informado.')
            
        return redirect('central_servicos:ativopredial_list')

class AtivoPredialCreateView(LoginRequiredMixin, CreateView):
    model = AtivoPredial
    form_class = AtivoPredialLoteForm
    template_name = 'central_servicos/ativopredial_form.html'
    success_url = reverse_lazy('central_servicos:ativopredial_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Injeta a estrutura hierárquica completa para a interface em árvore
        context['predios_hierarquia'] = Predio.objects.prefetch_related('andares__ambientes').all()
        return context

    def form_valid(self, form):
        ambientes = form.cleaned_data.get('ambientes')
        tipo = form.cleaned_data.get('tipo')
        nome_apelido = form.cleaned_data.get('nome_apelido')
        descricao = form.cleaned_data.get('descricao')
        
        # Cria os ativos considerando a quantidade por sala
        ativos_criados = 0
        for ambiente in ambientes:
            qtd_str = self.request.POST.get(f'quantidade_ambiente_{ambiente.id}')
            try:
                qtd = int(qtd_str) if qtd_str else 1
            except ValueError:
                qtd = 1
                
            for _ in range(qtd):
                AtivoPredial.objects.create(
                    ambiente=ambiente,
                    tipo=tipo,
                    nome_apelido=nome_apelido,
                    descricao=descricao,
                    patrimonio='', # Em branco no lote
                    numero_serie='' # Em branco no lote
                )
                ativos_criados += 1
            
        messages.success(self.request, f'{ativos_criados} Ativo(s) Predial(is) cadastrado(s) com sucesso.')
        # Redireciona manualmente pois não estamos usando form.save() padrão
        from django.http import JsonResponse, HttpResponseRedirect
        return HttpResponseRedirect(self.success_url)

class AtivoPredialUpdateView(LoginRequiredMixin, UpdateView):
    model = AtivoPredial
    form_class = AtivoPredialForm
    template_name = 'central_servicos/ativopredial_form.html'
    success_url = reverse_lazy('central_servicos:ativopredial_list')
    def form_valid(self, form):
        messages.success(self.request, 'Ativo Predial atualizado com sucesso.')
        return super().form_valid(form)

class AtivoPredialDeleteView(LoginRequiredMixin, DeleteView):
    model = AtivoPredial
    template_name = 'central_servicos/ativopredial_confirm_delete.html'
    success_url = reverse_lazy('central_servicos:ativopredial_list')
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Ativo Predial excluído com sucesso.')
        return super().delete(request, *args, **kwargs)

# ==========================================
# GESTÃO DE CATEGORIAS DE SERVIÇO
# ==========================================
class CategoriaServicoListView(LoginRequiredMixin, ListView):
    model = CategoriaServico
    template_name = 'central_servicos/categoriaservico_list.html'
    context_object_name = 'categorias'

class CategoriaServicoCreateView(LoginRequiredMixin, CreateView):
    model = CategoriaServico
    form_class = CategoriaServicoForm
    template_name = 'central_servicos/categoriaservico_form.html'
    success_url = reverse_lazy('central_servicos:categoriaservico_list')
    def form_valid(self, form):
        messages.success(self.request, 'Categoria cadastrada com sucesso.')
        return super().form_valid(form)

class CategoriaServicoUpdateView(LoginRequiredMixin, UpdateView):
    model = CategoriaServico
    form_class = CategoriaServicoForm
    template_name = 'central_servicos/categoriaservico_form.html'
    success_url = reverse_lazy('central_servicos:categoriaservico_list')
    def form_valid(self, form):
        messages.success(self.request, 'Categoria atualizada com sucesso.')
        return super().form_valid(form)

class CategoriaServicoDeleteView(LoginRequiredMixin, DeleteView):
    model = CategoriaServico
    template_name = 'central_servicos/categoriaservico_confirm_delete.html'
    success_url = reverse_lazy('central_servicos:categoriaservico_list')
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Categoria excluída com sucesso.')
        return super().delete(request, *args, **kwargs)

# ==========================================
# GESTÃO DE FINALIDADES
# ==========================================
class FinalidadeListView(LoginRequiredMixin, ListView):
    model = Finalidade
    template_name = 'central_servicos/finalidade_list.html'
    context_object_name = 'finalidades'

class FinalidadeCreateView(LoginRequiredMixin, CreateView):
    model = Finalidade
    form_class = FinalidadeForm
    template_name = 'central_servicos/finalidade_form.html'
    success_url = reverse_lazy('central_servicos:finalidade_list')
    def form_valid(self, form):
        messages.success(self.request, 'Finalidade cadastrada com sucesso.')
        return super().form_valid(form)

class FinalidadeUpdateView(LoginRequiredMixin, UpdateView):
    model = Finalidade
    form_class = FinalidadeForm
    template_name = 'central_servicos/finalidade_form.html'
    success_url = reverse_lazy('central_servicos:finalidade_list')
    def form_valid(self, form):
        messages.success(self.request, 'Finalidade atualizada com sucesso.')
        return super().form_valid(form)

class FinalidadeDeleteView(LoginRequiredMixin, DeleteView):
    model = Finalidade
    template_name = 'central_servicos/finalidade_confirm_delete.html'
    success_url = reverse_lazy('central_servicos:finalidade_list')
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Finalidade excluída com sucesso.')
        return super().delete(request, *args, **kwargs)

class TipoAtivoListView(LoginRequiredMixin, ListView):
    model = TipoAtivo
    template_name = 'central_servicos/tipoativo_list.html'

class TipoAtivoCreateView(LoginRequiredMixin, CreateView):
    model = TipoAtivo
    form_class = TipoAtivoForm
    template_name = 'central_servicos/tipoativo_form.html'
    success_url = reverse_lazy('central_servicos:tipoativo_list')
    def form_valid(self, form):
        messages.success(self.request, 'Tipo de Ativo cadastrado com sucesso.')
        return super().form_valid(form)

class TipoAtivoUpdateView(LoginRequiredMixin, UpdateView):
    model = TipoAtivo
    form_class = TipoAtivoForm
    template_name = 'central_servicos/tipoativo_form.html'
    success_url = reverse_lazy('central_servicos:tipoativo_list')
    def form_valid(self, form):
        messages.success(self.request, 'Tipo de Ativo atualizado com sucesso.')
        return super().form_valid(form)

class TipoAtivoDeleteView(LoginRequiredMixin, DeleteView):
    model = TipoAtivo
    template_name = 'central_servicos/tipoativo_confirm_delete.html'
    success_url = reverse_lazy('central_servicos:tipoativo_list')
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Tipo de Ativo excluído com sucesso.')
        return super().delete(request, *args, **kwargs)

class TipoAmbienteListView(LoginRequiredMixin, ListView):
    model = TipoAmbiente
    template_name = 'central_servicos/tipoambiente_list.html'
    context_object_name = 'tiposambiente'

class TipoAmbienteCreateView(LoginRequiredMixin, CreateView):
    model = TipoAmbiente
    form_class = TipoAmbienteForm
    template_name = 'central_servicos/tipoambiente_form.html'
    success_url = reverse_lazy('central_servicos:tipoambiente_list')

class TipoAmbienteUpdateView(LoginRequiredMixin, UpdateView):
    model = TipoAmbiente
    form_class = TipoAmbienteForm
    template_name = 'central_servicos/tipoambiente_form.html'
    success_url = reverse_lazy('central_servicos:tipoambiente_list')

class TipoAmbienteDeleteView(LoginRequiredMixin, DeleteView):
    model = TipoAmbiente
    template_name = 'central_servicos/tipoambiente_confirm_delete.html'
    success_url = reverse_lazy('central_servicos:tipoambiente_list')

# ==========================================
# GESTÃO DE CATEGORIAS DE ELEMENTO CONSTRUTIVO
# ==========================================
class CategoriaElementoListView(LoginRequiredMixin, ListView):
    model = CategoriaElemento
    template_name = 'central_servicos/categoriaelemento_list.html'
    context_object_name = 'categoriaselemento'

class CategoriaElementoCreateView(LoginRequiredMixin, CreateView):
    model = CategoriaElemento
    form_class = CategoriaElementoForm
    template_name = 'central_servicos/categoriaelemento_form.html'
    success_url = reverse_lazy('central_servicos:categoriaelemento_list')

class CategoriaElementoUpdateView(LoginRequiredMixin, UpdateView):
    model = CategoriaElemento
    form_class = CategoriaElementoForm
    template_name = 'central_servicos/categoriaelemento_form.html'
    success_url = reverse_lazy('central_servicos:categoriaelemento_list')

class CategoriaElementoDeleteView(LoginRequiredMixin, DeleteView):
    model = CategoriaElemento
    template_name = 'central_servicos/categoriaelemento_confirm_delete.html'
    success_url = reverse_lazy('central_servicos:categoriaelemento_list')

# ==========================================
# GESTÃO DE TIPOS DE ELEMENTO CONSTRUTIVO
# ==========================================
class TipoElementoListView(LoginRequiredMixin, ListView):
    model = TipoElemento
    template_name = 'central_servicos/tipoelemento_list.html'
    context_object_name = 'tiposelemento'

class TipoElementoCreateView(LoginRequiredMixin, CreateView):
    model = TipoElemento
    form_class = TipoElementoForm
    template_name = 'central_servicos/tipoelemento_form.html'
    success_url = reverse_lazy('central_servicos:tipoelemento_list')

class TipoElementoUpdateView(LoginRequiredMixin, UpdateView):
    model = TipoElemento
    form_class = TipoElementoForm
    template_name = 'central_servicos/tipoelemento_form.html'
    success_url = reverse_lazy('central_servicos:tipoelemento_list')

class TipoElementoDeleteView(LoginRequiredMixin, DeleteView):
    model = TipoElemento
    template_name = 'central_servicos/tipoelemento_confirm_delete.html'
    success_url = reverse_lazy('central_servicos:tipoelemento_list')

class ElementoConstrutivoListView(LoginRequiredMixin, ListView):
    model = ElementoConstrutivo
    template_name = 'central_servicos/elementoconstrutivo_list.html'
    context_object_name = 'elementosconstrutivos'

class ElementoConstrutivoCreateView(LoginRequiredMixin, CreateView):
    model = ElementoConstrutivo
    form_class = ElementoConstrutivoForm
    template_name = 'central_servicos/elementoconstrutivo_form.html'
    success_url = reverse_lazy('central_servicos:elementoconstrutivo_list')

class ElementoConstrutivoUpdateView(LoginRequiredMixin, UpdateView):
    model = ElementoConstrutivo
    form_class = ElementoConstrutivoForm
    template_name = 'central_servicos/elementoconstrutivo_form.html'
    success_url = reverse_lazy('central_servicos:elementoconstrutivo_list')

class ElementoConstrutivoDeleteView(LoginRequiredMixin, DeleteView):
    model = ElementoConstrutivo
    template_name = 'central_servicos/elementoconstrutivo_confirm_delete.html'
    success_url = reverse_lazy('central_servicos:elementoconstrutivo_list')


class TipoAmbienteAjaxCreateView(View):
    def post(self, request, *args, **kwargs):
        nome = request.POST.get('nome')
        descricao = request.POST.get('descricao')
        if not nome:
            return JsonResponse({'success': False, 'error': 'O nome é obrigatório.'})
            
        if TipoAmbiente.objects.filter(nome__iexact=nome).exists():
            return JsonResponse({'success': False, 'error': 'Já existe um Tipo de Ambiente com este nome.'})
            
        tipo = TipoAmbiente.objects.create(nome=nome, descricao=descricao)
        return JsonResponse({'success': True, 'id': tipo.id, 'nome': tipo.nome})

class RelatoriosView(LoginRequiredMixin, TemplateView):
    template_name = 'central_servicos/relatorios.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'total_predios': Predio.objects.count(),
            'total_andares': Andar.objects.count(),
            'total_ambientes': Ambiente.objects.count(),
            'total_elementos': ElementoConstrutivo.objects.count(),
            'total_ativos': AtivoPredial.objects.count(),
            'total_tipos_ambiente': TipoAmbiente.objects.count(),
            'total_tipos_ativo': TipoAtivo.objects.count(),
            'total_categorias': CategoriaServico.objects.count(),
            'total_finalidades': Finalidade.objects.count(),
            'predios_arvore': Predio.objects.prefetch_related(
                'andares__ambientes__elementos_construtivos',
                'andares__ambientes__ativos'
            ).all()
        })
        return context


from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json

@method_decorator(csrf_exempt, name='dispatch')
class ReordenarItensView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            modelo = data.get('modelo')
            ids = data.get('ids', [])
            
            if modelo == 'Predio':
                ModelClass = Predio
            elif modelo == 'Andar':
                ModelClass = Andar
            elif modelo == 'Ambiente':
                ModelClass = Ambiente
            else:
                return JsonResponse({'error': 'Modelo inválido'}, status=400)
                
            for index, item_id in enumerate(ids):
                # We use update to avoid triggering signals/history for a simple reorder, or we can just save.
                # Let's use update to be faster and not clutter history if not strictly necessary, 
                # but if we want history, we should fetch and save. We'll use update for performance.
                ModelClass.objects.filter(id=item_id).update(ordem=index)
                
            return JsonResponse({'status': 'ok'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
