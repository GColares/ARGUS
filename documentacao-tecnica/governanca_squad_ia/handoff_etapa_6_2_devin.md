# Handoff Cirúrgico de Engenharia — Fase 6 / Etapa 6.2
## Trava Regulatória de Bens de Capital EMBRAPII na Incorporação Patrimonial (RN-06)

> **Destinatário:** Devin Desktop (Engenheiro de Backend / Implementador)  
> **Autor / Tech Lead:** Antigravity-Gemini (Arquiteto de Software)  
> **Revisor Independente (Red Team):** DeepSeek (LM Studio / Bionic)  
> **Status do Repositório:** Baseline de **161/161 testes verdes**.  
> **Meta da Etapa 6.2:** **168/168 testes verdes (0 regressões, 100% de aprovação)**.

---

## 1. Contexto Regulatório e Regra de Negócio (RN-06)

Conforme a **Portaria SUFRAMA 9835/2022** e o **Manual de Operações da EMBRAPII**:
* Recursos de subvenção econômica governamental (**EMBRAPII** e **SEBRAE**) destinam-se exclusivamente a **Custeio** (bolsas, RH direto/indireto, material de consumo, diárias e viagens).
* É **TERMINANTEMENTE PROIBIDA** a aquisição de **Bens de Capital, Equipamentos, Máquinas ou Ativos Permanentes** com recursos da EMBRAPII ou SEBRAE.
* Bens patrimoniais só podem ser adquiridos com recursos da **Empresa Parceira** ou contrapartida da ICT.

---

## 2. Arquivos Estritamente Liberados para Edição (SoD)

Apenas os 5 arquivos a seguir estão autorizados para modificação:
1. `cadastros/models.py`
2. `incorporacao/models.py`
3. `patrimonio/models.py`
4. `patrimonio/views.py`
5. `incorporacao/tests.py`

---

## 3. Especificação Cirúrgica das Alterações

### 3.1. `cadastros/models.py`
No modelo `Processo` (aproximadamente linha 984):
1. Adicionar o campo `conta_bancaria`:
   ```python
   conta_bancaria = models.ForeignKey(
       'ContaBancaria',
       on_delete=models.SET_NULL,
       null=True,
       blank=True,
       related_name='processos',
       verbose_name="Conta Bancária Pagadora"
   )
   ```
2. No método `clean(self)` de `Processo`, adicionar a consistência de projeto e a trava contra **Mutação Posterior (*Anti-Tampering*)**:
   ```python
   # Validação de consistência com o projeto
   if self.conta_bancaria and self.projeto_id:
       if self.conta_bancaria.projeto_id != self.projeto_id:
           raise ValidationError({
               'conta_bancaria': "A conta bancária informada deve pertencer ao mesmo projeto do processo."
           })

   # RN-06: Proteção contra mutação posterior (Post-Hoc Tampering)
   # Se o processo já estiver vinculado a itens patrimoniais (compra ou pagamento),
   # não pode ter sua conta alterada para EMBRAPII ou SEBRAE.
   if self.pk and self.conta_bancaria and self.conta_bancaria.fonte_recurso:
       if self.conta_bancaria.fonte_recurso.nome in ['EMBRAPII', 'SEBRAE']:
           tem_itens_comprados = hasattr(self, 'itens_comprados') and self.itens_comprados.exists()
           tem_itens_pagos = hasattr(self, 'itens_pagos') and self.itens_pagos.exists()
           if tem_itens_comprados or tem_itens_pagos:
               raise ValidationError({
                   'conta_bancaria': "RN-06: Este processo está vinculado a bens de capital/patrimoniais e não pode ser associado a uma conta da EMBRAPII ou SEBRAE."
               })
   ```

---

### 3.2. `incorporacao/models.py`
1. No modelo `ItemPatrimonial` (linha ~39):
   Adicionar o campo `conta_bancaria`:
   ```python
   conta_bancaria = models.ForeignKey(
       'cadastros.ContaBancaria',
       on_delete=models.SET_NULL,
       null=True,
       blank=True,
       related_name='itens_patrimoniais',
       verbose_name="Conta Bancária de Débito"
   )
   ```
2. Adicionar o método `clean(self)` em `ItemPatrimonial`:
   ```python
   def clean(self):
       super().clean()
       from django.core.exceptions import ValidationError

       # 1. Consistência de Projeto
       if self.conta_bancaria and hasattr(self, 'termo') and self.termo and self.termo.projeto_id:
           if self.conta_bancaria.projeto_id != self.termo.projeto_id:
               raise ValidationError({
                   'conta_bancaria': "A conta bancária debitada deve pertencer ao mesmo projeto do Termo de Doação."
               })

       # 2. RN-06: Trava de Conta Direta
       if self.conta_bancaria and self.conta_bancaria.fonte_recurso:
           if self.conta_bancaria.fonte_recurso.nome in ['EMBRAPII', 'SEBRAE']:
               raise ValidationError({
                   'conta_bancaria': "RN-06: Recursos de subvenção da EMBRAPII ou SEBRAE não podem ser utilizados para aquisição de Bens de Capital."
               })

       # 3. RN-06: Trava de Processo de Compra
       if self.processo_compra and self.processo_compra.conta_bancaria and self.processo_compra.conta_bancaria.fonte_recurso:
           if self.processo_compra.conta_bancaria.fonte_recurso.nome in ['EMBRAPII', 'SEBRAE']:
               raise ValidationError({
                   'processo_compra': "RN-06: O processo de compra está associado a uma conta EMBRAPII/SEBRAE, o que é vedado para bens patrimoniais."
               })
   ```
3. Adicionar o **Signal Bidirecional `m2m_changed`** ao final de `incorporacao/models.py`:
   ```python
   from django.db.models.signals import m2m_changed
   from django.dispatch import receiver
   from django.core.exceptions import ValidationError

   @receiver(m2m_changed, sender=ItemPatrimonial.processos_pagamento.through)
   def validar_processos_pagamento_item_patrimonial(sender, instance, action, reverse, pk_set, **kwargs):
       """
       RN-06: Impede a vinculação de processos custeados por contas EMBRAPII/SEBRAE a bens patrimoniais.
       Trata tanto a direção direta (item.processos_pagamento.add) quanto a reversa (processo.itens_pagos.add).
       """
       if action == 'pre_add':
           if not pk_set:
               return

           from cadastros.models import Processo

           # 1. Direção Direta: instance é ItemPatrimonial, pk_set são IDs de Processo
           if not reverse:
               processos_vedados = Processo.objects.filter(
                   pk__in=pk_set,
                   conta_bancaria__fonte_recurso__nome__in=['EMBRAPII', 'SEBRAE']
               )
               if processos_vedados.exists():
                   raise ValidationError(
                       "RN-06: Vedação regulatória: não é permitido associar processos de pagamento "
                       "custeados por contas da EMBRAPII ou SEBRAE a bens de capital."
                   )

           # 2. Direção Reversa: instance é Processo, pk_set são IDs de ItemPatrimonial
           else:
               processo = instance
               if processo.conta_bancaria and processo.conta_bancaria.fonte_recurso:
                   if processo.conta_bancaria.fonte_recurso.nome in ['EMBRAPII', 'SEBRAE']:
                       raise ValidationError(
                           "RN-06: Vedação regulatória: este processo está vinculado a uma conta "
                           "EMBRAPII/SEBRAE e não pode receber a vinculação de bens patrimoniais."
                       )
   ```

---

### 3.3. `patrimonio/models.py`
No modelo `BemPatrimonial` (linha ~66):
1. Adicionar o campo `conta_bancaria`:
   ```python
   conta_bancaria = models.ForeignKey(
       'cadastros.ContaBancaria',
       on_delete=models.SET_NULL,
       null=True,
       blank=True,
       related_name='bens_patrimoniais',
       verbose_name="Conta Bancária Pagadora"
   )
   ```
2. Adicionar o método `clean(self)`:
   ```python
   def clean(self):
       super().clean()
       from django.core.exceptions import ValidationError

       if self.conta_bancaria and self.conta_bancaria.fonte_recurso:
           if self.conta_bancaria.fonte_recurso.nome in ['EMBRAPII', 'SEBRAE']:
               raise ValidationError({
                   'conta_bancaria': "RN-06: Bens de capital não podem ser custeados com recursos da conta EMBRAPII ou SEBRAE."
               })
   ```

---

### 3.4. `patrimonio/views.py`
Na view `confirmar_importacao(request, verificacao_id)` (linha ~415):
Adicionar a verificação regulatória antes de criar os `BemPatrimonial`:
```python
    from cadastros.models import ContaBancaria

    for item in itens_temporarios:
        projeto = ProjetoPDI.objects.filter(codigo=item.projeto).first() or ProjetoPDI.objects.filter(status='ATIVO').first()
        termo = TermoDoacao.objects.filter(numero=item.documento).first()

        # RN-06: Rastreamento e verificação da conta bancária de débito
        conta_obj = None
        if item.conta and item.conta != 'pendente':
            conta_obj = ContaBancaria.objects.filter(conta=item.conta, projeto=projeto).first()
            if not conta_obj:
                conta_obj = ContaBancaria.objects.filter(conta=item.conta).first()

        if conta_obj and conta_obj.fonte_recurso and conta_obj.fonte_recurso.nome in ['EMBRAPII', 'SEBRAE']:
            messages.error(
                request,
                f"RN-06 Violação Regulatória: O item '{item.descricao[:40]}' está associado à conta {item.conta} "
                f"da fonte {conta_obj.fonte_recurso.nome}. Bens de capital não podem ser adquiridos com recursos de subvenção."
            )
            return redirect('patrimonio:conferir_importacao', verificacao_id=verificacao.id)

        bens_para_criar.append(BemPatrimonial(
            patrimonio_doador=item.numero_ativo,
            descricao=item.descricao,
            valor=item.valor_bem,
            projeto=projeto,
            termo_doacao=termo,
            nota_fiscal=item.nota_fiscal,
            conta_bancaria=conta_obj,
            estado_conservacao='NOVO',
            status_operacional='ATIVO'
        ))
```

---

### 3.5. `incorporacao/tests.py`
Adicionar ao final de `incorporacao/tests.py` a classe de testes `TravaCapitalEmbrapiiTestCase` com os 7 testes a seguir:

```python
from django.core.exceptions import ValidationError
from cadastros.models import (
    FonteDeRecurso, ContaBancaria, Processo, TipoProcesso,
    TermoDoacao, OrigemDoacao
)
from incorporacao.models import ItemPatrimonial


class TravaCapitalEmbrapiiTestCase(TestCase):
    """
    Bateria de testes de conformidade regulatória para a RN-06:
    Vedação absoluta de aquisição de Bens de Capital com recursos de subvenção EMBRAPII/SEBRAE.
    """
    def setUp(self):
        self.empresa = EmpresaParceira.objects.create(
            nome="Empresa Teste Capital",
            cnpj="11.222.333/0001-44",
            natureza_juridica="LTDA",
            representante_legal="Gestor Empresa",
            cargo_representante="Diretor",
        )
        self.projeto = ProjetoPDI.objects.create(
            nome="Projeto PD&I Automação",
            fase="EXECUCAO",
            concedente=self.empresa,
        )
        self.origem = OrigemDoacao.objects.create(nome="FAEPI", sigla="FAEPI")
        self.termo = TermoDoacao.objects.create(
            projeto=self.projeto,
            origem=self.origem,
            numero="TD-001",
            ano="2026",
            data="2026-01-15",
        )
        self.tipo_proc = TipoProcesso.objects.create(nome="Compras e Pagamentos")

        # Fontes de Recursos
        self.fonte_empresa = FonteDeRecurso.objects.create(nome="Empresa Parceira")
        self.fonte_embrapii = FonteDeRecurso.objects.create(nome="EMBRAPII")
        self.fonte_sebrae = FonteDeRecurso.objects.create(nome="SEBRAE")

        # Contas Bancárias
        self.conta_empresa = ContaBancaria.objects.create(
            projeto=self.projeto,
            fonte_recurso=self.fonte_empresa,
            banco="Banco do Brasil",
            agencia="1234",
            conta="10001",
            dv="1",
        )
        self.conta_embrapii = ContaBancaria.objects.create(
            projeto=self.projeto,
            fonte_recurso=self.fonte_embrapii,
            banco="Banco do Brasil",
            agencia="1234",
            conta="20002",
            dv="2",
        )

    def test_01_criacao_legitima_com_conta_empresa_sucesso(self):
        """Item patrimonial com conta bancária da Empresa é válido e passa no clean()."""
        item = ItemPatrimonial(
            termo=self.termo,
            numero_ativo="BEM-001",
            descricao="Osciloscópio Digital",
            valor_bem=Decimal("15000.00"),
            conta_bancaria=self.conta_empresa,
        )
        item.full_clean()
        item.save()
        self.assertEqual(item.conta_bancaria.fonte_recurso.nome, "Empresa Parceira")

    def test_02_rejeita_item_patrimonial_com_conta_direta_embrapii(self):
        """Item patrimonial com conta direta EMBRAPII deve levantar ValidationError no clean()."""
        item = ItemPatrimonial(
            termo=self.termo,
            numero_ativo="BEM-002",
            descricao="Braço Robótico",
            valor_bem=Decimal("45000.00"),
            conta_bancaria=self.conta_embrapii,
        )
        with self.assertRaises(ValidationError) as ctx:
            item.full_clean()
        self.assertIn('conta_bancaria', ctx.exception.message_dict)

    def test_03_rejeita_item_patrimonial_com_processo_compra_embrapii(self):
        """Item patrimonial com processo de compra custeado por conta EMBRAPII deve ser rejeitado."""
        proc_compra = Processo.objects.create(
            projeto=self.projeto,
            tipo=self.tipo_proc,
            numero="00100/2026",
            conta_bancaria=self.conta_embrapii,
        )
        item = ItemPatrimonial(
            termo=self.termo,
            numero_ativo="BEM-003",
            descricao="Torno CNC",
            valor_bem=Decimal("80000.00"),
            processo_compra=proc_compra,
        )
        with self.assertRaises(ValidationError) as ctx:
            item.full_clean()
        self.assertIn('processo_compra', ctx.exception.message_dict)

    def test_04_signal_m2m_bloqueia_adicao_direta_processo_pagamento_embrapii(self):
        """Signal m2m_changed deve bloquear item.processos_pagamento.add(proc_embrapii)."""
        item = ItemPatrimonial.objects.create(
            termo=self.termo,
            numero_ativo="BEM-004",
            descricao="Estação de Solda",
            valor_bem=Decimal("3000.00"),
            conta_bancaria=self.conta_empresa,
        )
        proc_pagamento_embrapii = Processo.objects.create(
            projeto=self.projeto,
            tipo=self.tipo_proc,
            numero="00101/2026",
            conta_bancaria=self.conta_embrapii,
        )
        with self.assertRaises(ValidationError) as ctx:
            item.processos_pagamento.add(proc_pagamento_embrapii)
        self.assertIn("RN-06", str(ctx.exception))

    def test_05_signal_m2m_bloqueia_adicao_reversa_processo_pagamento_embrapii(self):
        """Signal m2m_changed deve bloquear processo_embrapii.itens_pagos.add(item) (Direção Reversa)."""
        item = ItemPatrimonial.objects.create(
            termo=self.termo,
            numero_ativo="BEM-005",
            descricao="Impressora 3D Industrial",
            valor_bem=Decimal("25000.00"),
            conta_bancaria=self.conta_empresa,
        )
        proc_pagamento_embrapii = Processo.objects.create(
            projeto=self.projeto,
            tipo=self.tipo_proc,
            numero="00102/2026",
            conta_bancaria=self.conta_embrapii,
        )
        with self.assertRaises(ValidationError) as ctx:
            proc_pagamento_embrapii.itens_pagos.add(item)
        self.assertIn("RN-06", str(ctx.exception))

    def test_06_processo_bloqueia_mutacao_posterior_para_conta_embrapii(self):
        """Processo já vinculado a item patrimonial não pode ter conta alterada para EMBRAPII (Anti-Tampering)."""
        proc_compra = Processo.objects.create(
            projeto=self.projeto,
            tipo=self.tipo_proc,
            numero="00103/2026",
            conta_bancaria=self.conta_empresa,
        )
        ItemPatrimonial.objects.create(
            termo=self.termo,
            numero_ativo="BEM-006",
            descricao="Sensor Laser LiDAR",
            valor_bem=Decimal("12000.00"),
            processo_compra=proc_compra,
        )
        # Tentativa de mutação posterior da conta do processo para EMBRAPII
        proc_compra.conta_bancaria = self.conta_embrapii
        with self.assertRaises(ValidationError) as ctx:
            proc_compra.clean()
        self.assertIn('conta_bancaria', ctx.exception.message_dict)

    def test_07_bem_patrimonial_clean_rejeita_conta_embrapii(self):
        """BemPatrimonial no inventário definitivo não aceita conta com fonte EMBRAPII."""
        bem = BemPatrimonial(
            projeto=self.projeto,
            descricao="Servidor de IA GPU",
            valor=Decimal("95000.00"),
            conta_bancaria=self.conta_embrapii,
        )
        with self.assertRaises(ValidationError) as ctx:
            bem.clean()
        self.assertIn('conta_bancaria', ctx.exception.message_dict)
```

---

## 4. Passo a Passo de Execução para o Devin

1. **Aplicar as alterações nos 5 arquivos** conforme a especificação acima.
2. **Gerar e aplicar as migrações:**
   ```powershell
   python manage.py makemigrations cadastros incorporacao patrimonio
   python manage.py migrate
   ```
3. **Executar verificação de sanidade:**
   ```powershell
   python manage.py check
   ```
4. **Executar a nova suíte de testes da Etapa 6.2:**
   ```powershell
   python manage.py test incorporacao.tests.TravaCapitalEmbrapiiTestCase
   ```
5. **Executar a suíte completa de testes do ARGUS:**
   ```powershell
   python manage.py test
   ```
   *Critério de Homologação:* **168 testes verdes (0 regressões, 0 falhas)**.
