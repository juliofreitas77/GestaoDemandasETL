from django.core.management.base import BaseCommand
from django.utils import timezone
from demandas.models import DemandaETL


class Command(BaseCommand):
    help = "Popula o banco com demandas de teste"

    def handle(self, *args, **kwargs):

        for i in range(1, 21):  # Cria 20 demandas
            DemandaETL.objects.create(
                titulo=f"TESTE_DEMANDA_{i}",
                id_demanda=f"1000000000{i}",
                workflow_mapping="Workflow Teste",
                folder_repositorio="Pasta Teste",
                lider_tecnico="Julio Freitas",
                data_recebimento=timezone.now().date(),
                data_implementacao=timezone.now().date(),
                status="D",
                descricao_solucao=f"Descrição automática da demanda {i}",
                script_sql_shell="SELECT * FROM tabela_teste;",
                link_jira=f"https://jira.teste.com/{i}"
            )

        self.stdout.write(self.style.SUCCESS("✅ 20 demandas criadas com sucesso!"))

