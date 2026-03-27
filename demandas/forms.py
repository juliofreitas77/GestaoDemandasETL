from django import forms
from .models import DemandaETL

class DemandaETLForm(forms.ModelForm):
    class Meta:
        model = DemandaETL
        fields = [
            'titulo',
            'id_demanda',
            'workflow_mapping',
            'folder_repositorio',
            'lider_tecnico',
            'data_implementacao', # Nome correto conforme seu models
            'status',
            'descricao_solucao',
            'script_sql_shell',
            'link_jira'
        ]

        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: TESTE_FRONT_END'}),
            'id_demanda': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 12345678910'}),
            'workflow_mapping': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome do workflow'}),
            'folder_repositorio': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Pasta no PowerCenter'}),
            'lider_tecnico': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome do TL'}),
              
            'data_implementacao': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            
            'status': forms.Select(attrs={'class': 'form-select'}),
            'descricao_solucao': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Descreva a solução...'}),
            'script_sql_shell': forms.Textarea(attrs={'class': 'form-control', 'rows': 6, 'placeholder': 'Cole scripts SQL/Shell...'}),
            'link_jira': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://jira.empresa.com/...'}),
        }

        labels = {
            'titulo': 'Título do Mapping',
            'id_demanda': 'ID da Demanda',
            'workflow_mapping': 'Workflow/Mapping',
            'folder_repositorio': 'Pasta do Repositório',
            'lider_tecnico': 'Líder Técnico',
            'data_implementacao': 'Data Limite de Implantação', # Ajustado o label também
            'status': 'Status Atual',
            'descricao_solucao': 'Descrição da Solução',
            'script_sql_shell': 'Scripts SQL/Shell',
            'link_jira': 'Link do Jira',
        }