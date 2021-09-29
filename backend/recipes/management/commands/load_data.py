import csv
from django.core.management.base import BaseCommand, CommandError
from django.db.utils import IntegrityError
from pathlib import Path

from recipes.models import Ingredient


class Command(BaseCommand):

    def handle(self, *args, **options):
        DATA = Path.cwd().parent.joinpath('data/ingredients.csv')
        with DATA.open(encoding='utf-8') as file:
            file_reader = csv.reader(file)
            for row in file_reader:
                name, unit = row
                try:
                    Ingredient.objects.get_or_create(name=name,
                                                     measurement_unit=unit)
                except IntegrityError:
                    raise CommandError(
                        f'повторяющийся ингредиент в списке {name}, {unit}')
