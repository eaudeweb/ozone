# Generated by Django 2.1.4 on 2020-02-18 09:05

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0022_uses_reported_decision_data_migration'),
    ]

    operations = [
        migrations.RenameField(
            model_name='processagentusesreported',
            old_name='decision',
            new_name='decision_tmp',
        ),
        migrations.RenameField(
            model_name='processagentusesreported',
            old_name='pa_decision',
            new_name='decision',
        ),
        migrations.RemoveField(
            model_name='processagentusesreported',
            name='decision_tmp',
        ),
        migrations.AlterField(
            model_name='processagentusesreported',
            name='decision',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='pa_uses_reported', to='core.ProcessAgentDecision'),
        ),
    ]
