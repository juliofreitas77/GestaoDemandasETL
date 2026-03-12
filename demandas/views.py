from django.shortcuts import render
from django.db.models import Q, Count
from datetime import date
from .models import DemandaETL
from django.http import HttpResponse
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side


def home(request):
    # 1. Captura o termo de busca vindo da URL
    busca = request.GET.get('search')

    # 2. Inicia o QuerySet com todas as demandas
    demandas_queryset = DemandaETL.objects.all().order_by('-data_recebimento')

    # 3. Aplica filtros de busca, se houver termo digitado
    if busca:
        demandas_queryset = demandas_queryset.filter(
            Q(titulo__icontains=busca) |
            Q(id_demanda__icontains=busca) |
            Q(workflow_mapping__icontains=busca) |
            Q(folder_repositorio__icontains=busca) |
            Q(origem_destino__icontains=busca)
        )

    # 4. Cálculos para os Cards do Dashboard
    total = demandas_queryset.count()
    em_desenv = demandas_queryset.filter(status='D').count()
    alta = demandas_queryset.filter(complexidade='A').count()

    # 5. Lógica do Semáforo de Prazos (RAG)
    hoje = date.today()
    for d in demandas_queryset:
        if d.data_implementacao:
            dias_restantes = (d.data_implementacao - hoje).days
            if dias_restantes < 0:
                d.risco_cor = "danger"  # Vermelho: Atrasado
                d.risco_texto = f"Atrasada ({abs(dias_restantes)}d)"
            elif dias_restantes <= 3:
                d.risco_cor = "warning"  # Amarelo: Prazo Crítico
                d.risco_texto = "Prazo Crítico"
            else:
                d.risco_cor = "success"  # Verde: No Prazo
                d.risco_texto = "No Prazo"
        else:
            d.risco_cor = "secondary"  # Cinza: Sem data
            d.risco_texto = "Sem data alvo"

    # 6. Dados para o Gráfico de Status
    stats_status = demandas_queryset.values('status').annotate(total=Count('status'))
    labels = []
    data_grafico = []
    status_map = dict(DemandaETL.STATUS_CHOICES)

    for s in stats_status:
        labels.append(status_map.get(s['status']))
        data_grafico.append(s['total'])

    context = {
        'demandas': demandas_queryset,
        'total': total,
        'em_desenv': em_desenv,
        'alta': alta,
        'valor_busca': busca,
        'labels': labels,
        'data_grafico': data_grafico,
    }
    return render(request, 'demandas/home.html', context)


# --- FUNÇÃO DE EXPORTAÇÃO ---
def exportar_excel(request):
    busca = request.GET.get('search')
    demandas_queryset = DemandaETL.objects.all().order_by('-data_recebimento')

    if busca:
        demandas_queryset = demandas_queryset.filter(
            Q(titulo__icontains=busca) | Q(id_demanda__icontains=busca)
        )

    wb = Workbook()
    ws = wb.active
    ws.title = "Relatorio_ETL"

    # Estilos profissionais para o Excel
    header_font = Font(name='Arial', bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="000851", end_color="000851", fill_type="solid")
    center_alignment = Alignment(horizontal="center", vertical="center")
    thin_border = Border(left=Side(style='thin'), right=Side(style='thin'),
                         top=Side(style='thin'), bottom=Side(style='thin'))

    # Cabeçalho da Planilha
    colunas = ['ID Demanda', 'Título', 'Status', 'Complexidade', 'TL Responsável', 'Link Jira', 'Pasta PC']
    ws.append(colunas)

    for cell in ws[1]:
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_alignment
        cell.border = thin_border

    # Inserção dos Dados
    for d in demandas_queryset:
        ws.append([
            d.id_demanda,
            d.titulo,
            d.get_status_display(),
            d.get_complexidade_display(),
            d.lider_tecnico,
            d.link_jira or 'N/A',
            d.folder_repositorio
        ])

    # Ajuste automático de largura das colunas
    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        ws.column_dimensions[column].width = max_length + 2

    ws.auto_filter.ref = ws.dimensions

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=Relatorio_Demandas_ETL.xlsx'
    wb.save(response)

    return response