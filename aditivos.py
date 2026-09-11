class TermoAditivo(models.Model):
    """Termo Aditivo unificado para todos os Instrumentos Jurídicos."""
    instrumento = models.ForeignKey(InstrumentoJuridicoBase, on_delete=models.CASCADE, related_name='aditivos')
    numero = models.CharField(max_length=50, verbose_name="Número do Aditivo")
    data_assinatura = models.DateField(verbose_name="Data de Assinatura")
    nova_data_fim = models.DateField(blank=True, null=True, verbose_name="Nova Data Fim (Prorrogação)")
    valor_acrescimo = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Valor Acrescido (R$)")
    objeto = models.TextField(verbose_name="Objeto / Justificativa")
    arquivo_pdf = models.FileField(upload_to='aditivos/', blank=True, null=True)

    class Meta:
        verbose_name = "Termo Aditivo"
        verbose_name_plural = "Termos Aditivos"
        ordering = ['-data_assinatura']

    def __str__(self):
        return f"Aditivo {self.numero} - {self.instrumento.numero}"

class TermoEncerramento(models.Model):
    """Termo de Encerramento unificado para todos os Instrumentos Jurídicos."""
    instrumento = models.OneToOneField(InstrumentoJuridicoBase, on_delete=models.CASCADE, related_name='encerramento')
    data_encerramento = models.DateField(verbose_name="Data do Encerramento")
    motivo_rescisao = models.TextField(verbose_name="Motivo / Justificativa")
    oficio_comunicacao = models.CharField(max_length=100, blank=True, null=True, verbose_name="Nº do Ofício")
    arquivo_pdf = models.FileField(upload_to='encerramentos/', blank=True, null=True)

    class Meta:
        verbose_name = "Termo de Encerramento"
        verbose_name_plural = "Termos de Encerramento"

    def __str__(self):
        return f"Encerramento - {self.instrumento.numero}"

