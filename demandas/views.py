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