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
    busca = request.GET.get('search') or request.GET.get('q') # Suporte para ambos os nomes de busca
    hoje = date.today()

    # 1. QuerySet inicial
    demandas_queryset = DemandaETL.objects.all()

    # 2. Aplicar busca se houver
    if busca:
        demandas_queryset = demandas_queryset.filter(
            Q(titulo__icontains=busca) |
            Q(id_demanda__icontains=busca) |
            Q(workflow_mapping__icontains=busca) |
            Q(folder_repositorio__icontains=busca)
        )

    # 3. Lógica ÚNICA de Semáforo, Lead Time e Prioridade
    for d in demandas_queryset:
        # Semáforo e Prioridade
        if d.data_implementacao:
            dias_restantes = (d.data_implementacao - hoje).days
            if dias_restantes < 0:
                d.semaforo_cor = "danger"
                d.semaforo_msg = f"Atrasada ({abs(dias_restantes)}d)"
                d.peso_prioridade = 1
            elif dias_restantes <= 3:
                d.semaforo_cor = "warning"
                d.semaforo_msg = "Urgente"
                d.peso_prioridade = 2
            else:
                d.semaforo_cor = "success"
                d.semaforo_msg = "No Prazo"
                d.peso_prioridade = 3
        else:
            d.semaforo_cor = "secondary"
            d.semaforo_msg = "Sem Data"
            d.peso_prioridade = 4

        # Lead Time (Tempo de Execução)
        if d.status == 'P' and d.data_implementacao:
            delta = d.data_implementacao - d.data_recebimento
            d.tempo_execucao = max(0, delta.days)
        else:
            d.tempo_execucao = None

    # 4. ORDENAÇÃO: Garantir que a lista ordenada seja a enviada
    demandas_final = sorted(demandas_queryset, key=lambda x: x.peso_prioridade)

    # 5. Cálculos dos Cards (sempre baseados no queryset filtrado)
    total = demandas_queryset.count()
    em_desenv = demandas_queryset.filter(status='D').count()
    alta = demandas_queryset.filter(complexidade='A').count()

    # 6. Gráfico de Status
    stats_status = demandas_queryset.values('status').annotate(total=Count('status'))
    labels = []
    data_grafico = []
    status_map = dict(DemandaETL.STATUS_CHOICES)
    for s in stats_status:
        labels.append(status_map.get(s['status']))
        data_grafico.append(s['total'])

    context = {
        'demandas': demandas_final, # ENVIANDO A LISTA COM SEMÁFORO E ORDEM
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