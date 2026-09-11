    def convenio(self):
        """Retorna o primeiro convênio associado."""
        return self.convenios.first()

    @property
    def acordo_parceria(self):
        """Retorna o primeiro acordo de parceria associado."""
        return self.acordos_parceria.first()

    @property
    def instrumento_vinculado(self):
        """Retorna o acordo de parceria ou convênio principal vinculado a este projeto."""
        return self.acordo_parceria or self.convenio
