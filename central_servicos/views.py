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
from .permissions import AdministradorRequiredMixin, GestorInfraRequiredMixin, OperadorInfraRequiredMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
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
        try:
            with transaction.atomic():
                for ambiente in ambientes:
                    nova_os = OrdemServico(
                        ambiente=ambiente,
                        categoria=categoria,
                        descricao_problema=descricao_problema,
                        ativo_predial=ativo_predial,
                        solicitante=solicitante
                    )
                    nova_os.full_clean()
                    nova_os.save()
                    os_criadas += 1
        except ValidationError as e:
            for field, errors in getattr(e, 'message_dict', {}).items():
                for erro in errors:
                    form.add_error(field, erro)
            if hasattr(e, 'messages') and not getattr(e, 'message_dict', None):
                for erro in e.messages:
                    form.add_error(None, erro)
            return self.form_invalid(form)

        messages.success(self.request, f'{os_criadas} Ordem(ns) de Serviço gerada(s) com sucesso.')
        from django.http import HttpResponseRedirect
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
class PredioListView(GestorInfraRequiredMixin, ListView):
    model = Predio
    template_name = 'central_servicos/predio_list.html'
    context_object_name = 'predios'
    
    def get_queryset(self):
        # pyrefly: ignore [missing-attribute]
        return Predio.objects.all().order_by('nome')

class PredioCreateView(GestorInfraRequiredMixin, CreateView):
    model = Predio
    form_class = PredioForm
    template_name = 'central_servicos/predio_form.html'
    success_url = reverse_lazy('central_servicos:predio_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Prédio cadastrado com sucesso.')
        return super().form_valid(form)

class PredioUpdateView(GestorInfraRequiredMixin, UpdateView):
    model = Predio
    form_class = PredioForm
    template_name = 'central_servicos/predio_form.html'
    success_url = reverse_lazy('central_servicos:predio_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Prédio atualizado com sucesso.')
        return super().form_valid(form)

class PredioDeleteView(GestorInfraRequiredMixin, DeleteView):
    model = Predio
    template_name = 'central_servicos/predio_confirm_delete.html'
    success_url = reverse_lazy('central_servicos:predio_list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Prédio excluído com sucesso.")
        return super().delete(request, *args, **kwargs)

# ==========================================
# GESTÃO DE ANDARES
# ==========================================
class AndarListView(GestorInfraRequiredMixin, ListView):
    model = Andar
    template_name = 'central_servicos/andar_list.html'
    context_object_name = 'andares'

class AndarCreateView(GestorInfraRequiredMixin, CreateView):
    model = Andar
    form_class = AndarForm
    template_name = 'central_servicos/andar_form.html'
    success_url = reverse_lazy('central_servicos:andar_list')
    def form_valid(self, form):
        messages.success(self.request, 'Andar cadastrado com sucesso.')
        return super().form_valid(form)

class AndarUpdateView(GestorInfraRequiredMixin, UpdateView):
    model = Andar
    form_class = AndarForm
    template_name = 'central_servicos/andar_form.html'
    success_url = reverse_lazy('central_servicos:andar_list')
    def form_valid(self, form):
        messages.success(self.request, 'Andar atualizado com sucesso.')
        return super().form_valid(form)

class AndarDeleteView(GestorInfraRequiredMixin, DeleteView):
    model = Andar
    template_name = 'central_servicos/andar_confirm_delete.html'
    success_url = reverse_lazy('central_servicos:andar_list')
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Andar excluído com sucesso.')
        return super().delete(request, *args, **kwargs)

# ==========================================
# GESTÃO DE AMBIENTES
# ==========================================
class AmbienteListView(GestorInfraRequiredMixin, ListView):
    model = Ambiente
    template_name = 'central_servicos/ambiente_list.html'
    context_object_name = 'ambientes'

    def get_queryset(self):
        return Ambiente.objects.filter(ativo=True)

class AmbienteCreateView(GestorInfraRequiredMixin, CreateView):
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

class AmbienteUpdateView(GestorInfraRequiredMixin, UpdateView):
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

class AmbienteInativarView(GestorInfraRequiredMixin, DeleteView):
    model = Ambiente
    template_name = 'central_servicos/ambiente_inativar.html'
    success_url = reverse_lazy('central_servicos:ambiente_list')
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        motivo = request.POST.get('motivo_inativacao', '').strip()
        try:
            self.object.inativar(motivo=motivo, usuario=request.user)
            messages.success(request, 'Ambiente inativado (soft-delete) com sucesso.')
            from django.http import HttpResponseRedirect
            return HttpResponseRedirect(self.success_url)
        except ValidationError as e:
            messages.error(request, e.message if hasattr(e, 'message') else str(e))
            return self.render_to_response(self.get_context_data())

class AmbienteReativarView(AdministradorRequiredMixin, View):
    def post(self, request, pk):
        from django.shortcuts import get_object_or_404
        from django.http import HttpResponseRedirect
        ambiente = get_object_or_404(Ambiente, pk=pk)
        motivo = request.POST.get('motivo_reativacao', '').strip()
        try:
            ambiente.reativar(motivo=motivo, usuario=request.user)
            messages.success(request, 'Ambiente reativado com sucesso.')
        except ValidationError as e:
            messages.error(request, e.message if hasattr(e, 'message') else str(e))
        return HttpResponseRedirect(reverse_lazy('central_servicos:ambiente_list'))

# ==========================================
# GESTÃO DE ATIVOS PREDIAIS
# ==========================================
class AtivoPredialListView(OperadorInfraRequiredMixin, ListView):
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

class AmbienteAtivosOffcanvasView(OperadorInfraRequiredMixin, TemplateView):
    template_name = 'central_servicos/_ambiente_ativos_offcanvas.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ambiente_id = self.kwargs.get('ambiente_id')
        ambiente = get_object_or_404(Ambiente, pk=ambiente_id)
        context['ambiente'] = ambiente
        context['ativos'] = AtivoPredial.objects.filter(ambiente=ambiente).select_related('tipo')
        context['tipos_ativos'] = TipoAtivo.objects.all()
        return context

class AtivoPredialRapidoCreateView(OperadorInfraRequiredMixin, View):
    def post(self, request, ambiente_id):
        ambiente = get_object_or_404(Ambiente, pk=ambiente_id)
        tipo_id = request.POST.get('tipo')
        nome_apelido = request.POST.get('nome_apelido')
        patrimonio = request.POST.get('patrimonio')
        
        if tipo_id:
            tipo = get_object_or_404(TipoAtivo, pk=tipo_id)
            try:
                with transaction.atomic():
                    novo_ativo = AtivoPredial(
                        ambiente=ambiente,
                        tipo=tipo,
                        nome_apelido=nome_apelido,
                        patrimonio=patrimonio
                    )
                    novo_ativo.full_clean()
                    novo_ativo.save()
                messages.success(request, 'Ativo adicionado com sucesso!')
            except ValidationError as e:
                # Tratamento simplificado de erros para a view rápida
                erro_msg = " | ".join([f"{k}: {v[0]}" for k, v in getattr(e, 'message_dict', {}).items()])
                if not erro_msg and hasattr(e, 'messages'):
                    erro_msg = " | ".join(e.messages)
                messages.error(request, f'Erro na validação do ativo: {erro_msg}')
        else:
            messages.error(request, 'Erro: Tipo de ativo não informado.')
            
        return redirect('central_servicos:ativopredial_list')

class AtivoPredialCreateView(OperadorInfraRequiredMixin, CreateView):
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
        
        ativos_criados = 0
        try:
            with transaction.atomic():
                for ambiente in ambientes:
                    qtd_str = self.request.POST.get(f'quantidade_ambiente_{ambiente.id}')
                    try:
                        qtd = int(qtd_str) if qtd_str else 1
                    except ValueError:
                        qtd = 1
                        
                    for _ in range(qtd):
                        novo_ativo = AtivoPredial(
                            ambiente=ambiente,
                            tipo=tipo,
                            nome_apelido=nome_apelido,
                            descricao=descricao,
                            patrimonio='',
                            numero_serie=''
                        )
                        novo_ativo.full_clean()
                        novo_ativo.save()
                        ativos_criados += 1
        except ValidationError as e:
            for field, errors in getattr(e, 'message_dict', {}).items():
                for erro in errors:
                    form.add_error(field, erro)
            if hasattr(e, 'messages') and not getattr(e, 'message_dict', None):
                for erro in e.messages:
                    form.add_error(None, erro)
            return self.form_invalid(form)
            
        messages.success(self.request, f'{ativos_criados} Ativo(s) Predial(is) cadastrado(s) com sucesso.')
        from django.http import HttpResponseRedirect
        return HttpResponseRedirect(self.success_url)

class AtivoPredialUpdateView(OperadorInfraRequiredMixin, UpdateView):
    model = AtivoPredial
    form_class = AtivoPredialForm
    template_name = 'central_servicos/ativopredial_form.html'
    success_url = reverse_lazy('central_servicos:ativopredial_list')
    def form_valid(self, form):
        messages.success(self.request, 'Ativo Predial atualizado com sucesso.')
        return super().form_valid(form)

class AtivoPredialDeleteView(OperadorInfraRequiredMixin, DeleteView):
    model = AtivoPredial
    template_name = 'central_servicos/ativopredial_confirm_delete.html'
    success_url = reverse_lazy('central_servicos:ativopredial_list')
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Ativo Predial excluído com sucesso.')
        return super().delete(request, *args, **kwargs)

# ==========================================
# GESTÃO DE CATEGORIAS DE SERVIÇO
# ==========================================
class CategoriaServicoListView(GestorInfraRequiredMixin, ListView):
    model = CategoriaServico
    template_name = 'central_servicos/categoriaservico_list.html'
    context_object_name = 'categorias'

class CategoriaServicoCreateView(GestorInfraRequiredMixin, CreateView):
    model = CategoriaServico
    form_class = CategoriaServicoForm
    template_name = 'central_servicos/categoriaservico_form.html'
    success_url = reverse_lazy('central_servicos:categoriaservico_list')
    def form_valid(self, form):
        messages.success(self.request, 'Categoria cadastrada com sucesso.')
        return super().form_valid(form)

class CategoriaServicoUpdateView(GestorInfraRequiredMixin, UpdateView):
    model = CategoriaServico
    form_class = CategoriaServicoForm
    template_name = 'central_servicos/categoriaservico_form.html'
    success_url = reverse_lazy('central_servicos:categoriaservico_list')
    def form_valid(self, form):
        messages.success(self.request, 'Categoria atualizada com sucesso.')
        return super().form_valid(form)

class CategoriaServicoDeleteView(GestorInfraRequiredMixin, DeleteView):
    model = CategoriaServico
    template_name = 'central_servicos/categoriaservico_confirm_delete.html'
    success_url = reverse_lazy('central_servicos:categoriaservico_list')
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Categoria excluída com sucesso.')
        return super().delete(request, *args, **kwargs)

# ==========================================
# GESTÃO DE FINALIDADES
# ==========================================
class FinalidadeListView(GestorInfraRequiredMixin, ListView):
    model = Finalidade
    template_name = 'central_servicos/finalidade_list.html'
    context_object_name = 'finalidades'

class FinalidadeCreateView(GestorInfraRequiredMixin, CreateView):
    model = Finalidade
    form_class = FinalidadeForm
    template_name = 'central_servicos/finalidade_form.html'
    success_url = reverse_lazy('central_servicos:finalidade_list')
    def form_valid(self, form):
        messages.success(self.request, 'Finalidade cadastrada com sucesso.')
        return super().form_valid(form)

class FinalidadeUpdateView(GestorInfraRequiredMixin, UpdateView):
    model = Finalidade
    form_class = FinalidadeForm
    template_name = 'central_servicos/finalidade_form.html'
    success_url = reverse_lazy('central_servicos:finalidade_list')
    def form_valid(self, form):
        messages.success(self.request, 'Finalidade atualizada com sucesso.')
        return super().form_valid(form)

class FinalidadeDeleteView(GestorInfraRequiredMixin, DeleteView):
    model = Finalidade
    template_name = 'central_servicos/finalidade_confirm_delete.html'
    success_url = reverse_lazy('central_servicos:finalidade_list')
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Finalidade excluída com sucesso.')
        return super().delete(request, *args, **kwargs)

class TipoAtivoListView(GestorInfraRequiredMixin, ListView):
    model = TipoAtivo
    template_name = 'central_servicos/tipoativo_list.html'

class TipoAtivoCreateView(GestorInfraRequiredMixin, CreateView):
    model = TipoAtivo
    form_class = TipoAtivoForm
    template_name = 'central_servicos/tipoativo_form.html'
    success_url = reverse_lazy('central_servicos:tipoativo_list')
    def form_valid(self, form):
        messages.success(self.request, 'Tipo de Ativo cadastrado com sucesso.')
        return super().form_valid(form)

class TipoAtivoUpdateView(GestorInfraRequiredMixin, UpdateView):
    model = TipoAtivo
    form_class = TipoAtivoForm
    template_name = 'central_servicos/tipoativo_form.html'
    success_url = reverse_lazy('central_servicos:tipoativo_list')
    def form_valid(self, form):
        messages.success(self.request, 'Tipo de Ativo atualizado com sucesso.')
        return super().form_valid(form)

class TipoAtivoDeleteView(GestorInfraRequiredMixin, DeleteView):
    model = TipoAtivo
    template_name = 'central_servicos/tipoativo_confirm_delete.html'
    success_url = reverse_lazy('central_servicos:tipoativo_list')
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Tipo de Ativo excluído com sucesso.')
        return super().delete(request, *args, **kwargs)

class TipoAmbienteListView(GestorInfraRequiredMixin, ListView):
    model = TipoAmbiente
    template_name = 'central_servicos/tipoambiente_list.html'
    context_object_name = 'tiposambiente'

class TipoAmbienteCreateView(GestorInfraRequiredMixin, CreateView):
    model = TipoAmbiente
    form_class = TipoAmbienteForm
    template_name = 'central_servicos/tipoambiente_form.html'
    success_url = reverse_lazy('central_servicos:tipoambiente_list')

class TipoAmbienteUpdateView(GestorInfraRequiredMixin, UpdateView):
    model = TipoAmbiente
    form_class = TipoAmbienteForm
    template_name = 'central_servicos/tipoambiente_form.html'
    success_url = reverse_lazy('central_servicos:tipoambiente_list')

class TipoAmbienteDeleteView(GestorInfraRequiredMixin, DeleteView):
    model = TipoAmbiente
    template_name = 'central_servicos/tipoambiente_confirm_delete.html'
    success_url = reverse_lazy('central_servicos:tipoambiente_list')

# ==========================================
# GESTÃO DE CATEGORIAS DE ELEMENTO CONSTRUTIVO
# ==========================================
class CategoriaElementoListView(GestorInfraRequiredMixin, ListView):
    model = CategoriaElemento
    template_name = 'central_servicos/categoriaelemento_list.html'
    context_object_name = 'categoriaselemento'

class CategoriaElementoCreateView(GestorInfraRequiredMixin, CreateView):
    model = CategoriaElemento
    form_class = CategoriaElementoForm
    template_name = 'central_servicos/categoriaelemento_form.html'
    success_url = reverse_lazy('central_servicos:categoriaelemento_list')

class CategoriaElementoUpdateView(GestorInfraRequiredMixin, UpdateView):
    model = CategoriaElemento
    form_class = CategoriaElementoForm
    template_name = 'central_servicos/categoriaelemento_form.html'
    success_url = reverse_lazy('central_servicos:categoriaelemento_list')

class CategoriaElementoDeleteView(GestorInfraRequiredMixin, DeleteView):
    model = CategoriaElemento
    template_name = 'central_servicos/categoriaelemento_confirm_delete.html'
    success_url = reverse_lazy('central_servicos:categoriaelemento_list')

# ==========================================
# GESTÃO DE TIPOS DE ELEMENTO CONSTRUTIVO
# ==========================================
class TipoElementoListView(GestorInfraRequiredMixin, ListView):
    model = TipoElemento
    template_name = 'central_servicos/tipoelemento_list.html'
    context_object_name = 'tiposelemento'

class TipoElementoCreateView(GestorInfraRequiredMixin, CreateView):
    model = TipoElemento
    form_class = TipoElementoForm
    template_name = 'central_servicos/tipoelemento_form.html'
    success_url = reverse_lazy('central_servicos:tipoelemento_list')

class TipoElementoUpdateView(GestorInfraRequiredMixin, UpdateView):
    model = TipoElemento
    form_class = TipoElementoForm
    template_name = 'central_servicos/tipoelemento_form.html'
    success_url = reverse_lazy('central_servicos:tipoelemento_list')

class TipoElementoDeleteView(GestorInfraRequiredMixin, DeleteView):
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
import json

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
