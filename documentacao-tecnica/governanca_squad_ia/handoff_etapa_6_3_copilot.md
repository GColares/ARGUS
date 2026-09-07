# Handoff Cirúrgico de Engenharia — Fase 6 / Etapa 6.3
## Trava Regulatória de Concessão e Acúmulo de Bolsas (RN-12 / Regulamento IFAM)

> **Destinatário:** GitHub Copilot (VS Code / Implementador)  
> **Autor / Tech Lead:** Antigravity-Gemini (Arquiteto de Software)  
> **Revisor Independente (Red Team):** DeepSeek (LM Studio) & Copilot  
> **Status do Repositório:** Baseline de **168/168 testes verdes (100% OK)**.  
> **Meta da Etapa 6.3:** **176/176 testes verdes (+8 testes unitários, 0 regressões)**.

---

## 1. Contexto Regulatório e Regras de Negócio (RN-12)

Conforme a **Lei 10.973/2004**, **Lei 12.772/2012** e o **Regulamento sobre Concessão de Bolsas do IFAM**:
1. **Teto de Projetos Simultâneos (§ 3º):** É permitida a participação em até **dois (02) projetos ativos concorrentes** com bolsa. A vinculação ao **terceiro projeto simultâneo é terminantemente vedada**, salvo com autorização excepcional justificada.
2. **Impedimento de Duplicidade no Mesmo Projeto:** É vedado ao mesmo beneficiário possuir mais de um termo de bolsa ativo no mesmo período no mesmo projeto.
3. **Cargos de Direção (§ 4º e § 5º):**
   * **CD-01 (Reitor / Pró-Reitor / Diretor-Geral):** **Vedação absoluta**. É proibido conceder qualquer modalidade de bolsa.
   * **CD-02, CD-03 e CD-04:** Teto especial de **no máximo um (01) projeto ativo**.
4. **Intersecção Temporal Estrita:** A colisão de termos só ocorre se houver sobreposição cronológica de vigência entre termos com status **`ATIVO`**:
   $$\text{vigência\_início}_A \le \text{vigência\_fim}_B \quad \text{e} \quad \text{vigência\_fim}_A \ge \text{vigência\_início}_B$$
5. **Teto de Carga Horária Semanal:** A soma das cargas horárias semanais dos termos ativos simultâneos não pode exceder **20 horas semanais** (respeitando o regime de dedicação exclusiva).

---

## 2. Arquivos Estritamente Liberados para Edição (SoD)

Apenas os 4 arquivos a seguir estão autorizados para modificação:
1. `cadastros/models.py`
2. `cadastros/forms.py`
3. `cadastros/templates/cadastros/form_pessoa_fisica.html`
4. `cadastros/tests.py`

---

## 3. Especificação Cirúrgica das Alterações

### 3.1. `cadastros/models.py`

#### A. No modelo `PerfilServidor` (linha ~770):
Adicionar a constante e o campo `cargo_direcao`:
```python
    CARGOS_DIRECAO_CHOICES = [
        ('NENHUM', 'Nenhum / Sem Cargo Comissionado'),
        ('CD1', 'CD-01 (Reitor / Pró-Reitor / Diretor-Geral)'),
        ('CD2', 'CD-02 (Diretor Sistêmico / Diretor de Campus Avançado)'),
        ('CD3', 'CD-03 (Diretor de Departamento / Coordenador-Geral)'),
        ('CD4', 'CD-04 (Coordenador de Curso / Chefe de Setor)'),
        ('FG', 'Função Gratificada (FG / FUC)'),
    ]

    cargo_direcao = models.CharField(
        max_length=10,
        choices=CARGOS_DIRECAO_CHOICES,
        default='NENHUM',
        verbose_name="Cargo de Direção / Função Gratificada"
    )
```

#### B. No modelo `TermoBolsa` (linha ~833):
Adicionar os campos de carga horária semanal e governança de exceção:
```python
    carga_horaria_semanal = models.PositiveIntegerField(
        default=20,
        verbose_name="Carga Horária Semanal (horas/semana)"
    )
    autorizacao_excepcional = models.BooleanField(
        default=False,
        verbose_name="Autorização Excepcional Deferida?"
    )
    justificativa_excepcional = models.TextField(
        blank=True,
        null=True,
        verbose_name="Justificativa / Parecer da Autorização Excepcional"
    )
```

#### C. No método `clean(self)` de `TermoBolsa` (linha ~862):
Substituir/expandir com o algoritmo de conformidade regulatória:
```python
    def clean(self):
        super().clean()

        if self.pessoa:
            if not (hasattr(self.pessoa, 'perfil_servidor') or 
                    hasattr(self.pessoa, 'perfil_aluno') or 
                    hasattr(self.pessoa, 'perfil_colaborador_externo')):
                raise ValidationError({"pessoa": "Apenas Servidores, Alunos ou Colaboradores Externos podem ser vinculados a um Termo de Bolsa. Terceirizados ou pessoas sem perfil não são permitidos."})
        
        # Impede exceções se campos essenciais ainda não foram informados
        if not self.quantidade_parcelas or not self.valor_parcela or not self.cota_pt:
            return

        # 1. Validação de Cotas (Parcelas)
        if self.quantidade_parcelas > self.cota_pt.parcelas_previstas:
            raise ValidationError({
                "quantidade_parcelas": f"O número de parcelas excede o teto ({self.cota_pt.parcelas_previstas}) estabelecido no PT."
            })

        # 2. Validação de Liquidação Financeira Global
        valor_total_deste_termo = Decimal(str(self.quantidade_parcelas)) * self.valor_parcela
        termos_consolidados = TermoBolsa.objects.filter(
            cota_pt=self.cota_pt,
            status__in=['ATIVO', 'ENCERRADO', 'SUBSTITUIDO']
        )
        if self.pk:
            termos_consolidados = termos_consolidados.exclude(pk=self.pk)

        gasto_acumulado = sum((Decimal(str(t.quantidade_parcelas)) * t.valor_parcela) for t in termos_consolidados)

        if (gasto_acumulado + valor_total_deste_termo) > self.cota_pt.valor_global_previsto:
            raise ValidationError(
                f"Liquidação bloqueada: A projeção financeira deste termo (R$ {valor_total_deste_termo:.2f}) "
                f"somada à execução anterior (R$ {gasto_acumulado:.2f}) ultrapassa o teto do Plano de Trabalho (R$ {self.cota_pt.valor_global_previsto:.2f})."
            )

        # =================================================================
        # 3. RN-12: TRAVAS DE CONCESSÃO E ACÚMULO DE BOLSAS (REGULAMENTO IFAM)
        # =================================================================
        if self.pessoa and self.vigencia_inicio and self.vigencia_fim and self.status == 'ATIVO':
            # Validação de Datas
            if self.vigencia_fim < self.vigencia_inicio:
                raise ValidationError({"vigencia_fim": "A data de término da vigência não pode ser anterior à data de início."})

            perfil_servidor = getattr(self.pessoa, 'perfil_servidor', None)

            # Regra 3.1: CD-01 tem VEDAÇÃO ABSOLUTA de receber bolsas (§ 4º)
            if perfil_servidor and perfil_servidor.cargo_direcao == 'CD1':
                raise ValidationError({
                    "pessoa": "Regulamento de Bolsas IFAM (§ 4º): É terminantemente vedada a concessão de bolsas a servidores ocupantes de Cargo de Direção CD-01."
                })

            # Busca termos concorrentes ativos com sobreposição cronológica
            termos_ativos = TermoBolsa.objects.filter(
                pessoa=self.pessoa,
                status='ATIVO',
                vigencia_inicio__lte=self.vigencia_fim,
                vigencia_fim__gte=self.vigencia_inicio
            )
            if self.pk:
                termos_ativos = termos_ativos.exclude(pk=self.pk)

            # Regra 3.2: CD-02 a CD-04 - Teto especial de no máximo 1 projeto ativo (§ 5º)
            if perfil_servidor and perfil_servidor.cargo_direcao in ['CD2', 'CD3', 'CD4']:
                projetos_existentes = set(termos_ativos.values_list('cota_pt__projeto_id', flat=True))
                if self.cota_pt.projeto_id not in projetos_existentes and len(projetos_existentes) >= 1:
                    raise ValidationError({
                        "pessoa": "Regulamento de Bolsas IFAM (§ 5º): Servidores ocupantes de Cargo de Direção CD-02, CD-03 ou CD-04 só podem participar de no máximo um (01) projeto ativo com bolsa."
                    })

            # Regra 3.3: Impedimento de Duplicidade de Bolsa no MESMO Projeto no mesmo período
            projeto_atual_id = self.cota_pt.projeto_id
            if termos_ativos.filter(cota_pt__projeto_id=projeto_atual_id).exists():
                raise ValidationError({
                    "pessoa": "RN-12: O beneficiário já possui um Termo de Bolsa ativo com vigência concorrente neste mesmo projeto."
                })

            # Regra 3.4: Teto Geral de no máximo DOIS (02) Projetos Distintos Concorrentes (§ 3º)
            projetos_concorrentes_ids = set(termos_ativos.values_list('cota_pt__projeto_id', flat=True))
            projetos_concorrentes_ids.add(projeto_atual_id)

            if len(projetos_concorrentes_ids) > 2 and not self.autorizacao_excepcional:
                raise ValidationError({
                    "pessoa": "RN-12 / Regulamento de Bolsas IFAM (§ 3º): É vedada a participação de um mesmo beneficiário em mais de dois (02) projetos simultâneos com bolsa sem autorização excepcional aprovada."
                })

            # Regra 3.5: Teto de Carga Horária Semanal Acumulada (Máximo 20 horas/semana)
            soma_ch_semanal = sum(t.carga_horaria_semanal for t in termos_ativos) + (self.carga_horaria_semanal or 0)
            if soma_ch_semanal > 20 and not self.autorizacao_excepcional:
                raise ValidationError({
                    "carga_horaria_semanal": f"Carga horária semanal acumulada ({soma_ch_semanal}h/sem) excede o teto legal de 20h semanais para bolsas concorrentes."
                })

            # Regra 3.6: Exigência de Justificativa se Autorização Excepcional estiver ativada
            if self.autorizacao_excepcional and not self.justificativa_excepcional:
                raise ValidationError({
                    "justificativa_excepcional": "Informe a justificativa fundamentada / despacho da Diretoria para a concessão da autorização excepcional."
                })
```

---

### 3.2. `cadastros/forms.py`

1. **No `PerfilServidorForm` (linha ~508):**
   Incluir `cargo_direcao` em `fields` e `widgets`:
   ```python
   class PerfilServidorForm(forms.ModelForm):
       ativo = forms.BooleanField(required=False, initial=True, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
       interno = forms.BooleanField(required=False, initial=True, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))

       class Meta:
           model = PerfilServidor
           fields = ['siape', 'cargo', 'cargo_direcao', 'lotacao', 'interno', 'ativo']
           widgets = {
               'siape': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Matrícula SIAPE'}),
               'cargo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Cargo Efetivo'}),
               'cargo_direcao': forms.Select(attrs={'class': 'form-select'}),
               'lotacao': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Lotação / Campus'}),
           }
   ```

2. **No `TermoBolsaForm` (linha ~250):**
   Incluir `carga_horaria_semanal`, `autorizacao_excepcional`, `justificativa_excepcional`:
   ```python
   class TermoBolsaForm(forms.ModelForm):
       class Meta:
           model = TermoBolsa
           fields = [
               'cota_pt', 'pessoa', 'modalidade_bolsa', 'carga_horaria_semanal', 'carga_horaria_total',
               'numero_termo', 'vigencia_inicio', 'vigencia_fim', 'quantidade_parcelas', 'valor_parcela',
               'status', 'autorizacao_excepcional', 'justificativa_excepcional'
           ]
           widgets = {
               'cota_pt': forms.Select(attrs={'class': 'form-select'}),
               'pessoa': forms.Select(attrs={'class': 'form-select'}),
               'modalidade_bolsa': forms.Select(attrs={'class': 'form-select'}),
               'numero_termo': forms.TextInput(attrs={'class': 'form-control'}),
               'vigencia_inicio': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
               'vigencia_fim': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
               'quantidade_parcelas': forms.NumberInput(attrs={'class': 'form-control'}),
               'carga_horaria_semanal': forms.NumberInput(attrs={'class': 'form-control'}),
               'carga_horaria_total': forms.NumberInput(attrs={'class': 'form-control'}),
               'valor_parcela': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
               'status': forms.Select(attrs={'class': 'form-select fw-bold'}),
               'autorizacao_excepcional': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
               'justificativa_excepcional': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
           }
   ```

---

### 3.3. `cadastros/templates/cadastros/form_pessoa_fisica.html`
Na seção do **Papel 1: Servidor Público** (dentro de `<div class="row g-3">`), logo após o campo `Campus / Lotação` (linha ~167), adicionar o campo `cargo_direcao`:
```html
                                            <div class="col-md-12">
                                                <label class="form-label small fw-semibold">Cargo de Direção / Função Gratificada</label>
                                                {{ form_servidor.cargo_direcao }}
                                            </div>
```

---

### 3.4. `cadastros/tests.py`
Adicionar ao final de `cadastros/tests.py` a suíte `TravaAcumuloBolsasTestCase` com os **8 testes automatizados**:

```python
from cadastros.models import PerfilServidor, PerfilAluno


class TravaAcumuloBolsasTestCase(TestCase):
    """
    Bateria de testes de conformidade regulatória para a RN-12 e Regulamento de Bolsas IFAM:
    Travas de teto de até 2 projetos, vedação para CD-01, limite para CD-02..04,
    proibição de duplicidade no mesmo projeto e teto de 20h semanais.
    """
    def setUp(self):
        self.empresa = EmpresaParceira.objects.create(
            nome="Empresa Fomento Bolsas",
            cnpj="77.888.999/0001-11",
            natureza_juridica="LTDA",
            representante_legal="Diretor Empresa",
            cargo_representante="Diretor",
        )
        self.projeto_a = ProjetoPDI.objects.create(nome="Projeto P&I Alpha", fase="EXECUCAO", concedente=self.empresa)
        self.projeto_b = ProjetoPDI.objects.create(nome="Projeto P&I Beta", fase="EXECUCAO", concedente=self.empresa)
        self.projeto_c = ProjetoPDI.objects.create(nome="Projeto P&I Gamma", fase="EXECUCAO", concedente=self.empresa)

        self.cota_a = CotaBolsaPT.objects.create(projeto=self.projeto_a, perfil_funcao="Pesquisador A", quantidade_vagas=2, parcelas_previstas=12, valor_global_previsto=Decimal("60000.00"))
        self.cota_b = CotaBolsaPT.objects.create(projeto=self.projeto_b, perfil_funcao="Pesquisador B", quantidade_vagas=2, parcelas_previstas=12, valor_global_previsto=Decimal("60000.00"))
        self.cota_c = CotaBolsaPT.objects.create(projeto=self.projeto_c, perfil_funcao="Pesquisador C", quantidade_vagas=2, parcelas_previstas=12, valor_global_previsto=Decimal("60000.00"))

        # Pessoas de Teste
        self.pf_docente = PessoaFisica.objects.create(nome="Prof. Carlos Silva", cpf="111.222.333-44", data_nascimento="1980-05-10")
        self.servidor_docente = PerfilServidor.objects.create(pessoa=self.pf_docente, siape="1234567", cargo="Professor EBTT", lotacao="Campus Manaus Centro", cargo_direcao="NENHUM")

        self.pf_gestor_cd1 = PessoaFisica.objects.create(nome="Diretor Reitor", cpf="222.333.444-55", data_nascimento="1975-02-15")
        PerfilServidor.objects.create(pessoa=self.pf_gestor_cd1, siape="2345678", cargo="Professor EBTT", lotacao="Reitoria", cargo_direcao="CD1")

        self.pf_gestor_cd3 = PessoaFisica.objects.create(nome="Chefe Departamento", cpf="333.444.555-66", data_nascimento="1985-08-20")
        PerfilServidor.objects.create(pessoa=self.pf_gestor_cd3, siape="3456789", cargo="Professor EBTT", lotacao="Campus Manaus Distrito", cargo_direcao="CD3")

    def test_01_bolsa_individual_legitima_sucesso(self):
        """Bolsa para docente em 1 projeto com 10h semanais é válida."""
        termo = TermoBolsa(
            cota_pt=self.cota_a, pessoa=self.pf_docente, modalidade_bolsa="Pesquisa",
            numero_termo="TB-001/2026", vigencia_inicio="2026-01-01", vigencia_fim="2026-06-30",
            quantidade_parcelas=6, valor_parcela=Decimal("2500.00"), carga_horaria_semanal=10, status="ATIVO"
        )
        termo.full_clean()
        termo.save()
        self.assertEqual(termo.status, "ATIVO")

    def test_02_rejeita_bolsa_para_servidor_cd01_vedacao_absoluta(self):
        """Ocupante de Cargo CD-01 tem vedação absoluta de bolsa (§ 4º)."""
        termo = TermoBolsa(
            cota_pt=self.cota_a, pessoa=self.pf_gestor_cd1, modalidade_bolsa="Pesquisa",
            numero_termo="TB-002/2026", vigencia_inicio="2026-01-01", vigencia_fim="2026-06-30",
            quantidade_parcelas=6, valor_parcela=Decimal("2500.00"), carga_horaria_semanal=10, status="ATIVO"
        )
        with self.assertRaises(ValidationError) as ctx:
            termo.full_clean()
        self.assertIn("pessoa", ctx.exception.message_dict)
        self.assertIn("CD-01", str(ctx.exception))

    def test_03_limita_servidor_cd02_a_cd04_a_um_projeto_ativo(self):
        """Servidor CD-02..CD-04 pode ter 1 projeto, mas é barrado ao tentar o segundo (§ 5º)."""
        TermoBolsa.objects.create(
            cota_pt=self.cota_a, pessoa=self.pf_gestor_cd3, modalidade_bolsa="Pesquisa",
            numero_termo="TB-CD3-1/2026", vigencia_inicio="2026-01-01", vigencia_fim="2026-06-30",
            quantidade_parcelas=6, valor_parcela=Decimal("2000.00"), carga_horaria_semanal=10, status="ATIVO"
        )
        # Tentativa no segundo projeto simultâneo
        termo_segundo = TermoBolsa(
            cota_pt=self.cota_b, pessoa=self.pf_gestor_cd3, modalidade_bolsa="Pesquisa",
            numero_termo="TB-CD3-2/2026", vigencia_inicio="2026-02-01", vigencia_fim="2026-07-31",
            quantidade_parcelas=6, valor_parcela=Decimal("2000.00"), carga_horaria_semanal=10, status="ATIVO"
        )
        with self.assertRaises(ValidationError) as ctx:
            termo_segundo.full_clean()
        self.assertIn("pessoa", ctx.exception.message_dict)
        self.assertIn("CD-02, CD-03 ou CD-04", str(ctx.exception))

    def test_04_permite_ate_dois_projetos_distintos_concorrentes(self):
        """Beneficiário comum pode participar de até 2 projetos com bolsa ativa simultânea (§ 3º)."""
        TermoBolsa.objects.create(
            cota_pt=self.cota_a, pessoa=self.pf_docente, modalidade_bolsa="Pesquisa",
            numero_termo="TB-P1/2026", vigencia_inicio="2026-01-01", vigencia_fim="2026-06-30",
            quantidade_parcelas=6, valor_parcela=Decimal("1500.00"), carga_horaria_semanal=10, status="ATIVO"
        )
        termo_p2 = TermoBolsa(
            cota_pt=self.cota_b, pessoa=self.pf_docente, modalidade_bolsa="Pesquisa",
            numero_termo="TB-P2/2026", vigencia_inicio="2026-02-01", vigencia_fim="2026-05-31",
            quantidade_parcelas=4, valor_parcela=Decimal("1500.00"), carga_horaria_semanal=10, status="ATIVO"
        )
        termo_p2.full_clean()
        termo_p2.save()
        self.assertEqual(termo_p2.status, "ATIVO")

    def test_05_rejeita_terceiro_projeto_concorrente_sem_excecao(self):
        """Tentativa de atuar em 3 projetos com sobreposição de vigência é rejeitada (§ 3º)."""
        TermoBolsa.objects.create(
            cota_pt=self.cota_a, pessoa=self.pf_docente, modalidade_bolsa="Pesquisa",
            numero_termo="TB-P1/2026", vigencia_inicio="2026-01-01", vigencia_fim="2026-06-30",
            quantidade_parcelas=6, valor_parcela=Decimal("1000.00"), carga_horaria_semanal=5, status="ATIVO"
        )
        TermoBolsa.objects.create(
            cota_pt=self.cota_b, pessoa=self.pf_docente, modalidade_bolsa="Pesquisa",
            numero_termo="TB-P2/2026", vigencia_inicio="2026-01-01", vigencia_fim="2026-06-30",
            quantidade_parcelas=6, valor_parcela=Decimal("1000.00"), carga_horaria_semanal=5, status="ATIVO"
        )
        # Tentativa no terceiro projeto
        termo_p3 = TermoBolsa(
            cota_pt=self.cota_c, pessoa=self.pf_docente, modalidade_bolsa="Pesquisa",
            numero_termo="TB-P3/2026", vigencia_inicio="2026-03-01", vigencia_fim="2026-08-31",
            quantidade_parcelas=6, valor_parcela=Decimal("1000.00"), carga_horaria_semanal=5, status="ATIVO"
        )
        with self.assertRaises(ValidationError) as ctx:
            termo_p3.full_clean()
        self.assertIn("pessoa", ctx.exception.message_dict)
        self.assertIn("mais de dois (02) projetos", str(ctx.exception))

    def test_06_rejeita_duplicidade_de_bolsa_no_mesmo_projeto(self):
        """Beneficiário não pode ter dois termos ativos no mesmo projeto com vigência concorrente."""
        TermoBolsa.objects.create(
            cota_pt=self.cota_a, pessoa=self.pf_docente, modalidade_bolsa="Pesquisa",
            numero_termo="TB-DUP1/2026", vigencia_inicio="2026-01-01", vigencia_fim="2026-06-30",
            quantidade_parcelas=6, valor_parcela=Decimal("2000.00"), carga_horaria_semanal=10, status="ATIVO"
        )
        termo_dup2 = TermoBolsa(
            cota_pt=self.cota_a, pessoa=self.pf_docente, modalidade_bolsa="Pesquisa",
            numero_termo="TB-DUP2/2026", vigencia_inicio="2026-02-01", vigencia_fim="2026-05-31",
            quantidade_parcelas=4, valor_parcela=Decimal("2000.00"), carga_horaria_semanal=10, status="ATIVO"
        )
        with self.assertRaises(ValidationError) as ctx:
            termo_dup2.full_clean()
        self.assertIn("pessoa", ctx.exception.message_dict)
        self.assertIn("neste mesmo projeto", str(ctx.exception))

    def test_07_rejeita_soma_carga_horaria_semanal_superior_a_20h(self):
        """Soma das cargas horárias dos termos ativos não pode ultrapassar 20h semanais."""
        TermoBolsa.objects.create(
            cota_pt=self.cota_a, pessoa=self.pf_docente, modalidade_bolsa="Pesquisa",
            numero_termo="TB-CH1/2026", vigencia_inicio="2026-01-01", vigencia_fim="2026-06-30",
            quantidade_parcelas=6, valor_parcela=Decimal("2000.00"), carga_horaria_semanal=15, status="ATIVO"
        )
        # Termo concorrente no projeto B com 10h/semana (soma = 25h > 20h)
        termo_ch2 = TermoBolsa(
            cota_pt=self.cota_b, pessoa=self.pf_docente, modalidade_bolsa="Pesquisa",
            numero_termo="TB-CH2/2026", vigencia_inicio="2026-02-01", vigencia_fim="2026-05-31",
            quantidade_parcelas=4, valor_parcela=Decimal("1500.00"), carga_horaria_semanal=10, status="ATIVO"
        )
        with self.assertRaises(ValidationError) as ctx:
            termo_ch2.full_clean()
        self.assertIn("carga_horaria_semanal", ctx.exception.message_dict)
        self.assertIn("excede o teto legal de 20h", str(ctx.exception))

    def test_08_autorizacao_excepcional_permite_terceiro_projeto_se_justificado(self):
        """Com autorização excepcional deferida e justificativa, terceiro projeto é aceito."""
        TermoBolsa.objects.create(
            cota_pt=self.cota_a, pessoa=self.pf_docente, modalidade_bolsa="Pesquisa",
            numero_termo="TB-EXC1/2026", vigencia_inicio="2026-01-01", vigencia_fim="2026-06-30",
            quantidade_parcelas=6, valor_parcela=Decimal("1000.00"), carga_horaria_semanal=5, status="ATIVO"
        )
        TermoBolsa.objects.create(
            cota_pt=self.cota_b, pessoa=self.pf_docente, modalidade_bolsa="Pesquisa",
            numero_termo="TB-EXC2/2026", vigencia_inicio="2026-01-01", vigencia_fim="2026-06-30",
            quantidade_parcelas=6, valor_parcela=Decimal("1000.00"), carga_horaria_semanal=5, status="ATIVO"
        )
        termo_p3_excepcional = TermoBolsa(
            cota_pt=self.cota_c, pessoa=self.pf_docente, modalidade_bolsa="Pesquisa",
            numero_termo="TB-EXC3/2026", vigencia_inicio="2026-03-01", vigencia_fim="2026-08-31",
            quantidade_parcelas=6, valor_parcela=Decimal("1000.00"), carga_horaria_semanal=5, status="ATIVO",
            autorizacao_excepcional=True,
            justificativa_excepcional="Despacho PROPESP/IFAM nº 42/2026 autorizando atuação estratégica em projeto prioritário."
        )
        termo_p3_excepcional.full_clean()
        termo_p3_excepcional.save()
        self.assertEqual(termo_p3_excepcional.status, "ATIVO")
        self.assertTrue(termo_p3_excepcional.autorizacao_excepcional)
```

---

## 4. Passo a Passo de Execução para o Copilot

1. **Aplicar as alterações nos 4 arquivos** conforme a especificação acima.
2. **Gerar e aplicar as migrações:**
   ```powershell
   python manage.py makemigrations cadastros
   python manage.py migrate
   ```
3. **Executar verificação de sanidade do Django:**
   ```powershell
   python manage.py check
   ```
4. **Executar a nova suíte de testes:**
   ```powershell
   python manage.py test cadastros.tests.TravaAcumuloBolsasTestCase
   ```
5. **Executar a suíte completa de regressão:**
   ```powershell
   python manage.py test
   ```
   *Critério de Homologação:* **176 testes verdes (100% de aprovação, 0 regressões)**.
