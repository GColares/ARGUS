# Handoff Cirúrgico de Engenharia — Fase 6 / Etapa 6.4
## Travas Regulatórias de Planejamento Físico & Congelamento de Escopo (RN-07 e RN-10)

> **Destinatário:** Devin Desktop (Desenvolvedor Autônomo & Refatorador)  
> **Autor / Tech Lead:** Antigravity-Gemini (Arquiteto de Software & Guardião do Domínio)  
> **Auditor Red Team:** DeepSeek (LM Studio) & Copilot  
> **Status Atual do Repositório:** Baseline de **176/176 testes verdes (100% OK)**.  
> **Meta da Etapa 6.4:** **184/184 testes verdes (+8 testes unitários, 0 regressões)**.

---

## 1. Contexto Regulatório e Regras de Negócio (RN-07 e RN-10)

Conforme a **Portaria SUFRAMA 9835/2022**, o **Manual de Operações EMBRAPII** e o documento de Requisitos do ARGUS (`01_ESPECIFICACAO_REQUISITOS.md`):

1. **RN-07 — Não-Sobreposição Temporal de Macroentregas (Sequenciamento Estrito):**
   - O planejamento físico em Macroentregas (TRL 3 a 6) de um `PlanoDeTrabalho` não permite sobreposição cronológica de tempo entre entregas subsequentes:
     $$\text{data\_inicio}(M_N) \ge \text{data\_fim}(M_{N-1})$$
   - A data final de uma macroentrega jamais pode ser anterior à sua data inicial:
     $$\text{data\_fim} \ge \text{data\_inicio}$$
   - Se duas macroentregas do mesmo plano de trabalho possuírem datas absolutas (`data_inicio` e `data_fim`), o sistema deve validar matematicamente que nenhuma sobreposição de intervalo fechado ocorre entre elas.

2. **RN-10 — Congelamento do Escopo em Execução:**
   - Uma vez que o `ProjetoPDI` atinge a fase de `EXECUCAO` (ou fases posteriores `PRESTACAO_CONTAS`, `ENCERRADO`), o escopo técnico do `PlanoDeTrabalho` entra em **congelamento integral**.
   - Qualquer tentativa de:
     - Adicionar nova `Macroentrega` vinculada ao plano vigente;
     - Modificar datas, nome ou TRL de `Macroentrega` existente;
     - Deletar uma `Macroentrega`;
     deve levantar `ValidationError` impedindo a alteração direta no banco de dados.
   - Alterações de escopo só são admitidas mediante formalização de Termo Aditivo ou criação de uma versão com status `RETIFICADO`.

---

## 2. Arquivos Estritamente Liberados para Edição (SoD)

Apenas os arquivos a seguir estão autorizados para modificação:
1. `cadastros/models.py` (Adicionar `clean()` e sobrescrever `delete()` em `Macroentrega`, além de `esta_congelado` em `PlanoDeTrabalho`)
2. `cadastros/tests.py` (Adicionar a suíte `TravaPlanejamentoFisicoTestCase` com 8 testes)

---

## 3. Especificação Cirúrgica das Alterações

### 3.1. `cadastros/models.py`

#### A. No modelo `PlanoDeTrabalho` (linha ~420):
Adicionar a propriedade auxiliar `esta_congelado`:
```python
    @property
    def esta_congelado(self):
        """Retorna True se o plano pertence a um projeto em fase de execução ou superior."""
        if hasattr(self, 'projeto') and self.projeto:
            return self.projeto.fase in ['EXECUCAO', 'PRESTACAO_CONTAS', 'ENCERRADO']
        if hasattr(self, 'termo_parceria') and self.termo_parceria and hasattr(self.termo_parceria, 'projeto') and self.termo_parceria.projeto:
            return self.termo_parceria.projeto.fase in ['EXECUCAO', 'PRESTACAO_CONTAS', 'ENCERRADO']
        return False
```

#### B. No modelo `Macroentrega` (linha ~1172):
Implementar o método `clean(self)` e sobrescrever `delete(self)` para blindar contra deleção em projeto em execução:
```python
    def clean(self):
        super().clean()
        from django.core.exceptions import ValidationError

        if not hasattr(self, 'plano_trabalho') or not self.plano_trabalho:
            return

        # 1. Trava RN-10: Congelamento de Escopo na Execução
        if self.plano_trabalho.esta_congelado:
            if not self.pk:
                raise ValidationError(
                    "RN-10: O Plano de Trabalho está vinculado a um projeto em execução e seu escopo "
                    "encontra-se congelado. Não é permitido adicionar novas macroentregas diretamente."
                )
            else:
                original = Macroentrega.objects.filter(pk=self.pk).first()
                if original:
                    campos_congelados = ['numero', 'nome', 'trl', 'data_inicio', 'data_fim']
                    alterados = [c for c in campos_congelados if getattr(self, c) != getattr(original, c)]
                    if alterados:
                        raise ValidationError(
                            f"RN-10: O escopo técnico deste plano está congelado (fase de Execução). "
                            f"Não é permitido alterar os campos: {', '.join(alterados)} sem Termo Aditivo."
                        )

        # 2. Validação básica de cronologia individual
        if self.data_inicio and self.data_fim:
            if self.data_fim < self.data_inicio:
                raise ValidationError({
                    'data_fim': "A data final da macroentrega não pode ser anterior à data inicial."
                })

        # 3. Trava RN-07: Sequenciamento Estrito de Macroentregas (sem sobreposição)
        if self.data_inicio and self.data_fim and self.numero:
            outras = Macroentrega.objects.filter(
                plano_trabalho=self.plano_trabalho
            )
            if self.pk:
                outras = outras.exclude(pk=self.pk)

            for outra in outras:
                if not outra.data_inicio or not outra.data_fim or not outra.numero:
                    continue

                # Macroentrega anterior (número menor) deve terminar antes ou no mesmo dia do início desta
                if outra.numero < self.numero and self.data_inicio < outra.data_fim:
                    raise ValidationError({
                        'data_inicio': (
                            f"RN-07: Violação de sequenciamento temporal: a Macroentrega {self.numero} "
                            f"inicia em {self.data_inicio.strftime('%d/%m/%Y')}, antes do término da "
                            f"Macroentrega {outra.numero} ({outra.data_fim.strftime('%d/%m/%Y')})."
                        )
                    })

                # Macroentrega posterior (número maior) não pode iniciar antes do término desta
                if outra.numero > self.numero and self.data_fim > outra.data_inicio:
                    raise ValidationError({
                        'data_fim': (
                            f"RN-07: Violação de sequenciamento temporal: a Macroentrega {self.numero} "
                            f"termina em {self.data_fim.strftime('%d/%m/%Y')}, após o início da "
                            f"Macroentrega {outra.numero} ({outra.data_inicio.strftime('%d/%m/%Y')})."
                        )
                    })

    def delete(self, *args, **kwargs):
        from django.core.exceptions import ValidationError
        if hasattr(self, 'plano_trabalho') and self.plano_trabalho and self.plano_trabalho.esta_congelado:
            raise ValidationError(
                "RN-10: Não é permitido excluir macroentregas de um Plano de Trabalho em execução (escopo congelado)."
            )
        return super().delete(*args, **kwargs)
```

---

## 4. Bateria de Testes Automatizados Requerida (`cadastros/tests.py`)

Criar a classe de teste `TravaPlanejamentoFisicoTestCase(TestCase)` com **8 testes rigorosos**:
1. `test_01_macroentrega_cronologia_invalida_rejeitada`: Data fim < data início gera `ValidationError({'data_fim': ...})`.
2. `test_02_macroentregas_sequenciais_validas`: M1 (Jan-Mar) e M2 (Mar-Jun) aceitas perfeitamente.
3. `test_03_macroentregas_sobrepostas_rejeitadas`: M2 iniciando antes do término de M1 é rejeitada pela RN-07.
4. `test_04_macroentrega_posterior_sobreposta_rejeitada`: M1 editada com data fim ultrapassando início de M2 é rejeitada.
5. `test_05_projeto_prospeccao_permite_edicao_livre`: Projeto em `fase='PROSPECCAO'` permite adicionar, editar e excluir macroentregas sem restrição de congelamento.
6. `test_06_projeto_execucao_bloqueia_nova_macroentrega`: Projeto em `fase='EXECUCAO'` rejeita adição de nova macroentrega com erro RN-10.
7. `test_07_projeto_execucao_bloqueia_mutacao_macroentrega_existente`: Tentar alterar nome, TRL ou datas de macroentrega existente em projeto em execução é rejeitado pela RN-10.
8. `test_08_projeto_execucao_bloqueia_delecao_macroentrega`: Tentar chamar `.delete()` em macroentrega de plano congelado levanta `ValidationError`.

---

## 5. Critérios de Aceite e Homologação
- `python manage.py check` -> 0 erros.
- `python manage.py test cadastros.tests.TravaPlanejamentoFisicoTestCase` -> **8/8 testes OK (100%)**.
- `python manage.py test` -> **184/184 testes OK (100% verde, 0 regressões)**.
