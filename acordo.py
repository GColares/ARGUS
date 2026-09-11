
class AcordoDeParceria(InstrumentoJuridicoBase):
    """Entidade macro jurídica para os novos acordos sob o Marco Legal de CT&I."""
    projeto = models.ForeignKey('ProjetoPDI', on_delete=models.CASCADE, related_name='acordos_parceria', null=True, blank=True, verbose_name="Projeto Mestre")
    concedente = models.ForeignKey('PessoaJuridica', on_delete=models.CASCADE, related_name='acordos_concedidos', verbose_name="Concedente (Empresa/Agência)")
    convenente = models.ForeignKey('ICT', on_delete=models.PROTECT, related_name='convenente_em_acordo', verbose_name="Convenente")
    interveniente = models.ForeignKey(FundacaoApoio, on_delete=models.PROTECT, related_name='interveniente_em_acordo', verbose_name="Interveniente")

    class Meta:
        verbose_name = "Acordo de Parceria"
        verbose_name_plural = "Acordos de Parceria"
        constraints = [
            models.UniqueConstraint(
                fields=['tipo_instrumento', 'sequencial', 'ano'],
                condition=models.Q(sequencial__isnull=False, ano__isnull=False),
                name='unique_seq_ano_acordo_parceria'
            )
        ]

    def __str__(self):
        return f"{self.numero or 'Sem Número'} ({self.concedente.sigla or self.concedente.nome_fantasia or self.concedente.nome})"

    @property
    def nome_especie(self):
        return self.tipo_instrumento_fk.nome if self.tipo_instrumento_fk else 'Acordo de Parceria'

    @property
    def nome_especie_plural(self):
        return self.tipo_instrumento_fk.nome if self.tipo_instrumento_fk else 'Acordos de Parceria'

    @property
    def sigla_especie(self):
        return self.tipo_instrumento_fk.sigla if self.tipo_instrumento_fk else 'AP'

