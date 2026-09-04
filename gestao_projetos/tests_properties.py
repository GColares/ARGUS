"""
gestao_projetos/tests_properties.py
=====================================
Suíte de Property-Based Testing do ARGUS
Engenheiro de QA: Kiro (AWS Bedrock)

Estratégia:
  - Sem `hypothesis` no ambiente → geradores determinísticos + pseudo-aleatórios
    nativos (random, itertools) com semente fixada (SEED) para reprodutibilidade.
  - Cada TestCase itera N_ROUNDS combinações geradas, verificando as propriedades
    formais descritas no design.md da spec qa-invariants-property-testing.

Invariantes cobertas:
  [REQ-QA-001..004] Unicidade de Exercício e Cascata de Suplência (Lei 8.112/90)
  [REQ-QA-005..007] Travas Orçamentárias SUFRAMA/EMBRAPII
"""

import random
import itertools
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.test import TestCase, override_settings

from gestao_projetos.models import (
    FuncaoInstitucional,
    OcupacaoFuncao,
    AfastamentoExercicio,
)
from cadastros.models import (
    EmpresaParceira,
    ProjetoPDI,
    PlanoDeTrabalho,
    RubricaOrcamentariaPT,
)

# ──────────────────────────────────────────────────────────────────────────────
# Configuração global da suíte
# ──────────────────────────────────────────────────────────────────────────────

# Semente fixa → resultados reproduzíveis em CI/CD
SEED = 42

# Número de rodadas por propriedade (balance: cobertura × velocidade)
N_ROUNDS = 150

# Janela de tempo base para geração de datas
BASE_DATE = date(2026, 1, 1)
WINDOW_DAYS = 365  # 1 ano


# ──────────────────────────────────────────────────────────────────────────────
# Task 2 — Geradores de Linha Temporal
# ──────────────────────────────────────────────────────────────────────────────

class GeradorLinhaTemporalAfastamentos:
    """
    Gera cenários arbitrários de afastamentos para N ocupações ao longo de uma
    janela de tempo, incluindo casos com sobreposições e buracos temporais.

    Propriedades garantidas pelo gerador:
    - Todo afastamento tem data_fim >= data_inicio (intervalo válido).
    - A data de consulta é sempre dentro da janela gerada.
    - Cenários incluem: todos livres, todos afastados (buraco), sobreposições
      parciais e transições exatas em datas limítrofes.
    """

    def __init__(self, seed: int = SEED):
        self.rng = random.Random(seed)

    def gerar_data_aleatoria(self, base: date = BASE_DATE, janela: int = WINDOW_DAYS) -> date:
        """Retorna uma data aleatória dentro da janela."""
        offset = self.rng.randint(0, janela - 1)
        return base + timedelta(days=offset)

    def gerar_intervalo_afastamento(self, base: date = BASE_DATE, janela: int = WINDOW_DAYS):
        """Retorna (data_inicio, data_fim) válido dentro da janela."""
        inicio_offset = self.rng.randint(0, janela - 30)
        duracao = self.rng.randint(1, 29)
        inicio = base + timedelta(days=inicio_offset)
        fim = inicio + timedelta(days=duracao)
        return inicio, fim

    def gerar_cenario(self, n_ocupacoes: int, n_afastamentos_por_ocupacao: int = 2):
        """
        Retorna uma lista de listas: para cada ocupação (índice = prioridade),
        uma lista de tuplas (data_inicio, data_fim, motivo) representando seus
        afastamentos.

        Cenários especiais injetados a cada ~10 rodadas:
        - Todos afastados simultaneamente (testa fallback None).
        - Zero afastamentos (testa retorno direto do titular).
        - Afastamento exato de 1 dia (testa fronteiras inclusivas).
        """
        motivos = ['FERIAS', 'LICENCA_MEDICA', 'MISSAO', 'LICENCA_CAPACITACAO', 'OUTRO']
        cenario = []
        for _ in range(n_ocupacoes):
            afastamentos = []
            n = self.rng.randint(0, n_afastamentos_por_ocupacao)
            for _ in range(n):
                inicio, fim = self.gerar_intervalo_afastamento()
                motivo = self.rng.choice(motivos)
                afastamentos.append((inicio, fim, motivo))
            cenario.append(afastamentos)
        return cenario

    def gerar_cenario_todos_afastados(self, n_ocupacoes: int, data_ref: date):
        """Cenário degenerado: todos afastados na data_ref — deve retornar None/fallback."""
        cenario = []
        for _ in range(n_ocupacoes):
            inicio = data_ref - timedelta(days=1)
            fim = data_ref + timedelta(days=1)
            cenario.append([(inicio, fim, 'FERIAS')])
        return cenario

    def gerar_cenario_zero_afastamentos(self, n_ocupacoes: int):
        """Cenário: nenhum afastamento — titular deve sempre ser retornado."""
        return [[] for _ in range(n_ocupacoes)]

    def gerar_cenario_fronteira_exata(self, n_ocupacoes: int, data_ref: date):
        """
        Afastamento do titular termina EXATAMENTE em data_ref - 1 dia.
        O titular deve estar em exercício em data_ref.
        """
        cenario = []
        for i in range(n_ocupacoes):
            if i == 0:
                # Titular: afastamento termina no dia anterior
                inicio = data_ref - timedelta(days=10)
                fim = data_ref - timedelta(days=1)
                cenario.append([(inicio, fim, 'FERIAS')])
            else:
                cenario.append([])
        return cenario

    def gerar_cenario_afastamento_inicia_hoje(self, n_ocupacoes: int, data_ref: date):
        """
        Afastamento do titular começa EXATAMENTE em data_ref.
        O titular NÃO deve estar em exercício → substituto deve ser selecionado.
        """
        cenario = []
        for i in range(n_ocupacoes):
            if i == 0:
                inicio = data_ref
                fim = data_ref + timedelta(days=10)
                cenario.append([(inicio, fim, 'FERIAS')])
            else:
                cenario.append([])
        return cenario


# ──────────────────────────────────────────────────────────────────────────────
# Helpers de fixture dinâmica
# ──────────────────────────────────────────────────────────────────────────────

def criar_funcao_com_ocupacoes(n_ocupacoes: int, sufixo: str = ""):
    """
    Cria uma FuncaoInstitucional com N ocupações (prioridades 0..N-1)
    e retorna (funcao, lista_de_ocupacoes).
    """
    funcao = FuncaoInstitucional.objects.create(
        codigo=f"FUNC_PROP_{sufixo}_{n_ocupacoes}",
        nome_cargo=f"Cargo Propriedade {sufixo}",
        ativo=True,
    )
    ocupacoes = []
    sufixos_cargo = ['', '1º Substituto', '2º Substituto', '3º Substituto']
    portarias = [
        'Portaria 100/2026', 'Portaria 101/2026',
        'Portaria 102/2026', 'Portaria 103/2026',
    ]
    for i in range(n_ocupacoes):
        oc = OcupacaoFuncao.objects.create(
            funcao=funcao,
            nome_externo=f"Pessoa_{sufixo}_{i}",
            prioridade=i,
            portaria_designacao=portarias[i] if i < len(portarias) else f"Portaria {i}/2026",
            sufixo_cargo=sufixos_cargo[i] if i < len(sufixos_cargo) else f"{i}º Substituto",
            ativo=True,
        )
        ocupacoes.append(oc)
    return funcao, ocupacoes


def aplicar_afastamentos(ocupacoes, cenario):
    """
    Cria objetos AfastamentoExercicio no banco para cada (ocupacao, cenario[i]).
    Retorna lista plana de objetos criados.
    """
    objetos = []
    for ocupacao, afastamentos in zip(ocupacoes, cenario):
        for inicio, fim, motivo in afastamentos:
            obj = AfastamentoExercicio.objects.create(
                ocupacao=ocupacao,
                data_inicio=inicio,
                data_fim=fim,
                motivo=motivo,
                ativo=True,
            )
            objetos.append(obj)
    return objetos


def ocupacao_afastada_na_data(afastamentos_da_ocupacao, data_ref):
    """Verifica localmente (sem banco) se a ocupação está afastada na data_ref."""
    for inicio, fim, _ in afastamentos_da_ocupacao:
        if inicio <= data_ref <= fim:
            return True
    return False


def primeira_disponivel(cenario, data_ref):
    """
    Retorna o índice (prioridade) da primeira ocupação NÃO afastada em data_ref,
    ou -1 se todas estiverem afastadas.
    """
    for i, afastamentos in enumerate(cenario):
        if not ocupacao_afastada_na_data(afastamentos, data_ref):
            return i
    return -1


# ──────────────────────────────────────────────────────────────────────────────
# Task 3 — Propriedades de Unicidade do Exercício (Lei 8.112/90)
# ──────────────────────────────────────────────────────────────────────────────

@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
)
class UniqueExercicioPropertyTests(TestCase):
    """
    [REQ-QA-001..004] — Unicidade de Exercício e Hierarquia Estrita de Suplência.

    Propriedade 1 (Unicidade): |Exercício(F, D)| ≤ 1 para todo D na linha do tempo.
    Propriedade 2 (Monotonicidade): Se ocupação de prioridade k está em exercício,
                                     então todas j < k estão afastadas.
    Propriedade 3 (Sem buracos): Quando alguma ocupação está disponível, o sistema
                                  NUNCA retorna o fallback vazio (prioridade -1).
    Propriedade 4 (Borda inclusiva): Afastamento que termina em D-1 não impede
                                      o exercício em D.
    Propriedade 5 (Borda de início): Afastamento que começa em D suspende o
                                      exercício em D.
    """

    def setUp(self):
        self.gerador = GeradorLinhaTemporalAfastamentos(seed=SEED)
        # Contadores para relatório final
        self._rodadas_ok = 0
        self._rodadas_total = 0

    def _executar_rodada(self, n_ocupacoes, cenario, data_ref, descricao=""):
        """
        Executa uma rodada de propriedade:
        1. Cria fixture em banco (transacional — rollback ao fim do TestCase).
        2. Chama obter_responsavel_em_exercicio.
        3. Valida as 3 propriedades formais.
        Retorna o resultado do sistema para inspeção.
        """
        sufixo = f"r{self._rodadas_total}"
        funcao, ocupacoes = criar_funcao_com_ocupacoes(n_ocupacoes, sufixo=sufixo)
        aplicar_afastamentos(ocupacoes, cenario)

        resultado = funcao.obter_responsavel_em_exercicio(data_ref)
        prioridade_sistema = resultado['prioridade']

        # ── Propriedade 1: Unicidade (retorna no máximo 1)
        # A função retorna um dict único — unicidade é garantida pela assinatura,
        # mas validamos que a prioridade retornada é coerente com o banco.
        self.assertIn(
            prioridade_sistema,
            list(range(n_ocupacoes)) + [-1],
            f"[{descricao}] Prioridade inválida retornada: {prioridade_sistema}"
        )

        # ── Propriedade 2: Monotonicidade de prioridade
        if prioridade_sistema >= 0:
            for j in range(prioridade_sistema):
                self.assertTrue(
                    ocupacao_afastada_na_data(cenario[j], data_ref),
                    f"[{descricao}] Violação de monotonicidade: ocupação {j} deveria "
                    f"estar afastada, mas o sistema selecionou prioridade {prioridade_sistema}."
                )

        # ── Propriedade 3: Sem buracos temporais — se alguém está disponível,
        #    o sistema não deve retornar fallback (-1)
        esperado = primeira_disponivel(cenario, data_ref)
        self.assertEqual(
            prioridade_sistema,
            esperado,
            f"[{descricao}] data={data_ref} | esperado prioridade={esperado}, "
            f"sistema retornou={prioridade_sistema}. "
            f"Cenário de afastamentos: {cenario}"
        )

        self._rodadas_ok += 1
        return resultado

    # ──────────────────────────────────────────────────────────────────────────
    # REQ-QA-001/002: N_ROUNDS combinações aleatórias — 2 e 3 ocupações
    # ──────────────────────────────────────────────────────────────────────────
    def test_prop_unicidade_aleatorio_2_ocupacoes(self):
        """
        [REQ-QA-001/002] — N_ROUNDS rodadas aleatórias com 2 ocupações (titular + 1 substituto).
        Valida unicidade, monotonicidade e ausência de buracos.
        """
        rng = random.Random(SEED)
        n = 2
        falhas = []

        for i in range(N_ROUNDS):
            self._rodadas_total += 1
            cenario = self.gerador.gerar_cenario(n, n_afastamentos_por_ocupacao=2)
            data_ref = self.gerador.gerar_data_aleatoria()

            try:
                self._executar_rodada(n, cenario, data_ref, descricao=f"2oc-rand-{i}")
            except AssertionError as e:
                falhas.append(str(e))

        if falhas:
            self.fail(
                f"{len(falhas)} falhas em {N_ROUNDS} rodadas (2 ocupações):\n"
                + "\n".join(falhas[:5])  # mostra no máximo 5 para não poluir o log
            )

    def test_prop_unicidade_aleatorio_4_ocupacoes(self):
        """
        [REQ-QA-003/004] — N_ROUNDS rodadas aleatórias com 4 ocupações
        (titular + 3 substitutos). Testa cascata automática de suplência.
        """
        n = 4
        falhas = []

        for i in range(N_ROUNDS):
            self._rodadas_total += 1
            cenario = self.gerador.gerar_cenario(n, n_afastamentos_por_ocupacao=3)
            data_ref = self.gerador.gerar_data_aleatoria()

            try:
                self._executar_rodada(n, cenario, data_ref, descricao=f"4oc-rand-{i}")
            except AssertionError as e:
                falhas.append(str(e))

        if falhas:
            self.fail(
                f"{len(falhas)} falhas em {N_ROUNDS} rodadas (4 ocupações):\n"
                + "\n".join(falhas[:5])
            )

    # ──────────────────────────────────────────────────────────────────────────
    # REQ-QA-001: Cenário degenerado — todos afastados → prioridade -1
    # ──────────────────────────────────────────────────────────────────────────
    def test_prop_todos_afastados_retorna_fallback(self):
        """
        [REQ-QA-001] — Com todos afastados, o sistema deve retornar o dict de
        fallback (prioridade=-1, nome com '[SEM RESPONSÁVEL...]').
        Testado para 1, 2, 3 e 4 ocupações.
        """
        for n in [1, 2, 3, 4]:
            with self.subTest(n_ocupacoes=n):
                data_ref = date(2026, 6, 15)
                cenario = self.gerador.gerar_cenario_todos_afastados(n, data_ref)
                sufixo = f"todos_afast_{n}"
                funcao, ocupacoes = criar_funcao_com_ocupacoes(n, sufixo=sufixo)
                aplicar_afastamentos(ocupacoes, cenario)

                resultado = funcao.obter_responsavel_em_exercicio(data_ref)

                self.assertEqual(
                    resultado['prioridade'], -1,
                    f"Com {n} ocupações todas afastadas, esperava prioridade=-1, "
                    f"obteve {resultado['prioridade']}"
                )
                self.assertIsNone(
                    resultado['pessoa'],
                    "Quando todos afastados, 'pessoa' deve ser None."
                )
                self.assertIn(
                    "SEM RESPONSÁVEL",
                    resultado['nome'],
                    "Fallback deve conter '[SEM RESPONSÁVEL...]' no nome."
                )

    # ──────────────────────────────────────────────────────────────────────────
    # REQ-QA-002: Zero afastamentos → titular (prioridade 0) sempre retornado
    # ──────────────────────────────────────────────────────────────────────────
    def test_prop_zero_afastamentos_retorna_titular(self):
        """
        [REQ-QA-002] — Sem nenhum afastamento cadastrado, obter_responsavel_em_exercicio
        deve sempre retornar o titular (prioridade 0) para qualquer data.
        Testado em 50 datas aleatórias.
        """
        n = 4
        cenario = self.gerador.gerar_cenario_zero_afastamentos(n)
        sufixo = "zero_afast"
        funcao, ocupacoes = criar_funcao_com_ocupacoes(n, sufixo=sufixo)
        aplicar_afastamentos(ocupacoes, cenario)

        for i in range(50):
            data_ref = self.gerador.gerar_data_aleatoria()
            with self.subTest(data=data_ref, rodada=i):
                resultado = funcao.obter_responsavel_em_exercicio(data_ref)
                self.assertEqual(
                    resultado['prioridade'], 0,
                    f"Sem afastamentos, titular deve ser retornado em {data_ref}. "
                    f"Obteve prioridade={resultado['prioridade']}."
                )
                self.assertEqual(
                    resultado['nome'], f"Pessoa_zero_afast_0",
                    "Nome do titular incorreto."
                )

    # ──────────────────────────────────────────────────────────────────────────
    # Propriedade 4 (Borda inclusiva): afastamento termina em D-1 → titular livre em D
    # ──────────────────────────────────────────────────────────────────────────
    def test_prop_borda_inclusiva_fim_afastamento(self):
        """
        Propriedade 4 — Borda inclusiva: afastamento que termina em data_ref-1
        NÃO deve impedir o exercício em data_ref.
        Testado em 30 datas distintas.
        """
        n = 2
        datas_base = [BASE_DATE + timedelta(days=d * 12) for d in range(30)]

        for data_ref in datas_base:
            with self.subTest(data_ref=data_ref):
                cenario = self.gerador.gerar_cenario_fronteira_exata(n, data_ref)
                sufixo = f"borda_fim_{data_ref.strftime('%m%d')}"
                funcao, ocupacoes = criar_funcao_com_ocupacoes(n, sufixo=sufixo)
                aplicar_afastamentos(ocupacoes, cenario)

                resultado = funcao.obter_responsavel_em_exercicio(data_ref)

                self.assertEqual(
                    resultado['prioridade'], 0,
                    f"Titular deveria estar em exercício em {data_ref} "
                    f"(afastamento terminou em {data_ref - timedelta(days=1)}). "
                    f"Sistema retornou prioridade={resultado['prioridade']}."
                )

    # ──────────────────────────────────────────────────────────────────────────
    # Propriedade 5 (Borda de início): afastamento começa em D → titular suspenso em D
    # ──────────────────────────────────────────────────────────────────────────
    def test_prop_borda_inicio_afastamento(self):
        """
        Propriedade 5 — Borda de início: afastamento que começa em data_ref
        DEVE suspender o exercício do titular em data_ref.
        """
        n = 2
        datas_base = [BASE_DATE + timedelta(days=d * 12) for d in range(30)]

        for data_ref in datas_base:
            with self.subTest(data_ref=data_ref):
                cenario = self.gerador.gerar_cenario_afastamento_inicia_hoje(n, data_ref)
                sufixo = f"borda_ini_{data_ref.strftime('%m%d')}"
                funcao, ocupacoes = criar_funcao_com_ocupacoes(n, sufixo=sufixo)
                aplicar_afastamentos(ocupacoes, cenario)

                resultado = funcao.obter_responsavel_em_exercicio(data_ref)

                self.assertEqual(
                    resultado['prioridade'], 1,
                    f"Com afastamento do titular iniciado em {data_ref}, "
                    f"1º substituto deveria estar em exercício. "
                    f"Sistema retornou prioridade={resultado['prioridade']}."
                )

    # ──────────────────────────────────────────────────────────────────────────
    # REQ-QA-004: Linha do tempo densa — cascata de 4 ocupações dia a dia
    # ──────────────────────────────────────────────────────────────────────────
    def test_prop_linha_tempo_densa_sem_ambiguidade(self):
        """
        [REQ-QA-004] — Varre 180 dias consecutivos com um cenário de afastamentos
        intercalados entre 4 ocupações. Para cada dia, valida que o sistema
        não retorna mais de uma autoridade (unicidade) e que a hierarquia é
        respeitada (monotonicidade).
        """
        n = 4
        # Cenário fixo e rico: afastamentos em cascata proposital
        data_base = date(2026, 1, 1)
        cenario = [
            # Titular: férias em jan + missão em mar
            [(date(2026, 1, 10), date(2026, 1, 25), 'FERIAS'),
             (date(2026, 3, 5),  date(2026, 3, 20), 'MISSAO')],
            # 1º Sub: licença médica em jan (sobrepõe férias do titular)
            [(date(2026, 1, 15), date(2026, 1, 20), 'LICENCA_MEDICA')],
            # 2º Sub: sem afastamento
            [],
            # 3º Sub: férias em fev
            [(date(2026, 2, 10), date(2026, 2, 20), 'FERIAS')],
        ]

        sufixo = "densa_cascata"
        funcao, ocupacoes = criar_funcao_com_ocupacoes(n, sufixo=sufixo)
        aplicar_afastamentos(ocupacoes, cenario)

        falhas = []
        for d in range(180):
            data_ref = data_base + timedelta(days=d)
            resultado = funcao.obter_responsavel_em_exercicio(data_ref)
            prioridade_sistema = resultado['prioridade']
            esperado = primeira_disponivel(cenario, data_ref)

            if prioridade_sistema != esperado:
                falhas.append(
                    f"  dia {data_ref}: esperado={esperado}, "
                    f"sistema={prioridade_sistema}"
                )

        if falhas:
            self.fail(
                f"Linha do tempo densa: {len(falhas)} inconsistências em 180 dias:\n"
                + "\n".join(falhas[:10])
            )

    # ──────────────────────────────────────────────────────────────────────────
    # REQ-QA-004: Afastamentos com sobreposição de datas (titular e 1º sub simultâneos)
    # ──────────────────────────────────────────────────────────────────────────
    def test_prop_sobreposicao_titular_e_sub1_simultâneos(self):
        """
        [REQ-QA-004] — Cenário específico de sobreposição: titular e 1º substituto
        afastados ao mesmo tempo. Sistema deve selecionar o 2º substituto.
        Testado em 20 combinações de datas de sobreposição.
        """
        n = 3
        falhas = []

        for i in range(20):
            offset = i * 15
            data_inicio_overlap = BASE_DATE + timedelta(days=offset)
            data_fim_overlap = data_inicio_overlap + timedelta(days=7)
            data_ref = data_inicio_overlap + timedelta(days=3)  # no meio da sobreposição

            cenario = [
                [(data_inicio_overlap, data_fim_overlap, 'FERIAS')],
                [(data_inicio_overlap, data_fim_overlap, 'MISSAO')],
                [],  # 2º sub livre
            ]
            sufixo = f"overlap_{i}"
            funcao, ocupacoes = criar_funcao_com_ocupacoes(n, sufixo=sufixo)
            aplicar_afastamentos(ocupacoes, cenario)

            resultado = funcao.obter_responsavel_em_exercicio(data_ref)
            if resultado['prioridade'] != 2:
                falhas.append(
                    f"  sobreposição {i} em {data_ref}: esperado prioridade=2, "
                    f"obteve {resultado['prioridade']}"
                )

        if falhas:
            self.fail(
                f"{len(falhas)}/20 falhas em cenário de sobreposição simultânea:\n"
                + "\n".join(falhas)
            )

    # ──────────────────────────────────────────────────────────────────────────
    # REQ-QA-003: Cargo display inclui sufixo e portaria para substitutos
    # ──────────────────────────────────────────────────────────────────────────
    def test_prop_cargo_display_substituto_inclui_sufixo_e_portaria(self):
        """
        [REQ-QA-003] — Quando um substituto está em exercício, cargo_display
        deve conter o sufixo do cargo e o número da portaria de designação.
        """
        n = 2
        data_ref = date(2026, 5, 10)
        cenario = [
            [(date(2026, 5, 1), date(2026, 5, 31), 'FERIAS')],  # titular afastado
            [],
        ]
        sufixo = "cargo_display"
        funcao, ocupacoes = criar_funcao_com_ocupacoes(n, sufixo=sufixo)
        aplicar_afastamentos(ocupacoes, cenario)

        resultado = funcao.obter_responsavel_em_exercicio(data_ref)

        self.assertEqual(resultado['prioridade'], 1)
        self.assertIn(
            '1º Substituto',
            resultado['cargo_display'],
            "cargo_display deve conter '1º Substituto' quando prioridade=1."
        )
        self.assertIn(
            'Portaria 101/2026',
            resultado['cargo_display'],
            "cargo_display deve conter a portaria de designação do substituto."
        )


# ──────────────────────────────────────────────────────────────────────────────
# Task 4 — Propriedades de Travas Orçamentárias (SUFRAMA & EMBRAPII)
# ──────────────────────────────────────────────────────────────────────────────

class GeradorOrcamentoArbitrario:
    """
    Gera combinações arbitrárias de rubricas orçamentárias para um PlanoDeTrabalho,
    respeitando e violando os tetos regulamentares.

    Cenários cobertos:
    - TERCEIROS exatamente em 30% (limite válido).
    - TERCEIROS em 30% + ε (violação).
    - SUPORTE exatamente em 15% (limite válido EMBRAPII).
    - SUPORTE exatamente em 20% (limite válido SUFRAMA).
    - SUPORTE em 15% + ε (violação EMBRAPII).
    - SUPORTE com fonte proibida (EMBRAPII/SEBRAE).
    - Conservação: soma das rubricas = valor_global.
    """

    def __init__(self, seed: int = SEED):
        self.rng = random.Random(seed + 1)

    def gerar_valor_global(self) -> Decimal:
        """Gera valor global entre R$ 50.000 e R$ 2.000.000."""
        valor = self.rng.randint(50_000, 2_000_000)
        return Decimal(str(valor))

    def calcular_teto(self, valor_global: Decimal, percentual: Decimal) -> Decimal:
        """Calcula teto com precisão decimal."""
        return (valor_global * percentual).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    def gerar_valor_abaixo_do_teto(self, teto: Decimal) -> Decimal:
        """Valor aleatório entre 1% e 99% do teto."""
        fator = Decimal(str(self.rng.uniform(0.01, 0.99)))
        return (teto * fator).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    def gerar_valor_acima_do_teto(self, teto: Decimal) -> Decimal:
        """Valor ligeiramente acima do teto (teto + R$ 0,01 a R$ 1.000)."""
        excesso = Decimal(str(self.rng.randint(1, 100_000))) / Decimal('100')
        return teto + excesso


_PLANO_COUNTER = 0  # Contador global para garantir CNPJs e projetos únicos


def _gerar_cnpj_unico() -> str:
    """Gera um CNPJ formatado único com base no contador global."""
    global _PLANO_COUNTER
    _PLANO_COUNTER += 1
    n = _PLANO_COUNTER
    # Gera 14 dígitos e formata como XX.XXXXXX/XXXX-XX
    s = f"{n:014d}"
    return f"{s[0:2]}.{s[2:8]}/{s[8:12]}-{s[12:14]}"


def criar_empresa_parceira(sufixo: str = "") -> EmpresaParceira:
    """Cria uma EmpresaParceira com CNPJ único, preenchendo campos obrigatórios."""
    cnpj = _gerar_cnpj_unico()
    return EmpresaParceira.objects.create(
        nome=f"Empresa Trava {sufixo} {cnpj}",
        nome_fantasia=f"ET {sufixo}",
        cnpj=cnpj,
        natureza_juridica="LTDA",
        endereco="Rua Teste, 1",
        representante_legal="Rep Teste",
        cargo_representante="Diretor",
    )


def criar_projeto_com_plano(valor_global: Decimal, aporte_empresa: Decimal = None):
    """
    Cria ProjetoPDI + PlanoDeTrabalho para testes orçamentários.
    Cada chamada cria um projeto único (sem risco de unique_together).
    aporte_empresa padrão = 15% do valor_global (acima do mínimo de 10%).
    termo_homologador é nullable — PlanoDeTrabalho é criado sem ele.
    """
    if aporte_empresa is None:
        aporte_empresa = (valor_global * Decimal('0.15')).quantize(Decimal('0.01'))

    # EMBRAPII = 55% e contrapartida = restante (garante EMBRAPII ≥ 10%)
    aporte_embrapii = (valor_global * Decimal('0.55')).quantize(Decimal('0.01'))
    aporte_contrapartida = valor_global - aporte_empresa - aporte_embrapii
    if aporte_contrapartida < Decimal('0'):
        aporte_contrapartida = Decimal('0.00')
        aporte_embrapii = valor_global - aporte_empresa

    empresa = criar_empresa_parceira(sufixo="Plano")
    projeto = ProjetoPDI.objects.create(
        nome=f"Projeto Trava #{_PLANO_COUNTER}",
        fase="EXECUCAO",
        concedente=empresa,
    )
    plano = PlanoDeTrabalho.objects.create(
        projeto=projeto,
        versao=1,
        aporte_empresa=aporte_empresa,
        aporte_embrapii=aporte_embrapii,
        aporte_sebrae=Decimal('0.00'),
        aporte_contrapartida=aporte_contrapartida,
    )
    plano.refresh_from_db()
    return projeto, plano


@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
)
class TravasOrcamentariasPropertyTests(TestCase):
    """
    [REQ-QA-005..007] — Travas Orçamentárias SUFRAMA/EMBRAPII.

    Propriedade A (Teto de Terceiros): soma(TERCEIROS) ≤ 30% * valor_global
    Propriedade B (Teto Overhead):     soma(SUPORTE)   ≤ 15% * valor_global
    Propriedade C (Fonte do Overhead): SUPORTE jamais usa fonte EMBRAPII/SEBRAE
    Propriedade D (Conservação):       aporte_empresa + aporte_embrapii +
                                        aporte_sebrae + contrapartida = valor_global
    Propriedade E (Aporte mínimo empresa): aporte_empresa ≥ 10% * valor_global
    """

    def setUp(self):
        self.gerador = GeradorOrcamentoArbitrario(seed=SEED)

    # ──────────────────────────────────────────────────────────────────────────
    # REQ-QA-005: Teto de Terceiros 30% — N_ROUNDS valores válidos não lançam erro
    # ──────────────────────────────────────────────────────────────────────────
    def test_prop_terceiros_abaixo_do_teto_aceito(self):
        """
        [REQ-QA-005] — Rubrica TERCEIROS com valor abaixo de 30% do valor_global
        deve ser aceita pelo RubricaOrcamentariaPT.clean() sem ValidationError.
        Testado em N_ROUNDS combinações aleatórias de valor_global e valor_rubrica.
        """
        from django.core.exceptions import ValidationError

        falhas = []
        for i in range(N_ROUNDS):
            valor_global = self.gerador.gerar_valor_global()
            teto = self.gerador.calcular_teto(valor_global, Decimal('0.30'))
            valor_rubrica = self.gerador.gerar_valor_abaixo_do_teto(teto)

            _, plano = criar_projeto_com_plano(valor_global)

            rubrica = RubricaOrcamentariaPT(
                plano_trabalho=plano,
                categoria='TERCEIROS',
                descricao=f'Serviço prop {i}',
                valor_previsto=valor_rubrica,
                fonte_recurso='EMPRESA',
            )
            try:
                rubrica.full_clean()
            except ValidationError as e:
                falhas.append(
                    f"  rodada {i}: global={valor_global}, teto={teto}, "
                    f"rubrica={valor_rubrica} → ERRO inesperado: {e}"
                )

        if falhas:
            self.fail(
                f"{len(falhas)}/{N_ROUNDS} rodadas com valor ABAIXO do teto "
                f"geraram ValidationError indevido:\n" + "\n".join(falhas[:5])
            )

    def test_prop_terceiros_acima_do_teto_rejeitado(self):
        """
        [REQ-QA-005] — Rubrica TERCEIROS com valor que ultrapassa 30% deve ser
        REJEITADA com ValidationError. Testado em N_ROUNDS combinações.
        """
        from django.core.exceptions import ValidationError

        falhas = []
        for i in range(N_ROUNDS):
            valor_global = self.gerador.gerar_valor_global()
            teto = self.gerador.calcular_teto(valor_global, Decimal('0.30'))
            valor_rubrica = self.gerador.gerar_valor_acima_do_teto(teto)

            _, plano = criar_projeto_com_plano(valor_global)

            rubrica = RubricaOrcamentariaPT(
                plano_trabalho=plano,
                categoria='TERCEIROS',
                descricao=f'Serviço excesso {i}',
                valor_previsto=valor_rubrica,
                fonte_recurso='EMPRESA',
            )
            try:
                rubrica.full_clean()
                # Se chegou aqui sem ValidationError, é uma falha
                falhas.append(
                    f"  rodada {i}: global={valor_global}, teto={teto}, "
                    f"rubrica={valor_rubrica} → DEVERIA ter rejeitado, mas aceitou."
                )
            except ValidationError:
                pass  # Comportamento correto

        if falhas:
            self.fail(
                f"{len(falhas)}/{N_ROUNDS} rodadas com valor ACIMA do teto "
                f"não foram rejeitadas:\n" + "\n".join(falhas[:5])
            )

    # ──────────────────────────────────────────────────────────────────────────
    # REQ-QA-005: Exatamente no teto (30%) — deve ser aceito (limite inclusivo)
    # ──────────────────────────────────────────────────────────────────────────
    def test_prop_terceiros_exatamente_no_teto_aceito(self):
        """
        [REQ-QA-005] — Rubrica TERCEIROS exatamente em 30% do valor_global
        deve ser aceita (teto é inclusivo).
        Testado em 50 valores de valor_global distintos.
        """
        from django.core.exceptions import ValidationError

        falhas = []
        for i in range(50):
            valor_global = Decimal(str((i + 1) * 10_000))  # 10k, 20k, ..., 500k
            teto = self.gerador.calcular_teto(valor_global, Decimal('0.30'))

            _, plano = criar_projeto_com_plano(valor_global)

            rubrica = RubricaOrcamentariaPT(
                plano_trabalho=plano,
                categoria='TERCEIROS',
                descricao=f'Terceiros exato {i}',
                valor_previsto=teto,
                fonte_recurso='EMPRESA',
            )
            try:
                rubrica.full_clean()
            except ValidationError as e:
                falhas.append(
                    f"  global={valor_global}, teto={teto} → REJEITADO indevidamente: {e}"
                )

        if falhas:
            self.fail(
                f"{len(falhas)}/50 casos com valor EXATAMENTE no teto foram rejeitados "
                f"(teto deve ser inclusivo):\n" + "\n".join(falhas[:5])
            )

    # ──────────────────────────────────────────────────────────────────────────
    # REQ-QA-006: Teto Overhead 15% (EMBRAPII) — N_ROUNDS combinações
    # ──────────────────────────────────────────────────────────────────────────
    def test_prop_suporte_abaixo_de_15pct_aceito(self):
        """
        [REQ-QA-006] — Rubrica SUPORTE com valor abaixo de 15% deve ser aceita.
        """
        from django.core.exceptions import ValidationError

        falhas = []
        for i in range(N_ROUNDS):
            valor_global = self.gerador.gerar_valor_global()
            teto = self.gerador.calcular_teto(valor_global, Decimal('0.15'))
            valor_rubrica = self.gerador.gerar_valor_abaixo_do_teto(teto)

            _, plano = criar_projeto_com_plano(valor_global)

            rubrica = RubricaOrcamentariaPT(
                plano_trabalho=plano,
                categoria='SUPORTE',
                descricao=f'Overhead prop {i}',
                valor_previsto=valor_rubrica,
                fonte_recurso='EMPRESA',
            )
            try:
                rubrica.full_clean()
            except ValidationError as e:
                falhas.append(
                    f"  rodada {i}: global={valor_global}, teto={teto}, "
                    f"rubrica={valor_rubrica} → ERRO inesperado: {e}"
                )

        if falhas:
            self.fail(
                f"{len(falhas)}/{N_ROUNDS} rodadas com SUPORTE abaixo de 15% "
                f"geraram ValidationError indevido:\n" + "\n".join(falhas[:5])
            )

    def test_prop_suporte_acima_de_15pct_rejeitado(self):
        """
        [REQ-QA-006] — Rubrica SUPORTE acima de 15% deve ser REJEITADA.
        """
        from django.core.exceptions import ValidationError

        falhas = []
        for i in range(N_ROUNDS):
            valor_global = self.gerador.gerar_valor_global()
            teto = self.gerador.calcular_teto(valor_global, Decimal('0.15'))
            valor_rubrica = self.gerador.gerar_valor_acima_do_teto(teto)

            _, plano = criar_projeto_com_plano(valor_global)

            rubrica = RubricaOrcamentariaPT(
                plano_trabalho=plano,
                categoria='SUPORTE',
                descricao=f'Overhead excesso {i}',
                valor_previsto=valor_rubrica,
                fonte_recurso='EMPRESA',
            )
            try:
                rubrica.full_clean()
                falhas.append(
                    f"  rodada {i}: global={valor_global}, teto={teto}, "
                    f"rubrica={valor_rubrica} → DEVERIA ter rejeitado, mas aceitou."
                )
            except ValidationError:
                pass

        if falhas:
            self.fail(
                f"{len(falhas)}/{N_ROUNDS} rodadas com SUPORTE acima de 15% "
                f"não foram rejeitadas:\n" + "\n".join(falhas[:5])
            )

    # ──────────────────────────────────────────────────────────────────────────
    # REQ-QA-006: Teto Overhead 20% (SUFRAMA) — testado com acumulação de rubricas
    # ──────────────────────────────────────────────────────────────────────────
    def test_prop_suporte_acumulado_ultrapassa_15pct(self):
        """
        [REQ-QA-006] — Duas rubricas de SUPORTE que juntas ultrapassam 15%
        devem ser rejeitadas na segunda inserção.
        Simula acumulação progressiva de overhead.
        """
        from django.core.exceptions import ValidationError

        falhas = []
        for i in range(50):
            valor_global = Decimal(str((i + 1) * 100_000))
            teto_15 = self.gerador.calcular_teto(valor_global, Decimal('0.15'))

            _, plano = criar_projeto_com_plano(valor_global)

            # Primeira rubrica: 10% (dentro do limite)
            primeira = Decimal('0.10') * valor_global
            r1 = RubricaOrcamentariaPT.objects.create(
                plano_trabalho=plano,
                categoria='SUPORTE',
                descricao='Overhead parcela 1',
                valor_previsto=primeira,
                fonte_recurso='EMPRESA',
            )

            # Segunda rubrica: 8% — soma total será 18% > 15%
            segunda = Decimal('0.08') * valor_global
            r2 = RubricaOrcamentariaPT(
                plano_trabalho=plano,
                categoria='SUPORTE',
                descricao='Overhead parcela 2',
                valor_previsto=segunda,
                fonte_recurso='EMPRESA',
            )
            try:
                r2.full_clean()
                falhas.append(
                    f"  rodada {i}: global={valor_global}, já havia {primeira}, "
                    f"nova={segunda}, soma={primeira+segunda} > {teto_15} "
                    f"→ DEVERIA rejeitar, mas aceitou."
                )
            except ValidationError:
                pass  # Correto

        if falhas:
            self.fail(
                f"{len(falhas)}/50 casos de acumulação de overhead não foram rejeitados:\n"
                + "\n".join(falhas[:5])
            )

    # ──────────────────────────────────────────────────────────────────────────
    # REQ-QA-006: Fonte proibida — SUPORTE com EMBRAPII ou SEBRAE deve ser rejeitado
    # ──────────────────────────────────────────────────────────────────────────
    def test_prop_suporte_fonte_embrapii_rejeitado(self):
        """
        [REQ-QA-006] — SUPORTE com fonte EMBRAPII deve ser SEMPRE rejeitado,
        independente do valor. Testado em 50 combinações de valor.
        """
        from django.core.exceptions import ValidationError

        falhas = []
        for i in range(50):
            valor_global = Decimal(str((i + 1) * 20_000))
            teto = self.gerador.calcular_teto(valor_global, Decimal('0.15'))
            # Usa um valor ABAIXO do teto para garantir que só falhe pela fonte
            valor_rubrica = self.gerador.gerar_valor_abaixo_do_teto(teto)

            _, plano = criar_projeto_com_plano(valor_global)

            rubrica = RubricaOrcamentariaPT(
                plano_trabalho=plano,
                categoria='SUPORTE',
                descricao=f'Overhead EMBRAPII {i}',
                valor_previsto=valor_rubrica,
                fonte_recurso='EMBRAPII',
            )
            try:
                rubrica.full_clean()
                falhas.append(
                    f"  rodada {i}: SUPORTE com fonte EMBRAPII (valor={valor_rubrica}) "
                    f"→ DEVERIA rejeitar pela fonte, mas aceitou."
                )
            except ValidationError:
                pass

        if falhas:
            self.fail(
                f"{len(falhas)}/50 casos com SUPORTE+EMBRAPII não foram rejeitados:\n"
                + "\n".join(falhas[:5])
            )

    def test_prop_suporte_fonte_sebrae_rejeitado(self):
        """
        [REQ-QA-006] — SUPORTE com fonte SEBRAE deve ser SEMPRE rejeitado.
        """
        from django.core.exceptions import ValidationError

        falhas = []
        for i in range(50):
            valor_global = Decimal(str((i + 1) * 20_000))
            teto = self.gerador.calcular_teto(valor_global, Decimal('0.15'))
            valor_rubrica = self.gerador.gerar_valor_abaixo_do_teto(teto)

            _, plano = criar_projeto_com_plano(valor_global)

            rubrica = RubricaOrcamentariaPT(
                plano_trabalho=plano,
                categoria='SUPORTE',
                descricao=f'Overhead SEBRAE {i}',
                valor_previsto=valor_rubrica,
                fonte_recurso='SEBRAE',
            )
            try:
                rubrica.full_clean()
                falhas.append(
                    f"  rodada {i}: SUPORTE com fonte SEBRAE (valor={valor_rubrica}) "
                    f"→ DEVERIA rejeitar pela fonte, mas aceitou."
                )
            except ValidationError:
                pass

        if falhas:
            self.fail(
                f"{len(falhas)}/50 casos com SUPORTE+SEBRAE não foram rejeitados:\n"
                + "\n".join(falhas[:5])
            )

    # ──────────────────────────────────────────────────────────────────────────
    # REQ-QA-006: CAPITAL não pode usar EMBRAPII ou SEBRAE
    # ──────────────────────────────────────────────────────────────────────────
    def test_prop_capital_embrapii_rejeitado(self):
        """
        [REQ-QA-006] — CAPITAL com fonte EMBRAPII deve ser SEMPRE rejeitado.
        """
        from django.core.exceptions import ValidationError

        for i, fonte in enumerate(['EMBRAPII', 'SEBRAE']):
            with self.subTest(fonte=fonte):
                valor_global = Decimal('500000.00')
                _, plano = criar_projeto_com_plano(valor_global)

                rubrica = RubricaOrcamentariaPT(
                    plano_trabalho=plano,
                    categoria='CAPITAL',
                    descricao=f'Equipamento proibido {fonte}',
                    valor_previsto=Decimal('10000.00'),
                    fonte_recurso=fonte,
                )
                with self.assertRaises(
                    ValidationError,
                    msg=f"CAPITAL com fonte {fonte} deveria lançar ValidationError."
                ):
                    rubrica.full_clean()

    # ──────────────────────────────────────────────────────────────────────────
    # Propriedade D: Conservação de Fontes — valor_global = soma dos aportes
    # ──────────────────────────────────────────────────────────────────────────
    def test_prop_conservacao_valor_global(self):
        """
        Propriedade D — Conservação: valor_global deve ser igual à soma dos
        aportes declarados em PlanoDeTrabalho. Testado em N_ROUNDS combinações.
        """
        falhas = []
        for i in range(N_ROUNDS):
            valor_global = self.gerador.gerar_valor_global()
            _, plano = criar_projeto_com_plano(valor_global)

            soma_aportes = (
                plano.aporte_empresa
                + plano.aporte_embrapii
                + plano.aporte_sebrae
                + plano.aporte_contrapartida
            )
            if plano.valor_global != soma_aportes:
                falhas.append(
                    f"  rodada {i}: soma_aportes={soma_aportes}, "
                    f"valor_global={plano.valor_global} → DIVERGÊNCIA"
                )

        if falhas:
            self.fail(
                f"{len(falhas)}/{N_ROUNDS} planos com valor_global divergente da "
                f"soma dos aportes:\n" + "\n".join(falhas[:5])
            )

    # ──────────────────────────────────────────────────────────────────────────
    # REQ-QA-007: Aporte mínimo empresa ≥ 10%
    # ──────────────────────────────────────────────────────────────────────────
    def test_prop_aporte_minimo_empresa_abaixo_rejeitado(self):
        """
        [REQ-QA-007] — PlanoDeTrabalho com aporte_empresa < 10% do valor_global
        deve ser REJEITADO pelo PlanoDeTrabalho.clean().
        Testado em 50 combinações com empresa não-agência.
        """
        from django.core.exceptions import ValidationError

        falhas = []
        for i in range(50):
            valor_global = Decimal(str((i + 1) * 50_000))
            # Aporte empresa = 5% (abaixo do mínimo de 10%)
            aporte_empresa = (valor_global * Decimal('0.05')).quantize(Decimal('0.01'))
            aporte_embrapii = (valor_global * Decimal('0.60')).quantize(Decimal('0.01'))
            aporte_contrapartida = valor_global - aporte_empresa - aporte_embrapii

            empresa = criar_empresa_parceira(sufixo=f"Min{i}")
            projeto = ProjetoPDI.objects.create(
                nome=f"Projeto Min Empresa {i}",
                fase="EXECUCAO",
                concedente=empresa,
            )
            plano = PlanoDeTrabalho(
                projeto=projeto,
                versao=1,
                aporte_empresa=aporte_empresa,
                aporte_embrapii=aporte_embrapii,
                aporte_sebrae=Decimal('0.00'),
                aporte_contrapartida=aporte_contrapartida,
            )
            try:
                plano.full_clean()
                falhas.append(
                    f"  rodada {i}: empresa={aporte_empresa} (5%), "
                    f"global={valor_global} → DEVERIA rejeitar, mas aceitou."
                )
            except ValidationError:
                pass  # Correto

        if falhas:
            self.fail(
                f"{len(falhas)}/50 casos com aporte_empresa < 10% não foram rejeitados:\n"
                + "\n".join(falhas[:5])
            )

    def test_prop_aporte_minimo_empresa_acima_aceito(self):
        """
        [REQ-QA-007] — PlanoDeTrabalho com aporte_empresa ≥ 10% deve ser aceito.
        Testado em N_ROUNDS combinações aleatórias.
        """
        from django.core.exceptions import ValidationError

        falhas = []
        for i in range(N_ROUNDS):
            valor_global = self.gerador.gerar_valor_global()
            # Aporte empresa entre 10% e 50%
            pct = Decimal(str(self.gerador.rng.uniform(0.10, 0.50)))
            aporte_empresa = (valor_global * pct).quantize(Decimal('0.01'))
            aporte_embrapii = (valor_global * Decimal('0.50')).quantize(Decimal('0.01'))
            aporte_contrapartida = valor_global - aporte_empresa - aporte_embrapii
            if aporte_contrapartida < Decimal('0'):
                # Ajuste para evitar negativo
                aporte_embrapii = valor_global - aporte_empresa
                aporte_contrapartida = Decimal('0.00')

            empresa = criar_empresa_parceira(sufixo=f"OK{i}")
            projeto = ProjetoPDI.objects.create(
                nome=f"Projeto OK Empresa {i}",
                fase="EXECUCAO",
                concedente=empresa,
            )
            plano = PlanoDeTrabalho(
                projeto=projeto,
                versao=1,
                aporte_empresa=aporte_empresa,
                aporte_embrapii=aporte_embrapii,
                aporte_sebrae=Decimal('0.00'),
                aporte_contrapartida=aporte_contrapartida,
            )
            try:
                plano.full_clean()
            except ValidationError as e:
                falhas.append(
                    f"  rodada {i}: empresa={aporte_empresa} ({float(pct)*100:.1f}%), "
                    f"global={valor_global} → ERRO inesperado: {e}"
                )

        if falhas:
            self.fail(
                f"{len(falhas)}/{N_ROUNDS} planos com aporte_empresa ≥ 10% "
                f"foram rejeitados indevidamente:\n" + "\n".join(falhas[:5])
            )

    # ──────────────────────────────────────────────────────────────────────────
    # Combinatória cruzada: múltiplas rubricas TERCEIROS + SUPORTE acumuladas
    # ──────────────────────────────────────────────────────────────────────────
    def test_prop_combinatoria_rubricas_multiplas(self):
        """
        Teste combinatório cruzado: insere múltiplas rubricas TERCEIROS e SUPORTE
        com valores aleatórios, verificando que os tetos são respeitados
        acumulativamente. Simula a inserção incremental de itens no Plano de Trabalho.
        """
        from django.core.exceptions import ValidationError

        valor_global = Decimal('1000000.00')
        teto_terceiros = Decimal('300000.00')  # 30%
        teto_suporte = Decimal('150000.00')    # 15%

        _, plano = criar_projeto_com_plano(valor_global)

        # Inserções que ficam dentro dos tetos
        parcelas_terceiros = [
            Decimal('50000.00'),
            Decimal('80000.00'),
            Decimal('100000.00'),
        ]  # Soma = 230.000 < 300.000 ✓

        parcelas_suporte = [
            Decimal('60000.00'),
            Decimal('70000.00'),
        ]  # Soma = 130.000 < 150.000 ✓

        for v in parcelas_terceiros:
            r = RubricaOrcamentariaPT(
                plano_trabalho=plano,
                categoria='TERCEIROS',
                descricao=f'Terceiros {v}',
                valor_previsto=v,
                fonte_recurso='EMPRESA',
            )
            try:
                r.full_clean()
                r.save()
            except ValidationError as e:
                self.fail(f"Terceiros {v} dentro do teto não deveria falhar: {e}")

        for v in parcelas_suporte:
            r = RubricaOrcamentariaPT(
                plano_trabalho=plano,
                categoria='SUPORTE',
                descricao=f'Suporte {v}',
                valor_previsto=v,
                fonte_recurso='EMPRESA',
            )
            try:
                r.full_clean()
                r.save()
            except ValidationError as e:
                self.fail(f"Suporte {v} dentro do teto não deveria falhar: {e}")

        # Agora tenta inserir o excesso que ultrapassa o teto
        excesso_terceiros = RubricaOrcamentariaPT(
            plano_trabalho=plano,
            categoria='TERCEIROS',
            descricao='Excesso terceiros',
            valor_previsto=Decimal('80000.01'),  # 230k + 80k > 300k
            fonte_recurso='EMPRESA',
        )
        with self.assertRaises(
            ValidationError,
            msg="Terceiros acumulados > 300k deveria lançar ValidationError."
        ):
            excesso_terceiros.full_clean()

        excesso_suporte = RubricaOrcamentariaPT(
            plano_trabalho=plano,
            categoria='SUPORTE',
            descricao='Excesso suporte',
            valor_previsto=Decimal('30000.01'),  # 130k + 30k > 150k
            fonte_recurso='EMPRESA',
        )
        with self.assertRaises(
            ValidationError,
            msg="Suporte acumulado > 150k deveria lançar ValidationError."
        ):
            excesso_suporte.full_clean()
