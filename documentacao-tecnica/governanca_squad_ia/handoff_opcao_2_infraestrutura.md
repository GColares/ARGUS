# Handoff de Implementação: Opção 2 (RF-14 - Infraestrutura e Espaços Físicos)

**Destinatário:** Squad IA de Implementação (Claude Desktop / Devin)
**Autor:** Antigravity / Arquiteto Sênior (revisado por GitHub Copilot)
**Status dos Testes Atuais:** 100% OK (Base inicial)

## Resumo Arquitetural
A missão é refatorar e blindar o modelo de Infraestrutura (`central_servicos`), implementando o **Composite Pattern com proteção relacional** e um robusto mecanismo de **Soft-Delete no Domínio**. Adicionalmente, toda a manipulação do histórico espacial e manutenções passará por uma governança restrita via **RBAC**.

O planejamento foi rigorosamente revisado, e você **deve** implementar as camadas abaixo exatamente como descritas para fechar os *bypasses* de ORM e aderir ao padrão do projeto ARGUS.

---

## Passo a Passo para a Implementação

### 1. Camada de Modelos e Banco de Dados (`central_servicos/models.py`)

1. **Alterar ForeignKeys para PROTECT:**
   - Em `Ambiente`, altere `ambiente_pai` para `on_delete=models.PROTECT`.
   - Em `ElementoConstrutivo`, altere `ambiente` para `on_delete=models.PROTECT`.

2. **Adicionar Auditoria de Inativação em `Ambiente`:**
   ```python
   motivo_inativacao = models.TextField(blank=True, null=True, verbose_name="Motivo da Inativação / Mutação")
   inativado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='ambientes_inativados')
   data_inativacao = models.DateTimeField(blank=True, null=True)
   ```

3. **Propriedades e Regras de Negócio em `Ambiente`:**
   - `@property def is_folha(self): return not self.sub_ambientes.filter(ativo=True).exists()`

4. **Transações de Ciclo de Vida em `Ambiente`:**
   ```python
   def inativar(self, motivo, usuario):
       if not motivo:
           raise ValidationError("O motivo da inativação é obrigatório.")
       if not usuario:
           raise ValidationError("O usuário responsável pela inativação é obrigatório.")
       
       with transaction.atomic():
           self.ativo = False
           self.motivo_inativacao = motivo
           self.inativado_por = usuario
           self.data_inativacao = timezone.now()
           self.save()
           
           for filho in self.sub_ambientes.filter(ativo=True):
               filho.inativar(f"Inativado em cascata pelo ambiente pai. Motivo: {motivo}", usuario)

   def reativar(self, motivo, usuario):
       if not motivo or not usuario:
           raise ValidationError("Motivo e usuário são obrigatórios para reativação.")
       # Restaura APENAS o nó atual
       self.ativo = True
       self.motivo_inativacao = f"Reativado: {motivo}"
       self.data_inativacao = None
       self.save()
   ```

5. **Sobrescrever `delete()` em `Ambiente`:**
   ```python
   def delete(self, using=None, keep_parents=False, hard_delete=False, user=None, motivo=None):
       if not hard_delete:
           if not motivo:
               motivo = "Inativação (Soft-Delete) solicitada pelo sistema."
           self.inativar(motivo, user)
           return (1, {'central_servicos.Ambiente': 1})
       else:
           # Permite exclusão física (gerará ProtectedError se houver filhos, devido ao PROTECT)
           # A view deverá validar is_superuser / group admin antes de chamar hard_delete=True
           return super().delete(using=using, keep_parents=keep_parents)
   ```

6. **Validações no `clean()` para Compatibilidade e Legado:**
   - **`AtivoPredial.clean()`:** Se `not self.pk` (novo) ou `ambiente_id` alterado, validar `self.ambiente.ativo` e `self.ambiente.is_folha`.
   - **`OrdemServico.clean()`:** Se novo ou `ambiente` alterado, validar que o ambiente está ativo e é folha. Adicionalmente: se houver `self.ativo_predial`, verificar rigorosamente se `self.ativo_predial.ambiente == self.ambiente`.
   *NOTA: Para tolerância ao legado, instâncias antigas já gravadas no banco não devem lançar erro apenas por terem macro-ambientes se não sofrerem alteração nesses campos.*

### 2. Governança e RBAC (`central_servicos/permissions.py` e `views.py`)

1. **Criar `central_servicos/permissions.py`:**
   Implementar as funções `is_administrador(user)`, `is_gestor_infraestrutura(user)`, e mixins:
   - `AdministradorRequiredMixin` (para exclusão física e reativação).
   - `GestorInfraRequiredMixin` (criação de prédios, andares, inativação de ambiente).
   - `OperadorInfraRequiredMixin` (cadastro de ativos, OSs).

2. **Garantir `full_clean()` em Views de Criação Customizadas (`views.py` e Forms):**
   - Na `OrdemServicoCreateView` e em views em lote (onde ocorre um `for` invocando `OrdemServico.objects.create(...)`), a instância criada *deve* invocar `.full_clean()` antes de salvar ou estar totalmente validada no backend para evitar que o `objects.create()` evite as regras de domínio. O código atual da OS iterando sobre "ambientes" (linha 69-82) deve validar ou falhar no formulário.

3. **Views de Inativação e Reativação:**
   - Criar `AmbienteInativarView` (FormView): pede o motivo e chama `ambiente.inativar(motivo, request.user)`.
   - Criar `AmbienteReativarView`.
   - O `AmbienteDeleteView` legado pode ser removido, sendo substituído por esses dois.

### 3. Padrão Visual (Almoxarifado)

1. **`ambiente_list.html`**:
   - Cabeçalho Flexbox com `javascript:history.back()`.
   - Adicionar badge com o total e um Dropdown de Filtro ("Apenas Ativos", "Histórico Completo").
   - Cabeçalhos de tabela devem possuir classe `.text-center`.

2. **`ambiente_inativar.html`**:
   - Formulário amigável de inativação contendo campo obrigatório `motivo_inativacao`.

### 4. Bateria de Testes (`central_servicos/tests.py`)

Adicione uma classe `AmbienteEspacosFisicosTestCase` cobrindo 11 testes essenciais:
1. `test_exclusao_fisica_pai_com_filho_dispara_protect`
2. `test_inativacao_pai_inativa_subarvore_transacional`
3. `test_inativacao_preserva_vinculo_os_e_ativos` (sem `SET_NULL`)
4. `test_ambiente_inativo_rejeitado_em_novos_ativos_e_os`
5. `test_ativo_vinculado_a_macro_ambiente_rejeitado`
6. `test_ativo_incompativel_com_ambiente_rejeitado_na_os`
7. `test_views_rapidas_aplicam_trava_de_folha`
8. `test_rbac_usuario_comum_bloqueado_em_criacao_edicao_ambiente`
9. `test_rbac_gestor_infraestrutura_autorizado`
10. `test_rbac_administrador_reativa_ambiente_com_auditoria`
11. `test_listagem_historico_completo_inclui_inativos`

**Regra de Ouro:** O repositório deve manter 100% de testes passando (0 erros) após suas alterações.
