from django.contrib import admin
from .models import DemandaETL
from django.forms import Textarea
from django.db import models

@admin.register(DemandaETL)
class DemandaETLAdmin(admin.ModelAdmin):
    # Colunas que aparecerão na listagem
    list_display = ('folder_repositorio', 'titulo', 'status', 'complexidade', 'data_recebimento')
    # Filtros laterais
    list_filter = ('status', 'complexidade', 'folder_repositorio')
    # Barra de busca
    search_fields = ('titulo', 'workflow_mapping', 'descricao_solucao')

    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 10, 'cols': 80, 'style': 'font-family: monospace;'})},
    }