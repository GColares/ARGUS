from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import OrdemServico, Predio, Andar, Sala, AtivoPredial, CategoriaServico, MaterialUtilizado
from .forms import OrdemServicoForm

@login_required
def dashboard(request):
    os_pendentes = OrdemServico.objects.filter(status='PENDENTE').count()
    os_em_andamento = OrdemServico.objects.filter(status='EM_ANDAMENTO').count()
    os_concluidas = OrdemServico.objects.filter(status='CONCLUIDA').count()
    ultimas_os = OrdemServico.objects.all().order_by('-data_abertura')[:10]
    
    context = {
        'os_pendentes': os_pendentes,
        'os_em_andamento': os_em_andamento,
        'os_concluidas': os_concluidas,
        'ultimas_os': ultimas_os,
    }
    
    return render(request, 'manutencao_predial/dashboard.html', context)


class OrdemServicoCreateView(LoginRequiredMixin, CreateView):
    model = OrdemServico
    form_class = OrdemServicoForm
    template_name = 'manutencao_predial/os_form.html'
    success_url = reverse_lazy('home_manutencao_predial:dashboard')

    def form_valid(self, form):
        form.instance.solicitante = self.request.user
        return super().form_valid(form)
