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
