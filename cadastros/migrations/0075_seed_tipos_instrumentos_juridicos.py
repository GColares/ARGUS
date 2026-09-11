from django.db import migrations


def seed_tipos_instrumentos(apps, schema_editor):
    TipoInstrumentoJuridico = apps.get_model('cadastros', 'TipoInstrumentoJuridico')
    TermoDeParceria = apps.get_model('cadastros', 'TermoDeParceria')
    TermoCooperacao = apps.get_model('cadastros', 'TermoCooperacao')

    tipos_padrao = [
        {
            'nome': 'Acordo de Parceria para P&D&I',
            'sigla': 'AP',
            'fundamentacao_legal': 'Art. 9º da Lei nº 10.973/2004 e Decreto nº 9.283/2018',
            'descricao': 'Instrumento formal tripartite para pesquisa, desenvolvimento científico e inovação entre ICT pública, empresa financiadora e fundação de apoio como interveniente-anuente gestora.',
            'exige_fundacao_apoio': True,
            'ativo': True,
        },
        {
            'nome': 'Termo de Cooperação Técnica',
            'sigla': 'TC',
            'fundamentacao_legal': 'Art. 116 da Lei nº 8.666/1993 e Marco Legal de CT&I',
            'descricao': 'Instrumento de cooperação institucional e técnica para conjugação de esforços em programas temáticos e projetos sem transferência voluntária obrigatória de recursos.',
            'exige_fundacao_apoio': False,
            'ativo': True,
        },
        {
            'nome': 'Acordo de Confidencialidade e Sigilo (NDA)',
            'sigla': 'NDA',
            'fundamentacao_legal': 'Lei nº 9.279/1996 e Marco Legal de CT&I',
            'descricao': 'Instrumento para resguardo de informações confidenciais, segredos industriais e propriedade intelectual prévia em negociações e projetos colaborativos.',
            'exige_fundacao_apoio': False,
            'ativo': True,
        },
        {
            'nome': 'Prestação de Serviços Técnicos Especializados',
            'sigla': 'STE',
            'fundamentacao_legal': 'Art. 8º da Lei nº 10.973/2004 e Decreto nº 9.283/2018',
            'descricao': 'Contrato para prestação de serviços técnicos de alta complexidade e consultorias tecnológicas por pesquisadores e laboratórios da ICT.',
            'exige_fundacao_apoio': False,
            'ativo': True,
        },
        {
            'nome': 'Contrato de Licenciamento / Transferência de Tecnologia',
            'sigla': 'CLTT',
            'fundamentacao_legal': 'Art. 6º da Lei nº 10.973/2004 e Resoluções Institucionais',
            'descricao': 'Instrumento para concessão de exploração comercial de patentes, registros de software e know-how desenvolvidos pela instituição.',
            'exige_fundacao_apoio': False,
            'ativo': True,
        },
        {
            'nome': 'Termo de Compartilhamento de Infraestrutura / Laboratórios',
            'sigla': 'TCIL',
            'fundamentacao_legal': 'Art. 4º da Lei nº 10.973/2004 e Decreto nº 9.283/2018',
            'descricao': 'Permissão de uso compartilhado de laboratórios, equipamentos e instalações de pesquisa da ICT por empresas parceiras e startups.',
            'exige_fundacao_apoio': False,
            'ativo': True,
        },
        {
            'nome': 'Convênio de P&D&I',
            'sigla': 'CV',
            'fundamentacao_legal': 'Lei nº 8.666/1993 (Regime Anterior)',
            'descricao': 'Instrumento de convênio celebrado sob a vigência da legislação anterior ou transferências governamentais tradicionais.',
            'exige_fundacao_apoio': True,
            'ativo': True,
        },
    ]

    mapa_tipos = {}
    for dados in tipos_padrao:
        obj, _ = TipoInstrumentoJuridico.objects.get_or_create(
            sigla=dados['sigla'],
            defaults=dados
        )
        mapa_tipos[dados['sigla']] = obj

    # Backfill em TermoDeParceria
    ap = mapa_tipos.get('AP')
    cv = mapa_tipos.get('CV')
    for tp in TermoDeParceria.objects.all():
        if not tp.tipo_instrumento_fk_id:
            if getattr(tp, 'tipo_instrumento', None) == 'CONVENIO':
                tp.tipo_instrumento_fk = cv
            else:
                tp.tipo_instrumento_fk = ap
            tp.save(update_fields=['tipo_instrumento_fk'])

    # Backfill em TermoCooperacao
    tc = mapa_tipos.get('TC')
    for termo in TermoCooperacao.objects.all():
        if not termo.tipo_instrumento_fk_id:
            termo.tipo_instrumento_fk = tc
            termo.save(update_fields=['tipo_instrumento_fk'])


def reverter_seed(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('cadastros', '0074_tipoinstrumentojuridico_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_tipos_instrumentos, reverter_seed),
    ]
