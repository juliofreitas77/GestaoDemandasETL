from django.contrib import admin
from .models import DemandaETL

@admin.register(DemandaETL)
class DemandaETLAdmin(admin.ModelAdmin):
    # Colunas que aparecerão na listagem
    list_display = ('folder_repositorio', 'titulo', 'status', 'complexidade', 'data_recebimento')
    # Filtros laterais
    list_filter = ('status', 'complexidade', 'folder_repositorio')
    # Barra de busca
    search_fields = ('titulo', 'workflow_mapping', 'descricao_solucao')