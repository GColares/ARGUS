import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'argus_core.settings')
django.setup()

from cadastros.models import PessoaJuridica, TermoDeParceria, PlanoDeTrabalho, ProjetoPDI
from datetime import date

def run():
    print("Criando Pessoas Jurídicas...")
    
    ifam, _ = PessoaJuridica.objects.get_or_create(
        cnpj='10.792.928/0001-00',
        defaults={
            'nome': 'Instituto Federal De Educação, Ciência E Tecnologia Do Amazonas - IFAM',
            'natureza_juridica': 'Autarquia Federal',
            'endereco': 'Rua Ferreira Pena, 1109, Centro, Cidade: Manaus - AM CEP: 69025-010',
            'representante_legal': 'Jaime Cavalcante Alves',
            'nacionalidade_representante': 'Brasileira',
            'estado_civil_representante': 'Casado',
            'cargo_representante': 'Reitor',
            'ato_nomeacao': 'Decreto de 21 de junho de 2023, publicado em: 21/06/2023 | Edição: 116-A | Seção: 2 - Extra A | Página: 1'
        }
    )

    empresa, _ = PessoaJuridica.objects.get_or_create(
        cnpj='60.369.979/0001-00',
        defaults={
            'nome': 'LC Indústria e Comercio de Frutas LTDA.',
            'natureza_juridica': 'Sociedade Empresária Limitada (LTDA)',
            'endereco': 'Avenida Bom Jesus, no 888, Colônia Terra Nova, Manaus - AM, CEP: 69.015-300',
            'representante_legal': 'Letícia Castro Barreto',
            'nacionalidade_representante': 'Brasileira',
            'estado_civil_representante': 'Solteira',
            'cargo_representante': 'Representante',
            'ato_nomeacao': ''
        }
    )

    faepi, _ = PessoaJuridica.objects.get_or_create(
        cnpj='04.623.300/0001-88',
        defaults={
            'nome': 'Fundação de Apoio ao Ensino, Pesquisa, Extensão e Interiorização do IFAM -FAEPI',
            'natureza_juridica': 'Fundação de direito privado',
            'endereco': 'Av. Borba, 144 - Cidade: Manaus-AM CEP: 69065-030',
            'representante_legal': 'Luana Marinho Monteiro',
            'nacionalidade_representante': 'Brasileira',
            'estado_civil_representante': 'Solteira',
            'cargo_representante': 'Diretora Executiva',
            'ato_nomeacao': ''
        }
    )

    print("Criando Termo de Parceria e vinculando ao Projeto PDI...")
    projeto = ProjetoPDI.objects.first()
    if projeto:
        termo, created = TermoDeParceria.objects.get_or_create(
            numero='0001/2026',
            defaults={
                'objeto': 'Desenvolvimento de pesquisa e inovação tecnológica',
                'concedente': empresa,
                'convenente': ifam,
                'interveniente': faepi,
                'data_assinatura': date.today(),
            }
        )
        
        if created:
            PlanoDeTrabalho.objects.create(
                termo_parceria=termo,
                versao=1,
                abordagem_tecnica='Desenvolvimento experimental',
                abordagem_financeira='Repasse de recursos',
                produto_entregue='Relatório de Pesquisa'
            )

        projeto.termo_parceria = termo
        projeto.save()
        print("Projeto vinculado ao Termo de Parceria com sucesso!")
    else:
        print("Nenhum ProjetoPDI encontrado.")

if __name__ == "__main__":
    run()
