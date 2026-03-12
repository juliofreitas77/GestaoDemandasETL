from django.db import models
from django.utils import timezone

class DemandaETL(models.Model):
    COMPLEXIDADE_CHOICES = [('B', 'Baixa'), ('M', 'Média'), ('A', 'Alta')]
    STATUS_CHOICES = [('D', 'Desenvolvimento'), ('T', 'Homologação'), ('P', 'Produção')]

    # Novos Campos Solicitados
    id_demanda = models.CharField(max_length=50, verbose_name="ID da Demanda/Ticket")
    link_jira = models.URLField(max_length=500, blank=True, null=True, verbose_name="Link do Card Jira")
    data_implementacao = models.DateField(null=True, blank=True, verbose_name="Data Limite de Implantação")
    lider_tecnico = models.CharField(max_length=100, verbose_name="TL (Líder Técnico)")

    # Campos anteriores (mantidos)
    titulo = models.CharField(max_length=400)
    data_recebimento = models.DateField()
    data_implementacao = models.DateField(verbose_name="Data Limite de Implantação")
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='D')
    complexidade = models.CharField(max_length=1, choices=COMPLEXIDADE_CHOICES, default='B')
    folder_repositorio = models.CharField(max_length=100, verbose_name="Pasta no Repository Manager")
    workflow_mapping = models.CharField(max_length=255, verbose_name="Workflow/Mapping")
    origem_destino = models.CharField(max_length=255, help_text="Ex: Oracle CRM -> Teradata DW")
    descricao_solucao = models.TextField(verbose_name="O que foi desenvolvido")
    script_sql_shell = models.TextField(blank=True, verbose_name="Queries SQL ou Scripts Shell")
    arquivo_tecnico = models.FileField(upload_to='documentos_pc/', verbose_name="Anexo (Proposta Técnica)")

    def __str__(self):
        return f"{self.id_demanda} - {self.titulo}"