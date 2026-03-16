from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q, Count, Case, When, Value, IntegerField
from datetime import date
from .models import DemandaETL
from django.http import HttpResponse
from django.contrib import messages
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from .forms import DemandaETLForm


def home(request):
    busca = request.GET.get('search')
    hoje = date.today()

    # 1. Definimos o QuerySet inicial
    demandas_queryset = DemandaETL.objects.all()

    # 2. Aplicamos a busca primeiro, se houver
    if busca:
        demandas_queryset = demandas_queryset.filter(
            Q(titulo__icontains=busca) |
            Q(id_demanda__icontains=busca) |
            Q(workflow_mapping__icontains=busca) |
            Q(folder_repositorio__icontains=busca) |
            Q(origem_destino__icontains=busca)
        )

    # 3. Lógica do Semáforo E Atribuição de Peso para Ordenação
    for d in demandas_queryset:
        if d.data_implementacao:
            dias_restantes = (d.data_implementacao - hoje).days
            if dias_restantes < 0:
                d.risco_cor = "danger"
                d.risco_texto = f"Atrasada ({abs(dias_restantes)}d)"
                d.peso_prioridade = 1  # Prioridade Máxima
            elif dias_restantes <= 3:
                d.risco_cor = "warning"
                d.risco_texto = "Prazo Crítico"
                d.peso_prioridade = 2  # Prioridade Alta
            else:
                d.risco_cor = "success"
                d.risco_texto = "No Prazo"
                d.peso_prioridade = 3  # Normal
        else:
            d.risco_cor = "secondary"
            d.risco_texto = "Sem data alvo"
            d.peso_prioridade = 4  # Menor prioridade visual

            # NOVO: Cálculo de Tempo de Execução (Lead Time)
        if d.status == 'P' and d.data_implementacao:
            # Diferença entre Implantação e Recebimento
            delta = d.data_implementacao - d.data_recebimento
            d.tempo_execucao = delta.days
            if d.tempo_execucao < 0: d.tempo_execucao = 0  # Evita erro se datas forem invertidas
        else:
            d.tempo_execucao = None

    # 4. Ordenação manual da lista (Python) baseada no peso de risco
    # Isso garante que as atrasadas fiquem no topo
    demandas_ordenadas = sorted(demandas_queryset, key=lambda x: x.peso_prioridade)

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


def alterar_status(request, id):
    """Altera o status da demanda"""
    demanda = get_object_or_404(DemandaETL, id=id)

    if request.method == 'POST':
        novo_status = request.POST.get('status')

        if novo_status in ['D', 'T', 'P']:
            demanda.status = novo_status
            demanda.save()

            messages.success(
                request,
                f'Status alterado para {demanda.get_status_display()} com sucesso!'
            )
        else:
            messages.error(request, 'Status inválido.')

    return redirect('home')

def excluir_demanda(request, id):
    demanda = get_object_or_404(DemandaETL, id=id)

    if request.method == "POST":
        demanda.delete()
        messages.success(request, "Demanda excluída com sucesso!")

    return redirect('home')

def editar_demanda(request, id):
    demanda = get_object_or_404(DemandaETL, id=id)

    if request.method == 'POST':
        form = DemandaETLForm(request.POST, instance=demanda)
        if form.is_valid():
            form.save()
            messages.success(request, "Demanda atualizada com sucesso!")
            return redirect('home')
    else:
        form = DemandaETLForm(instance=demanda)

    return render(request, 'demandas/editar_demanda.html', {
        'form': form,
        'demanda': demanda
    })


def deletar_demanda(request, id):
    demanda = get_object_or_404(DemandaETL, id=id)

    if request.method == "POST":
        titulo = demanda.titulo
        demanda.delete()
        messages.success(request, f"Demanda '{titulo}' excluída com sucesso!")

    return redirect('home')