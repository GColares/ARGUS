from decimal import Decimal

from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone

from cadastros.models import Fornecedor, PessoaFisica, PerfilServidor
from almoxarifado.models import (
    PerfilUsuario, NotaFiscalAlmoxarifado, ProdutoAlmoxarifado, TermoRME,
)


@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
)
class AlmoxarifadoTestCase(TestCase):
    """
    Suíte de testes do módulo Almoxarifado — Fase 5 / Etapa 5.1.

    Correções aplicadas sobre o Handoff original:
    - Fornecedor criado com os campos obrigatórios de PessoaJuridica
      (endereco, representante_legal, cargo_representante).
    - ProjetoPDI removido do setUp (não era usado em nenhum teste).
    - Servidor criado via caminho canônico (PessoaFisica + PerfilServidor),
      que é validado pelo cenário 1 do @servidor_efetivo_required.
    - nf.refresh_from_db() adicionado no Teste 08 para garantir leitura
      atualizada do campo FileField.
    """

    def setUp(self):
        self.client = Client()

        # ── 1. Usuário comum (sem perfil de servidor) ──
        self.user_comum = User.objects.create_user(username='comum', password='123')

        # ── 2. Servidor público via caminho canônico (PessoaFisica + PerfilServidor) ──
        # O @servidor_efetivo_required valida request.user.pessoa_fisica.perfil_servidor.
        self.servidor = User.objects.create_user(username='servidor_siape', password='123')
        pessoa_fisica = PessoaFisica.objects.create(
            nome='Servidor Teste SIAPE',
            cpf='000.111.222-33',
            user=self.servidor,
        )
        PerfilServidor.objects.create(
            pessoa=pessoa_fisica,
            siape='9876543',
            cargo='Assistente em Administração',
            lotacao='Polo de Inovação',
            ativo=True,
        )

        # ── 3. Fornecedor com todos os campos obrigatórios de PessoaJuridica ──
        self.fornecedor = Fornecedor.objects.create(
            nome='Fornecedor Teste LTDA',
            cnpj='12.345.678/0001-90',
            natureza_juridica='LTDA',
            endereco='Rua dos Testes, 100',
            representante_legal='Rep Fornecedor',
            cargo_representante='Sócio-Gerente',
            sigla='FORN_TESTE',
        )

    # ------------------------------------------------------------------ #
    # Teste 01 — Dashboard vazio                                          #
    # ------------------------------------------------------------------ #
    def test_01_home_almoxarifado_vazio(self):
        """Dashboard carrega corretamente com 0 notas e valores zerados (HTTP 200)."""
        self.client.login(username='comum', password='123')
        resp = self.client.get(reverse('almoxarifado:home_almoxarifado'))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context['indicadores']['total_notas'], 0)
        self.assertEqual(resp.context['indicadores']['valor_acumulado'], Decimal('0.00'))

    # ------------------------------------------------------------------ #
    # Teste 02 — Dashboard com agregações                                 #
    # ------------------------------------------------------------------ #
    def test_02_home_almoxarifado_com_agregacoes(self):
        """Dashboard agrega corretamente totais de notas, produtos e descontos."""
        NotaFiscalAlmoxarifado.objects.create(
            numero='NF-100',
            serie='1',
            data_emissao=timezone.now().date(),
            fornecedor=self.fornecedor,
            valor_total_produtos=Decimal('1000.00'),
            valor_desconto=Decimal('50.00'),
            valor_total_nota=Decimal('950.00'),
            destinatario_nome='IFAM Polo',
            destinatario_cnpj='10.792.928/0001-00',
        )
        self.client.login(username='comum', password='123')
        resp = self.client.get(reverse('almoxarifado:home_almoxarifado'))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context['indicadores']['total_notas'],    1)
        self.assertEqual(resp.context['indicadores']['valor_acumulado'], Decimal('950.00'))
        self.assertEqual(resp.context['indicadores']['valor_produtos'],  Decimal('1000.00'))
        self.assertEqual(resp.context['indicadores']['valor_desconto'],  Decimal('50.00'))

    # ------------------------------------------------------------------ #
    # Teste 03 — Validação clean(): trava fiscal de líquido               #
    # ------------------------------------------------------------------ #
    def test_03_validacao_clean_nota_fiscal_inconsistencia(self):
        """Dispara ValidationError se valor_total_nota for menor que produtos − desconto."""
        nf = NotaFiscalAlmoxarifado(
            numero='NF-999',
            serie='1',
            data_emissao=timezone.now().date(),
            fornecedor=self.fornecedor,
            valor_total_produtos=Decimal('500.00'),
            valor_desconto=Decimal('0.00'),
            valor_total_nota=Decimal('400.00'),   # Inválido: 400 < 500 - 0.01
            destinatario_nome='IFAM',
            destinatario_cnpj='10.792.928/0001-00',
        )
        with self.assertRaises(ValidationError):
            nf.clean()

    # ------------------------------------------------------------------ #
    # Teste 04 — inconsistencia_produtos com tolerância de 2 centavos     #
    # ------------------------------------------------------------------ #
    def test_04_property_inconsistencia_produtos_tolerancia_centavos(self):
        """
        Diferença de 1 centavo (dentro da tolerância de 2¢) → False.
        Diferença de 10 centavos (fora da tolerância) → True.
        soma_itens_calculada usa aggregate() no banco a cada chamada —
        não precisa de refresh_from_db() na instância.
        """
        nf = NotaFiscalAlmoxarifado.objects.create(
            numero='NF-200',
            serie='1',
            data_emissao=timezone.now().date(),
            fornecedor=self.fornecedor,
            valor_total_produtos=Decimal('100.00'),
            valor_total_nota=Decimal('100.00'),
            destinatario_nome='IFAM',
            destinatario_cnpj='10.792.928/0001-00',
        )
        # Item com R$ 99,99 → diferença de 1¢ → dentro da tolerância
        ProdutoAlmoxarifado.objects.create(
            nota_fiscal=nf,
            numero_item=1,
            descricao='Insumo A',
            quantidade=Decimal('1'),
            unidade_comercial='UN',
            valor_unitario=Decimal('99.99'),
            valor_total=Decimal('99.99'),
        )
        self.assertFalse(nf.inconsistencia_produtos,
                         "Diferença de 1¢ deve estar dentro da tolerância de 2¢.")

        # Atualiza via ORM para R$ 99,90 → diferença de 10¢ → fora da tolerância
        ProdutoAlmoxarifado.objects.filter(nota_fiscal=nf).update(
            valor_unitario=Decimal('99.90'),
            valor_total=Decimal('99.90'),
        )
        # soma_itens_calculada sempre consulta o banco — sem cache na instância
        self.assertTrue(nf.inconsistencia_produtos,
                        "Diferença de 10¢ deve estar fora da tolerância de 2¢.")

    # ------------------------------------------------------------------ #
    # Teste 05 — Unicidade (numero, fornecedor)                           #
    # ------------------------------------------------------------------ #
    def test_05_unicidade_numero_fornecedor(self):
        """Não é possível criar duas notas com o mesmo número e fornecedor."""
        NotaFiscalAlmoxarifado.objects.create(
            numero='NF-DUP',
            serie='1',
            data_emissao=timezone.now().date(),
            fornecedor=self.fornecedor,
            destinatario_nome='IFAM',
            destinatario_cnpj='10.792.928/0001-00',
        )
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            NotaFiscalAlmoxarifado.objects.create(
                numero='NF-DUP',
                serie='2',
                data_emissao=timezone.now().date(),
                fornecedor=self.fornecedor,
                destinatario_nome='IFAM',
                destinatario_cnpj='10.792.928/0001-00',
            )

    # ------------------------------------------------------------------ #
    # Teste 06 — @servidor_efetivo_required bloqueia usuário comum (403)  #
    # ------------------------------------------------------------------ #
    def test_06_servidor_efetivo_bloqueia_usuario_comum(self):
        """Usuário sem SIAPE recebe HTTP 403 no Termo RME."""
        nf = NotaFiscalAlmoxarifado.objects.create(
            numero='NF-300',
            serie='1',
            data_emissao=timezone.now().date(),
            fornecedor=self.fornecedor,
            destinatario_nome='IFAM',
            destinatario_cnpj='10.792.928/0001-00',
        )
        self.client.login(username='comum', password='123')
        resp = self.client.get(reverse('almoxarifado:ver_termo_rme', args=[nf.id]))
        self.assertEqual(resp.status_code, 403)

    # ------------------------------------------------------------------ #
    # Teste 07 — @servidor_efetivo_required libera servidor efetivo (200) #
    # ------------------------------------------------------------------ #
    def test_07_servidor_efetivo_libera_servidor_siape(self):
        """Servidor efetivo com SIAPE ativo acessa o Termo RME (HTTP 200)."""
        nf = NotaFiscalAlmoxarifado.objects.create(
            numero='NF-301',
            serie='1',
            data_emissao=timezone.now().date(),
            fornecedor=self.fornecedor,
            destinatario_nome='IFAM',
            destinatario_cnpj='10.792.928/0001-00',
        )
        self.client.login(username='servidor_siape', password='123')
        resp = self.client.get(reverse('almoxarifado:ver_termo_rme', args=[nf.id]))
        self.assertEqual(resp.status_code, 200)

    # ------------------------------------------------------------------ #
    # Teste 08 — Upload de Termo: rejeita arquivo não-PDF                 #
    # ------------------------------------------------------------------ #
    def test_08_anexar_termo_assinado_rejeita_nao_pdf(self):
        """Upload de arquivo não-PDF é rejeitado; campo termo_recebimento_assinado permanece vazio."""
        nf = NotaFiscalAlmoxarifado.objects.create(
            numero='NF-302',
            serie='1',
            data_emissao=timezone.now().date(),
            fornecedor=self.fornecedor,
            destinatario_nome='IFAM',
            destinatario_cnpj='10.792.928/0001-00',
        )
        self.client.login(username='servidor_siape', password='123')
        arquivo_falso = SimpleUploadedFile(
            'termo.txt', b'conteudo texto puro', content_type='text/plain',
        )
        resp = self.client.post(
            reverse('almoxarifado:anexar_termo', args=[nf.id]),
            {'termo_pdf': arquivo_falso},
            follow=True,
        )
        self.assertEqual(resp.status_code, 200)
        # refresh_from_db() necessário: FileField é lido do banco, não da instância em memória
        nf.refresh_from_db()
        self.assertFalse(
            bool(nf.termo_recebimento_assinado),
            "Arquivo não-PDF não deve ser salvo no campo termo_recebimento_assinado.",
        )
