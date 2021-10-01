# Generated by Django 3.1 on 2021-09-30 13:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0003_auto_20210930_1351'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ingredient',
            name='measurement_unit',
            field=models.CharField(choices=[('г', 'г'), ('кг', 'кг'), ('шт.', 'шт.'), ('ч. л.', 'ч. л.'), ('ст. л.', 'ст. л.'), ('мл', 'мл'), ('л', 'л'), ('стакан', 'стакан'), ('долька', 'долька'), ('веточка', 'веточка'), ('горсть', 'горсть'), ('пучок', 'пучок'), ('щепотка', 'щепотка'), ('по вкусу', 'по вкусу'), ('кусок', 'кусок'), ('банка', 'банка'), ('упаковка', 'упаковка'), ('батон', 'батон'), ('капля', 'капля'), ('бутылка', 'бутылка'), ('зубчик', 'зубчик')], max_length=200, verbose_name='Единица Измерения'),
        ),
    ]
