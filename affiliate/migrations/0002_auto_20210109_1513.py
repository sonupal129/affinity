# Generated by Django 2.2 on 2021-01-09 15:13

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('affiliate', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalproduct',
            name='marketplace',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='affiliate.MarketPlace'),
        ),
        migrations.AddField(
            model_name='product',
            name='marketplace',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='affiliate.MarketPlace'),
        ),
        migrations.AlterField(
            model_name='channel',
            name='marketplace',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='affiliate.MarketPlace'),
        ),
        migrations.AlterField(
            model_name='channel',
            name='networking_company',
            field=models.CharField(choices=[('TW', 'Twitter'), ('IT', 'Instagram'), ('TG', 'Telegram'), ('FB', 'Facebook')], default='FB', max_length=2),
        ),
        migrations.AlterField(
            model_name='historicalchannel',
            name='networking_company',
            field=models.CharField(choices=[('TW', 'Twitter'), ('IT', 'Instagram'), ('TG', 'Telegram'), ('FB', 'Facebook')], default='FB', max_length=2),
        ),
        migrations.AlterField(
            model_name='historicalmarketplace',
            name='country',
            field=models.CharField(choices=[('AU', 'Australia'), ('DE', 'Germany'), ('CA', 'Canada'), ('GB', 'United Kingdom'), ('US', 'United States'), ('HK', 'Hong Kong'), ('FR', 'France'), ('IT', 'Italy'), ('AE', 'United Arab Emirates'), ('IN', 'India')], default=None, max_length=30),
        ),
        migrations.AlterField(
            model_name='marketplace',
            name='country',
            field=models.CharField(choices=[('AU', 'Australia'), ('DE', 'Germany'), ('CA', 'Canada'), ('GB', 'United Kingdom'), ('US', 'United States'), ('HK', 'Hong Kong'), ('FR', 'France'), ('IT', 'Italy'), ('AE', 'United Arab Emirates'), ('IN', 'India')], default=None, max_length=30),
        ),
        migrations.AlterField(
            model_name='product',
            name='category',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='affiliate.Category'),
        ),
    ]
