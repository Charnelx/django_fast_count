from django.core.management.base import BaseCommand
from core.models import TestProfileModel


class Command(BaseCommand):
    help = 'Create 1M records in DB'

    def handle(self, *args, **options):
        TestProfileModel.objects.bulk_create(
            [TestProfileModel(first_name=f'Joe #{i}', last_name=f'Doe #{i}') for i in range(1000000)]
        )
        print('Objects created: {}'.format(TestProfileModel.objects.count()))
