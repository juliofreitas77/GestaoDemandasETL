from django.shortcuts import render
from .models import DemandaETL
from django.db.models import Q  # Importante para buscas complexas (OR)
def home(request):
    # Captura o termo de busca vindo da URL (ex: ?search=Oracle)
    busca = request.GET.get('search')

    # Começa com todas as demandas
    demandas = DemandaETL.objects.all().order_by('-data_recebimento')

    # Se houver algo na busca, filtra por múltiplos campos
    if busca:
        demandas = demandas.filter(
            Q(titulo__icontains=busca) |
            Q(id_demanda__icontains=busca) |
            Q(workflow_mapping__icontains=busca) |
            Q(folder_repositorio__icontains=busca) |
            Q(origem_destino__icontains=busca)
        )

    # Cálculos para o Dashboard (baseados no que foi filtrado ou no total)
    total = demandas.count()
    em_desenv = demandas.filter(status='D').count()
    alta = demandas.filter(complexidade='A').count()

    context = {
        'demandas': demandas,
        'total': total,
        'em_desenv': em_desenv,
        'alta': alta,
        'valor_busca': busca,  # Devolvemos o termo para o campo de busca
    }
    return render(request, 'demandas/home.html', context)


from django.http import HttpResponse
from openpyxl import Workbook
from .models import DemandaETL


def exportar_excel(request):
    # Pega os mesmos filtros da busca
    busca = request.GET.get('search')
    demandas = DemandaETL.objects.all().order_by('-data_recebimento')

    if busca:
        from django.db.models import Q
        demandas = demandas.filter(
            Q(titulo__icontains=busca) | Q(id_demanda__icontains=busca)
        )

    # Cria o arquivo Excel na memória
    wb = Workbook()
    ws = wb.active
    ws.title = "Relatorio de Demandas ETL"

    # Cabeçalho da planilha
    colunas = ['ID Demanda', 'Título', 'Status', 'Complexidade', 'TL Responsável', 'Link Jira', 'Pasta PC']
    ws.append(colunas)

    # Preenche os dados
    for d in demandas:
        ws.append([
            d.id_demanda,
            d.titulo,
            d.get_status_display(),  # Pega o texto amigável do status
            d.get_complexidade_display(),
            d.lider_tecnico,
            d.link_jira or 'N/A',
            d.folder_repositorio
        ])

    # Configura a resposta do navegador para download
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=Relatorio_ETL.xlsx'
    wb.save(response)

    return response