# pyrefly: ignore [untyped-import]
from django.shortcuts import render
# pyrefly: ignore [untyped-import]
from django.contrib.auth.decorators import login_required
# pyrefly: ignore [untyped-import]
from django.contrib.auth.mixins import LoginRequiredMixin
# pyrefly: ignore [untyped-import]
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
# pyrefly: ignore [untyped-import]
from django.urls import reverse_lazy
from .models import OrdemServico, Predio, Andar, Sala, AtivoPredial, CategoriaServico, MaterialUtilizado, Finalidade
from .forms import OrdemServicoForm, OrdemServicoCancelamentoForm, PredioForm, AndarForm, SalaForm, AtivoPredialForm, CategoriaServicoForm, FinalidadeForm
from django.core.exceptions import PermissionDenied
from django.contrib import messages

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
    }
    return render(request, 'central_servicos/home_central_servicos.html', context)


class OrdemServicoCreateView(LoginRequiredMixin, CreateView):
    model = OrdemServico
    form_class = OrdemServicoForm
    template_name = 'central_servicos/os_form.html'
    success_url = reverse_lazy('central_servicos:home_central_servicos')

    def form_valid(self, form):
        form.instance.solicitante = self.request.user
        return super().form_valid(form)

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
# GESTÃO DE SALAS
# ==========================================
class SalaListView(LoginRequiredMixin, ListView):
    model = Sala
    template_name = 'central_servicos/sala_list.html'
    context_object_name = 'salas'

class SalaCreateView(LoginRequiredMixin, CreateView):
    model = Sala
    form_class = SalaForm
    template_name = 'central_servicos/sala_form.html'
    success_url = reverse_lazy('central_servicos:sala_list')
    def form_valid(self, form):
        messages.success(self.request, 'Sala cadastrada com sucesso.')
        return super().form_valid(form)

class SalaUpdateView(LoginRequiredMixin, UpdateView):
    model = Sala
    form_class = SalaForm
    template_name = 'central_servicos/sala_form.html'
    success_url = reverse_lazy('central_servicos:sala_list')
    def form_valid(self, form):
        messages.success(self.request, 'Sala atualizada com sucesso.')
        return super().form_valid(form)

class SalaDeleteView(LoginRequiredMixin, DeleteView):
    model = Sala
    template_name = 'central_servicos/sala_confirm_delete.html'
    success_url = reverse_lazy('central_servicos:sala_list')
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

class AtivoPredialCreateView(LoginRequiredMixin, CreateView):
    model = AtivoPredial
    form_class = AtivoPredialForm
    template_name = 'central_servicos/ativopredial_form.html'
    success_url = reverse_lazy('central_servicos:ativopredial_list')
    def form_valid(self, form):
        messages.success(self.request, 'Ativo Predial cadastrado com sucesso.')
        return super().form_valid(form)

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
