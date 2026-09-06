from decimal import Decimal

from django.contrib.auth.models import User
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from cadastros.models import EmpresaParceira, MembroEquipe, ProjetoPDI
from patrimonio.models import BemPatrimonial


@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
)
class MinutaTermoDoacaoProjetoTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        User.objects.create_superuser('admin_inc', 'admin@inc.com', 'senha123')
        self.membro_user = User.objects.create_user(
            'membro_inc',
            'membro@inc.com',
            'senha123',
        )
        User.objects.create_user('leigo_inc', 'leigo@inc.com', 'senha123')

        self.empresa = EmpresaParceira.objects.create(
            nome="Empresa Doacao",
            cnpj="33.444.555/0001-66",
            natureza_juridica="LTDA",
            representante_legal="Rep Doacao",
            cargo_representante="Dir",
        )
        self.projeto = ProjetoPDI.objects.create(
            nome="Projeto Incorporacao Teste",
            fase="PRESTACAO_CONTAS",
            concedente=self.empresa,
        )
        MembroEquipe.objects.create(
            projeto=self.projeto,
            usuario=self.membro_user,
            papel='GESTOR',
        )

        BemPatrimonial.objects.create(
            projeto=self.projeto,
            patrimonio_ifam="IFAM-2001",
            descricao="Servidor Rack 2U",
            valor=Decimal("12000.00"),
        )
        self.url = reverse(
            'incorporacao:gerar_termo_doacao_projeto',
            args=[self.projeto.id],
        )

    def test_rbac_acesso_leigo_bloqueado(self):
        self.client.login(username='leigo_inc', password='senha123')

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)

    def test_minuta_doacao_renderizacao_sucesso(self):
        self.client.login(username='membro_inc', password='senha123')

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_itens'], 1)
        self.assertEqual(response.context['valor_total'], Decimal("12000.00"))
        self.assertContains(response, "Servidor Rack 2U")
        self.assertContains(response, "TERMO DE DOAÇÃO")
