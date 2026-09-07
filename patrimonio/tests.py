from decimal import Decimal

from django.contrib.auth.models import User
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from cadastros.models import EmpresaParceira, MembroEquipe, PerfilServidor, PessoaFisica, ProjetoPDI
from central_servicos.models import Ambiente, Predio, TipoAmbiente
from patrimonio.models import BemPatrimonial
from patrimonio.views import gerar_qr_code_svg


@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    },
    STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage',
)
class ConferenciaBensProjetoTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.super_user = User.objects.create_superuser(
            'admin_pat',
            'admin@pat.com',
            'senha123',
        )
        self.membro_user = User.objects.create_user(
            'membro_pat',
            'membro@pat.com',
            'senha123',
        )
        User.objects.create_user(
            'leigo_pat',
            'leigo@pat.com',
            'senha123',
        )

        self.empresa = EmpresaParceira.objects.create(
            nome="Empresa Pat",
            cnpj="11.222.333/0001-44",
            natureza_juridica="LTDA",
            representante_legal="Rep",
            cargo_representante="Dir",
        )
        self.projeto = ProjetoPDI.objects.create(
            nome="Projeto Patrimonio Teste",
            fase="EXECUCAO",
            concedente=self.empresa,
        )
        MembroEquipe.objects.create(
            projeto=self.projeto,
            usuario=self.membro_user,
            papel='GESTOR',
        )

        self.bem1 = BemPatrimonial.objects.create(
            projeto=self.projeto,
            patrimonio_ifam="IFAM-1001",
            descricao="Osciloscópio Digital 100MHz",
            valor=Decimal("4500.00"),
        )
        self.bem2 = BemPatrimonial.objects.create(
            projeto=self.projeto,
            patrimonio_doador="DOADOR-500",
            descricao="Fonte de Alimentação DC",
            valor=Decimal("1500.00"),
        )
        self.url = reverse(
            'patrimonio:conferir_bens_projeto',
            args=[self.projeto.id],
        )

    def test_rbac_acesso_leigo_bloqueado(self):
        self.client.login(username='leigo_pat', password='senha123')

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)

    def test_conferencia_bens_kpis_sucesso(self):
        self.client.login(username='membro_pat', password='senha123')

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_itens'], 2)
        self.assertEqual(response.context['valor_total'], Decimal("6000.00"))
        self.assertEqual(response.context['tombados_ifam'], 1)
        self.assertEqual(response.context['pendentes_tombamento'], 1)
        self.assertContains(response, "Osciloscópio Digital 100MHz")


@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    },
    STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage',
)
class EtiquetasPatrimonioTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        # 1. Superuser
        self.super_user = User.objects.create_superuser('super_etq', 'super@etq.com', 'senha123')
        # 2. Servidor com SIAPE ativo (Canônico)
        self.servidor_user = User.objects.create_user('servidor_etq', 'servidor@etq.com', 'senha123')
        self.pf_servidor = PessoaFisica.objects.create(
            user=self.servidor_user,
            nome="Prof Servidor Efetivo",
            cpf="999.888.777-66",
        )
        self.perfil_servidor = PerfilServidor.objects.create(
            pessoa=self.pf_servidor,
            siape="1928374",
            cargo="Docente EBTT",
            lotacao="Polo de Inovação",
            ativo=True,
        )
        # 3. Coordenador de Projeto
        self.coord_user = User.objects.create_user('coord_etq', 'coord@etq.com', 'senha123')
        self.pf_coord = PessoaFisica.objects.create(
            user=self.coord_user,
            nome="Coordenador do Projeto",
            cpf="111.222.333-44",
        )
        # 4. Membro de Equipe
        self.membro_user = User.objects.create_user('membro_etq', 'membro@etq.com', 'senha123')
        # 5. Usuário Leigo (Sem alçada)
        self.leigo_user = User.objects.create_user('leigo_etq', 'leigo@etq.com', 'senha123')
        # Estruturas de Apoio
        self.empresa = EmpresaParceira.objects.create(
            nome="Parceira Tech",
            cnpj="55.666.777/0001-88",
            natureza_juridica="LTDA",
            representante_legal="Gestor",
            cargo_representante="Diretor",
        )
        self.projeto = ProjetoPDI.objects.create(
            nome="Projeto Automação Polo",
            fase="EXECUCAO",
            concedente=self.empresa,
            coordenador=self.pf_coord,
        )
        MembroEquipe.objects.create(
            projeto=self.projeto,
            usuario=self.membro_user,
            papel='ANALISTA',
        )
        self.tipo_amb = TipoAmbiente.objects.create(nome="Laboratório de Robótica")
        self.predio = Predio.objects.create(nome="Bloco Central", sigla="BC")
        self.ambiente = Ambiente.objects.create(
            nome="Lab 01 - Robótica Avançada",
            predio=self.predio,
            tipo=self.tipo_amb,
        )
        self.bem = BemPatrimonial.objects.create(
            projeto=self.projeto,
            ambiente=self.ambiente,
            patrimonio_ifam="IFAM-QR-001",
            descricao="Braço Robótico Articulado 6 Eixos",
            valor=Decimal("25000.00"),
        )
        self.bem_sem_tombo = BemPatrimonial.objects.create(
            projeto=self.projeto,
            ambiente=self.ambiente,
            descricao="Kit Sensores IoT Recém Chegado",
            valor=Decimal("1200.00"),
        )
        self.url_etiqueta_bem = reverse('patrimonio:gerar_etiqueta_patrimonial', args=[self.bem.id])
        self.url_etiqueta_sem_tombo = reverse('patrimonio:gerar_etiqueta_patrimonial', args=[self.bem_sem_tombo.id])
        self.url_etiquetas_ambiente = reverse('patrimonio:gerar_etiquetas_ambiente', args=[self.ambiente.id])

    def test_01_geracao_qr_code_svg_formato_vetorial(self):
        """Valida que o ReportLab gera SVG nativo com elementos rect vetoriais sem Cairo."""
        payload = "ARGUS-BEM:IFAM-QR-001|Braço Robótico"
        svg_content = gerar_qr_code_svg(payload, tamanho=90)
        self.assertIn('<svg', svg_content)
        self.assertIn('<rect', svg_content)
        self.assertGreater(len(svg_content), 100)

    def test_02_rbac_etiqueta_individual_superusuario(self):
        """Superusuário possui acesso irrestrito à impressão de etiquetas."""
        self.client.login(username='super_etq', password='senha123')
        response = self.client.get(self.url_etiqueta_bem)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "IFAM-QR-001")
        self.assertContains(response, "Braço Robótico")

    def test_03_rbac_etiqueta_individual_coordenador(self):
        """Coordenador do projeto pode imprimir etiquetas dos bens do seu projeto."""
        self.client.login(username='coord_etq', password='senha123')
        response = self.client.get(self.url_etiqueta_bem)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "IFAM-QR-001")

    def test_04_rbac_etiqueta_individual_membro_equipe(self):
        """Membro da equipe do projeto pode emitir etiquetas dos bens do projeto."""
        self.client.login(username='membro_etq', password='senha123')
        response = self.client.get(self.url_etiqueta_bem)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "IFAM-QR-001")

    def test_05_rbac_etiqueta_individual_usuario_sem_permissao(self):
        """Usuário comum sem vínculo ao projeto ou SIAPE recebe 403 Forbidden."""
        self.client.login(username='leigo_etq', password='senha123')
        response = self.client.get(self.url_etiqueta_bem)
        self.assertEqual(response.status_code, 403)

    def test_06_rbac_etiquetas_ambiente_servidor_autorizado(self):
        """Servidor efetivo com SIAPE pode emitir o lote de etiquetas de um ambiente."""
        self.client.login(username='servidor_etq', password='senha123')
        response = self.client.get(self.url_etiquetas_ambiente)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Lab 01 - Robótica Avançada")
        self.assertContains(response, "IFAM-QR-001")

    def test_07_rbac_etiquetas_ambiente_usuario_comum_bloqueado(self):
        """Usuário leigo sem SIAPE é bloqueado de emitir lote do ambiente com 403."""
        self.client.login(username='leigo_etq', password='senha123')
        response = self.client.get(self.url_etiquetas_ambiente)
        self.assertEqual(response.status_code, 403)

    def test_08_fallback_identificador_bem_sem_tombamento(self):
        """Bens ainda sem número IFAM ou doador utilizam identificador de fallback gracioso ID-<id>."""
        self.client.login(username='super_etq', password='senha123')
        response = self.client.get(self.url_etiqueta_sem_tombo)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f"ID-{self.bem_sem_tombo.id}")
        self.assertContains(response, "Kit Sensores IoT")
