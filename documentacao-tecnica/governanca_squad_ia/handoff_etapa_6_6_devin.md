# Handoff Cirúrgico de Engenharia — Fase 6 / Etapa 6.6
## Máquina de Estados e Governança do Ciclo de Vida de Projetos PDI (RF-05, RF-06 e Gateways SoD)

> **Destinatário:** Devin Desktop (Desenvolvedor Autônomo & Refatorador)  
> **Autor / Tech Lead:** Antigravity-Gemini (Arquiteto de Software)  
> **Revisor Red Team:** GitHub Copilot (VS Code)  
> **Status Atual do Repositório:** Baseline de **192/192 testes verdes (100% OK)**.  
> **Meta da Etapa 6.6:** **200/200 testes verdes (+8 testes unitários, 0 regressões)**.

---

## 1. Contexto Regulatório e Regras da Máquina de Estados (SoD)

Conforme a **Lei 10.973/2004**, **Lei 4.320/1964**, **Manual EMBRAPII** e a revisão crítica do Red Team:
1. **Auditoria Persistente Obrigatória (`HistoricoTransicaoFase`):** Nenhuma transição de fase ocorre sem registrar permanentemente no banco: `projeto`, `usuario`, `fase_anterior`, `fase_nova`, `data_transicao` e `justificativa`.
2. **Anti-Bypass no `save()`:** É proibido alterar diretamente o atributo `projeto.fase = ...; projeto.save()` burlando os gateways de validação. Mudanças de fase exigem obrigatoriamente a invocação do método oficial `projeto.transicionar_fase(nova_fase, usuario, justificativa)`.
3. **Gateway 1 (`PROSPECCAO` ➔ `EXECUCAO`):**
   - Exige Termo de Parceria formalizado: `ativo=True`, `numero` preenchido, `data_assinatura` preenchida e partícipes qualificados (`concedente`, `convenente`, `interveniente`).
   - Exige Plano de Trabalho com Macroentregas cadastradas (`plano.macroentregas.exists()`).
   - Exige pelo menos uma Conta Bancária cadastrada para o projeto.
   - *Efeito Colateral:* Ao entrar em `EXECUCAO`, o sistema ativa a trava `esta_congelado` do `PlanoDeTrabalho` (RN-10).
4. **Gateway 2 (`EXECUCAO` ➔ `PRESTACAO_CONTAS`):**
   - Transição técnica legítima ao concluir as macroentregas.
5. **Gateway 3 (`PRESTACAO_CONTAS` ➔ `ENCERRADO`):**
   - Exige que todas as parcelas de bolsas vinculadas ao projeto estejam com status `PAGO` ou `CANCELADO`. Se houver parcelas pendentes ou em análise, a transição é bloqueada.
6. **Cancelamento (`CANCELADO`):**
   - Permitido apenas a partir de `PROSPECCAO` ou `EXECUCAO` (projetos em `PRESTACAO_CONTAS` ou `ENCERRADO` não podem ser cancelados).
   - Exige obrigatoriamente `justificativa` não-vazia.
7. **Estados Terminais & Idempotência:**
   - `ENCERRADO` e `CANCELADO` são estados terminais; tentativas de transição a partir deles são bloqueadas.
   - Transição para a mesma fase (ex: `EXECUCAO` ➔ `EXECUCAO`) é rejeitada.
8. **RBAC Estrito na View:**
   - Apenas Superusuários, o Coordenador do Projeto (`projeto.coordenador.user == request.user`) ou membros da equipe (`MembroEquipe`) com papel `COORDENADOR` ou `GESTOR` daquele projeto específico podem executar a transição (demais recebem 403 `HttpResponseForbidden`).

---

## 2. Arquivos Autorizados para Edição (SoD)

1. `cadastros/models.py`
2. `cadastros/views.py`
3. `cadastros/urls.py`
4. `cadastros/templates/cadastros/visualizar_projeto.html`
5. `cadastros/tests.py`

---

## 3. Especificação Cirúrgica das Alterações

### 3.1. `cadastros/models.py`

#### A. Criar o modelo `HistoricoTransicaoFase`:
```python
class HistoricoTransicaoFase(models.Model):
    """Rastro de auditoria indelével para a máquina de estados do Projeto PDI."""
    projeto = models.ForeignKey('ProjetoPDI', on_delete=models.CASCADE, related_name='historico_fases')
    usuario = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name="Responsável pela Transição")
    fase_anterior = models.CharField(max_length=20, choices=ProjetoPDI.FASE_CHOICES)
    fase_nova = models.CharField(max_length=20, choices=ProjetoPDI.FASE_CHOICES)
    data_transicao = models.DateTimeField(auto_now_add=True, verbose_name="Data/Hora da Transição")
    justificativa = models.TextField(blank=True, null=True, verbose_name="Justificativa / Parecer")

    class Meta:
        verbose_name = "Histórico de Transição de Fase"
        verbose_name_plural = "Histórico de Transições de Fases"
        ordering = ['-data_transicao']

    def __str__(self):
        return f"{self.projeto.nome}: {self.fase_anterior} -> {self.fase_nova} ({self.data_transicao.strftime('%d/%m/%Y %H:%M')})"
```

#### B. No modelo `ProjetoPDI`:
1. Implementar `validar_transicao_fase(self, nova_fase, justificativa=None)`:
```python
    def validar_transicao_fase(self, nova_fase, justificativa=None):
        """Valida os gateways regulatórios e retorna lista de pendências impeditivas."""
        pendencias = []
        fase_atual = self.fase

        if nova_fase == fase_atual:
            pendencias.append(f"O projeto já se encontra na fase {self.get_fase_display()}.")
            return pendencias

        if fase_atual in ['ENCERRADO', 'CANCELADO']:
            pendencias.append(f"O projeto está em estado terminal ({self.get_fase_display()}) e não admite novas transições.")
            return pendencias

        if nova_fase == 'CANCELADO':
            if fase_atual not in ['PROSPECCAO', 'EXECUCAO']:
                pendencias.append("Projetos em fase de Prestação de Contas ou Encerrados não podem ser cancelados.")
            if not justificativa or not justificativa.strip():
                pendencias.append("O cancelamento de um projeto exige justificativa formal fundamentada.")
            return pendencias

        # Gateway 1: PROSPECCAO -> EXECUCAO
        if fase_atual == 'PROSPECCAO' and nova_fase == 'EXECUCAO':
            termo = self.termo_parceria
            if not termo or not termo.ativo or not termo.numero or not termo.data_assinatura:
                pendencias.append("Exige Termo de Parceria ativo, numerado e formalmente assinado.")
            if not termo or not termo.concedente or not termo.convenente or not termo.interveniente:
                pendencias.append("Exige a qualificação completa dos partícipes (Concedente, Convenente e Interveniente).")
            
            plano = self.planos_trabalho.filter(ativo=True).first() or (termo.planos_trabalho.first() if termo else None)
            if not plano or not plano.macroentregas.exists():
                pendencias.append("Exige Plano de Trabalho com Macroentregas cadastradas.")
            if not self.contas.exists():
                pendencias.append("Exige pelo menos uma Conta Bancária vinculada ao projeto.")

        # Gateway 2: EXECUCAO -> PRESTACAO_CONTAS
        elif fase_atual == 'EXECUCAO' and nova_fase == 'PRESTACAO_CONTAS':
            pass

        # Gateway 3: PRESTACAO_CONTAS -> ENCERRADO
        elif fase_atual == 'PRESTACAO_CONTAS' and nova_fase == 'ENCERRADO':
            from cadastros.models import Parcela
            parcelas_pendentes = Parcela.objects.filter(
                termo_bolsa__cota_pt__projeto=self
            ).exclude(status__in=['PAGO', 'CANCELADO'])
            if parcelas_pendentes.exists():
                pendencias.append(f"Existem {parcelas_pendentes.count()} parcelas de bolsas não liquidadas (devem estar Pagas ou Canceladas).")

        else:
            pendencias.append(f"Transição inválida: não é permitido saltar de {self.get_fase_display()} diretamente para {nova_fase}.")

        return pendencias
```

2. Implementar `transicionar_fase(self, nova_fase, usuario, justificativa=None)`:
```python
    def transicionar_fase(self, nova_fase, usuario, justificativa=None):
        """Executa a transição atômica registrando rastro indelével de auditoria."""
        pendencias = self.validar_transicao_fase(nova_fase, justificativa)
        if pendencias:
            from django.core.exceptions import ValidationError
            raise ValidationError(pendencias)

        from django.db import transaction
        with transaction.atomic():
            fase_anterior = self.fase
            self._permitir_mudanca_fase = True
            self.fase = nova_fase
            self.save()

            HistoricoTransicaoFase.objects.create(
                projeto=self,
                usuario=usuario,
                fase_anterior=fase_anterior,
                fase_nova=nova_fase,
                justificativa=justificativa
            )
```

3. Atualizar `save(self, *args, **kwargs)` com trava anti-bypass:
```python
    def save(self, *args, **kwargs):
        if self.pk:
            original = ProjetoPDI.objects.filter(pk=self.pk).values('fase').first()
            if original and original['fase'] != self.fase and not getattr(self, '_permitir_mudanca_fase', False):
                from django.core.exceptions import ValidationError
                raise ValidationError("A fase do projeto só pode ser alterada através do método oficial transicionar_fase().")
        super().save(*args, **kwargs)
```

---

### 3.2. `cadastros/views.py`

Criar a view `transicionar_fase_projeto(request, projeto_id)`:
- Apenas `POST`.
- **RBAC Estrito:**
  ```python
  tem_permissao = False
  if request.user.is_superuser:
      tem_permissao = True
  elif projeto.coordenador and projeto.coordenador.user_id == request.user.pk:
      tem_permissao = True
  elif MembroEquipe.objects.filter(projeto=projeto, usuario=request.user, papel__in=['COORDENADOR', 'GESTOR']).exists():
      tem_permissao = True

  if not tem_permissao:
      return HttpResponseForbidden("Acesso negado: Apenas a coordenação ou gestores deste projeto podem alterar sua fase.")
  ```
- Recebe `nova_fase` e `justificativa`.
- Invoca `projeto.transicionar_fase(nova_fase, request.user, justificativa)`.
- Se ocorrer `ValidationError`: captura e exibe `messages.error(request, ...)` para cada pendência.
- Se sucesso: `messages.success(request, f"Projeto transicionado com sucesso para {projeto.get_fase_display()}!")`.
- Redireciona para `cadastros:visualizar_projeto`.

---

### 3.3. `cadastros/urls.py`
Registrar:
```python
path('projeto/<int:projeto_id>/transicionar-fase/', views.transicionar_fase_projeto, name='transicionar_fase_projeto'),
```

---

### 3.4. `cadastros/templates/cadastros/visualizar_projeto.html`
- Inserir logo acima das abas um **Stepper do Ciclo de Vida do Projeto** no Padrão Almoxarifado / Design System:
  - Fases: `Prospecção`, `Execução`, `Prestação de Contas`, `Encerrado`.
  - A fase atual em destaque com cor semântica e ícone.
- Botão de Ação no cabeçalho ou no card da fase:
  - Se `PROSPECCAO`: Botão verde `<i class="fas fa-play me-1"></i> Iniciar Execução do Projeto` (abre modal de confirmação alertando sobre o congelamento de escopo).
  - Se `EXECUCAO`: Botão azul `<i class="fas fa-forward me-1"></i> Concluir e Iniciar Prestação de Contas`.
  - Se `PRESTACAO_CONTAS`: Botão escuro `<i class="fas fa-check-double me-1"></i> Homologar Encerramento`.
  - Botão discreto `Cancelar Projeto` (disponível apenas em `PROSPECCAO` ou `EXECUCAO`, com modal exigindo justificativa).

---

### 3.5. `cadastros/tests.py`

Criar a suíte `CicloVidaProjetoTestCase(TestCase)` com **8 testes rigorosos**:
1. `test_01_gateway_execucao_sem_termo_ou_plano_bloqueado`: Valida que pendências impedem transição para `EXECUCAO`.
2. `test_02_gateway_execucao_com_sucesso_ativa_congelamento`: Transiciona para `EXECUCAO`, cria `HistoricoTransicaoFase` e valida `plano.esta_congelado == True`.
3. `test_03_anti_bypass_save_direto_bloqueado`: Tentar fazer `projeto.fase = 'ENCERRADO'; projeto.save()` gera `ValidationError`.
4. `test_04_gateway_encerrado_bloqueia_se_houver_parcelas_pendentes`: Rejeita transição para `ENCERRADO` se houver parcela com status `EM_ANALISE` ou `APROVADO`.
5. `test_05_gateway_encerrado_sucesso_quando_parcelas_pagas`: Permite encerramento quando todas as parcelas do projeto estão `PAGO`.
6. `test_06_cancelamento_exige_justificativa_e_salva_historico`: Cancelamento sem justificativa falha; com justificativa salva no `HistoricoTransicaoFase`.
7. `test_07_estados_terminais_bloqueiam_novas_transicoes`: Projeto `ENCERRADO` ou `CANCELADO` rejeita qualquer transição subsequente.
8. `test_08_rbac_estrito_view_transicionar_fase`: Coordenador/Gestor do projeto consegue transicionar via POST; usuário alheio ao projeto recebe `403 Forbidden`.

---

## 4. Comandos de Homologação
```powershell
python manage.py makemigrations cadastros
python manage.py migrate
python manage.py check
python manage.py test cadastros.tests.CicloVidaProjetoTestCase
python manage.py test
```
* **Critério de Aceite:** 192 ➔ **200 testes aprovados (100% verde, 0 falhas, 0 regressões)**.
