from django.contrib import admin
from .models import DemandaETL
from django.forms import Textarea
from django.db import models
from django.urls import reverse
from django.shortcuts import redirect

@admin.register(DemandaETL)
class DemandaETLAdmin(admin.ModelAdmin):
    # Colunas que aparecerão na listagem
    #list_display = ('folder_repositorio', 'titulo', 'status', 'complexidade', 'data_recebimento')
    list_display = ('id_demanda', 'folder_repositorio', 'titulo', 'status', 'complexidade', 'data_recebimento')
    # Filtros laterais
    list_filter = ('status', 'complexidade', 'folder_repositorio')
    # Barra de busca
    search_fields = ('titulo', 'workflow_mapping', 'descricao_solucao')

    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 10, 'cols': 80, 'style': 'font-family: monospace;'})},
    }

    def response_add(self, request, obj, post_url_continue=None):
        """Redireciona para a home após criar um novo registro"""
        # Verifica se o usuário clicou em "_addanother" ou "_continue"
        # Se não, manda para a nossa página 'home'
        if "_addanother" not in request.POST and "_continue" not in request.POST:
            return redirect(reverse('home'))
        return super().response_add(request, obj, post_url_continue)

    def response_change(self, request, obj):
        """Redireciona para a home após editar um registro existente"""
        if "_addanother" not in request.POST and "_continue" not in request.POST:
            return redirect(reverse('home'))
        return super().response_change(request, obj)