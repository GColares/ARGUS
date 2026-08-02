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
from .models import OrdemServico, Predio, Andar, Sala, AtivoPredial, CategoriaServico, MaterialUtilizado
from .forms import OrdemServicoForm

@login_required
def dashboard(request):
    # pyrefly: ignore [missing-attribute]
    os_pendentes = OrdemServico.objects.filter(status='PENDENTE').count()
    # pyrefly: ignore [missing-attribute]
    os_em_andamento = OrdemServico.objects.filter(status='EM_ANDAMENTO').count()
    # pyrefly: ignore [missing-attribute]
    os_concluidas = OrdemServico.objects.filter(status='CONCLUIDA').count()
    # pyrefly: ignore [missing-attribute]
    ultimas_os = OrdemServico.objects.all().order_by('-data_abertura')[:10]
    
    context = {
        'os_pendentes': os_pendentes,
        'os_em_andamento': os_em_andamento,
        'os_concluidas': os_concluidas,
        'ultimas_os': ultimas_os,
    }
    
    return render(request, 'central_servicos/dashboard.html', context)


class OrdemServicoCreateView(LoginRequiredMixin, CreateView):
    model = OrdemServico
    form_class = OrdemServicoForm
    template_name = 'central_servicos/os_form.html'
    success_url = reverse_lazy('central_servicos:dashboard')

    def form_valid(self, form):
        form.instance.solicitante = self.request.user
        return super().form_valid(form)
