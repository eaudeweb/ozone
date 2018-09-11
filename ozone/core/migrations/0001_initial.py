# Generated by Django 2.0.5 on 2018-09-11 09:21

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import ozone.core.models.party


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Annex',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('annex_id', models.CharField(max_length=16, unique=True)),
                ('name', models.CharField(max_length=64, unique=True)),
                ('description', models.CharField(blank=True, max_length=256)),
            ],
            options={
                'verbose_name_plural': 'annexes',
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='Article7Destruction',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('remarks_party', models.CharField(blank=True, max_length=512)),
                ('remarks_os', models.CharField(blank=True, max_length=512)),
                ('quantity_destroyed', models.FloatField(validators=[django.core.validators.MinValueValidator(0.0)])),
            ],
            options={
                'db_table': 'reporting_article_seven_destruction',
            },
        ),
        migrations.CreateModel(
            name='Article7Emission',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('facility_name', models.CharField(max_length=256)),
                ('quantity_emitted', models.FloatField(validators=[django.core.validators.MinValueValidator(0.0)])),
                ('remarks_party', models.CharField(blank=True, max_length=512)),
                ('remarks_os', models.CharField(blank=True, max_length=512)),
            ],
            options={
                'db_table': 'reporting_article_seven_emissions',
            },
        ),
        migrations.CreateModel(
            name='Article7Export',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('remarks_party', models.CharField(blank=True, max_length=512)),
                ('remarks_os', models.CharField(blank=True, max_length=512)),
                ('quantity_total_new', models.FloatField(null=True, validators=[django.core.validators.MinValueValidator(0.0)])),
                ('quantity_total_recovered', models.FloatField(null=True, validators=[django.core.validators.MinValueValidator(0.0)])),
                ('quantity_feedstock', models.FloatField(null=True, validators=[django.core.validators.MinValueValidator(0.0)])),
                ('quantity_exempted', models.FloatField(null=True, validators=[django.core.validators.MinValueValidator(0.0)])),
                ('type_exempted', models.CharField(blank=True, choices=[('Critical use', 'CRITICAL'), ('Essential use', 'ESSENTIAL'), ('High ambient', 'HIGH_AMBIENT'), ('Process agent', 'PROCESS_AGENT'), ('Laboratory', 'LABORATORY'), ('Other', 'OTHER')], max_length=32)),
            ],
            options={
                'db_table': 'reporting_article_seven_exports',
            },
        ),
        migrations.CreateModel(
            name='Article7Flags',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('flag_incomplete', models.BooleanField(default=True)),
                ('annex', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='incomplete_flags', to='core.Annex')),
            ],
            options={
                'db_table': 'reporting_article_seven_flags',
            },
        ),
        migrations.CreateModel(
            name='Article7Import',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('remarks_party', models.CharField(blank=True, max_length=512)),
                ('remarks_os', models.CharField(blank=True, max_length=512)),
                ('quantity_total_new', models.FloatField(null=True, validators=[django.core.validators.MinValueValidator(0.0)])),
                ('quantity_total_recovered', models.FloatField(null=True, validators=[django.core.validators.MinValueValidator(0.0)])),
                ('quantity_feedstock', models.FloatField(null=True, validators=[django.core.validators.MinValueValidator(0.0)])),
                ('quantity_exempted', models.FloatField(null=True, validators=[django.core.validators.MinValueValidator(0.0)])),
                ('type_exempted', models.CharField(blank=True, choices=[('Critical use', 'CRITICAL'), ('Essential use', 'ESSENTIAL'), ('High ambient', 'HIGH_AMBIENT'), ('Process agent', 'PROCESS_AGENT'), ('Laboratory', 'LABORATORY'), ('Other', 'OTHER')], max_length=32)),
            ],
            options={
                'db_table': 'reporting_article_seven_imports',
            },
        ),
        migrations.CreateModel(
            name='Article7NonPartyTrade',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('remarks_party', models.CharField(blank=True, max_length=512)),
                ('remarks_os', models.CharField(blank=True, max_length=512)),
                ('quantity_import_new', models.FloatField(null=True, validators=[django.core.validators.MinValueValidator(0.0)])),
                ('quantity_import_recovered', models.FloatField(null=True, validators=[django.core.validators.MinValueValidator(0.0)])),
                ('quantity_export_new', models.FloatField(null=True, validators=[django.core.validators.MinValueValidator(0.0)])),
                ('quantity_export_recovered', models.FloatField(null=True, validators=[django.core.validators.MinValueValidator(0.0)])),
            ],
            options={
                'db_table': 'reporting_article_seven_non_party_trade',
            },
        ),
        migrations.CreateModel(
            name='Article7Production',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('remarks_party', models.CharField(blank=True, max_length=512)),
                ('remarks_os', models.CharField(blank=True, max_length=512)),
                ('quantity_total_produced', models.FloatField(null=True, validators=[django.core.validators.MinValueValidator(0.0)])),
                ('quantity_feedstock', models.FloatField(null=True, validators=[django.core.validators.MinValueValidator(0.0)])),
                ('quantity_article_5', models.FloatField(null=True, validators=[django.core.validators.MinValueValidator(0.0)])),
                ('quantity_exempted', models.FloatField(null=True, validators=[django.core.validators.MinValueValidator(0.0)])),
                ('type_exempted', models.CharField(blank=True, choices=[('Critical use', 'CRITICAL'), ('Essential use', 'ESSENTIAL'), ('High ambient', 'HIGH_AMBIENT'), ('Process agent', 'PROCESS_AGENT'), ('Laboratory', 'LABORATORY'), ('Other', 'OTHER')], max_length=32)),
            ],
            options={
                'db_table': 'reporting_article_seven_production',
            },
        ),
        migrations.CreateModel(
            name='Article7Questionnaire',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('remarks_party', models.CharField(blank=True, max_length=512)),
                ('remarks_os', models.CharField(blank=True, max_length=512)),
                ('has_imports', models.BooleanField()),
                ('has_exports', models.BooleanField()),
                ('has_produced', models.BooleanField()),
                ('has_destroyed', models.BooleanField()),
                ('has_nonparty', models.BooleanField()),
                ('has_emissions', models.BooleanField()),
            ],
            options={
                'db_table': 'reporting_article_seven_questionnaire',
            },
        ),
        migrations.CreateModel(
            name='Blend',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('blend_id', models.CharField(max_length=64, unique=True)),
                ('composition', models.CharField(max_length=256)),
                ('other_names', models.CharField(blank=True, max_length=256)),
                ('type', models.CharField(choices=[('Zeotrope', 'ZEOTROPE'), ('Azeotrope', 'AZEOTROPE')], max_length=128)),
                ('odp', models.FloatField(null=True)),
                ('gwp', models.IntegerField(null=True)),
                ('hfc', models.NullBooleanField()),
                ('hcfc', models.NullBooleanField()),
                ('mp_control', models.CharField(blank=True, max_length=256)),
                ('main_usage', models.CharField(blank=True, max_length=256)),
                ('remark', models.CharField(blank=True, max_length=256)),
            ],
        ),
        migrations.CreateModel(
            name='BlendComponent',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('percentage', models.FloatField(validators=[django.core.validators.MinValueValidator(0.0), django.core.validators.MaxValueValidator(1.0)])),
                ('blend', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='components', to='core.Blend')),
            ],
            options={
                'ordering': ('blend', 'substance'),
            },
        ),
        migrations.CreateModel(
            name='Decision',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('decision_id', models.CharField(max_length=16, unique=True)),
                ('name', models.CharField(max_length=256, unique=True)),
                ('remarks', models.CharField(blank=True, max_length=256)),
            ],
        ),
        migrations.CreateModel(
            name='Group',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('group_id', models.CharField(max_length=16, unique=True)),
                ('description', models.CharField(max_length=256)),
                ('phase_out_year_article_5', models.DateField(blank=True, null=True)),
                ('phase_out_year_non_article_5', models.DateField(blank=True, null=True)),
                ('exemption', models.CharField(blank=True, max_length=64)),
                ('annex', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='groups', to='core.Annex')),
            ],
            options={
                'ordering': ('annex', 'group_id'),
            },
        ),
        migrations.CreateModel(
            name='Meeting',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('meeting_id', models.CharField(max_length=16, unique=True)),
                ('treaty_flag', models.BooleanField(default=False)),
                ('start_date', models.DateField(blank=True, null=True)),
                ('end_date', models.DateField(blank=True, null=True)),
                ('location', models.CharField(max_length=128)),
                ('description', models.CharField(max_length=128)),
            ],
            options={
                'ordering': ['pk'],
            },
        ),
        migrations.CreateModel(
            name='Obligation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=256, unique=True)),
                ('is_continuous', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='Party',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=256, unique=True)),
                ('abbr', models.CharField(max_length=32, unique=True)),
                ('signed_vienna_convention', models.DateField(blank=True, null=True)),
                ('ratification_date_vienna_convention', models.DateField(blank=True, null=True)),
                ('ratification_type_vienna_convention', models.CharField(blank=True, choices=[('Accession', 'ACCESSION'), ('Approval', 'APPROVAL'), ('Acceptance', 'ACCEPTANCE'), ('Ratification', 'RATIFICATION'), ('Succession', 'SUCCESSION'), ('Signing', 'SIGNING')], max_length=40)),
                ('signed_montreal_protocol', models.DateField(blank=True, null=True)),
                ('ratification_date_montreal_protocol', models.DateField(blank=True, null=True)),
                ('ratification_type_montreal_protocol', models.CharField(blank=True, choices=[('Accession', 'ACCESSION'), ('Approval', 'APPROVAL'), ('Acceptance', 'ACCEPTANCE'), ('Ratification', 'RATIFICATION'), ('Succession', 'SUCCESSION'), ('Signing', 'SIGNING')], max_length=40)),
                ('ratification_date_london_amendment', models.DateField(blank=True, null=True)),
                ('ratification_type_london_amendment', models.CharField(blank=True, choices=[('Accession', 'ACCESSION'), ('Approval', 'APPROVAL'), ('Acceptance', 'ACCEPTANCE'), ('Ratification', 'RATIFICATION'), ('Succession', 'SUCCESSION'), ('Signing', 'SIGNING')], max_length=40)),
                ('ratification_date_copenhagen_amendment', models.DateField(blank=True, null=True)),
                ('ratification_type_copenhagen_amendment', models.CharField(blank=True, choices=[('Accession', 'ACCESSION'), ('Approval', 'APPROVAL'), ('Acceptance', 'ACCEPTANCE'), ('Ratification', 'RATIFICATION'), ('Succession', 'SUCCESSION'), ('Signing', 'SIGNING')], max_length=40)),
                ('ratification_date_montreal_amendment', models.DateField(blank=True, null=True)),
                ('ratification_type_montreal_amendment', models.CharField(blank=True, choices=[('Accession', 'ACCESSION'), ('Approval', 'APPROVAL'), ('Acceptance', 'ACCEPTANCE'), ('Ratification', 'RATIFICATION'), ('Succession', 'SUCCESSION'), ('Signing', 'SIGNING')], max_length=40)),
                ('ratification_date_beijing_amendment', models.DateField(blank=True, null=True)),
                ('ratification_type_beijing_amendment', models.CharField(blank=True, choices=[('Accession', 'ACCESSION'), ('Approval', 'APPROVAL'), ('Acceptance', 'ACCEPTANCE'), ('Ratification', 'RATIFICATION'), ('Succession', 'SUCCESSION'), ('Signing', 'SIGNING')], max_length=40)),
                ('remarks', models.CharField(blank=True, max_length=512)),
                ('parent_party', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='child_parties', to='core.Party')),
            ],
            options={
                'verbose_name_plural': 'parties',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='PartyHistory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('year', models.IntegerField(validators=[django.core.validators.MinValueValidator, ozone.core.models.party.max_value_current_year])),
                ('population', models.FloatField(validators=[django.core.validators.MinValueValidator(0.0)])),
                ('is_article_5', models.BooleanField()),
                ('is_eu_member', models.BooleanField()),
                ('is_ceit', models.BooleanField()),
                ('remark', models.CharField(blank=True, max_length=256)),
                ('party', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='history', to='core.Party')),
            ],
            options={
                'verbose_name_plural': 'parties history',
                'ordering': ('party', 'year'),
            },
        ),
        migrations.CreateModel(
            name='Region',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('abbr', models.CharField(max_length=32, unique=True)),
                ('name', models.CharField(max_length=256, unique=True)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='ReportingPeriod',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=64, unique=True)),
                ('is_year', models.BooleanField(default=True)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('description', models.CharField(blank=True, max_length=256)),
            ],
        ),
        migrations.CreateModel(
            name='Submission',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('schema_version', models.CharField(max_length=64)),
                ('filled_by_secretariat', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
                ('version', models.PositiveSmallIntegerField(default=1)),
                ('status', models.CharField(max_length=64)),
                ('flag_provisional', models.BooleanField(default=False)),
                ('flag_valid', models.BooleanField(default=False)),
                ('flag_superseded', models.BooleanField(default=False)),
                ('submitted_via', models.CharField(choices=[('Web form', 'WEBFORM'), ('Email', 'EMAIL')], max_length=32)),
                ('remarks_party', models.CharField(blank=True, max_length=512)),
                ('remarks_secretariat', models.CharField(blank=True, max_length=512)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='submissions_created', to=settings.AUTH_USER_MODEL)),
                ('last_edited_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='submissions_last_edited', to=settings.AUTH_USER_MODEL)),
                ('obligation', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='submissions', to='core.Obligation')),
                ('party', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='submissions', to='core.Party')),
                ('reporting_period', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='submissions', to='core.ReportingPeriod')),
            ],
        ),
        migrations.CreateModel(
            name='Subregion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('abbr', models.CharField(max_length=32)),
                ('name', models.CharField(max_length=256)),
                ('region', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='subregions', to='core.Region')),
            ],
            options={
                'ordering': ['region', 'name'],
            },
        ),
        migrations.CreateModel(
            name='Substance',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('substance_id', models.IntegerField(unique=True)),
                ('name', models.CharField(max_length=64, unique=True)),
                ('description', models.CharField(max_length=256)),
                ('odp', models.FloatField()),
                ('min_odp', models.FloatField()),
                ('max_odp', models.FloatField()),
                ('gwp', models.IntegerField(null=True)),
                ('formula', models.CharField(max_length=256)),
                ('number_of_isomers', models.SmallIntegerField(null=True)),
                ('gwp2', models.IntegerField(null=True)),
                ('carbons', models.CharField(blank=True, max_length=128)),
                ('hydrogens', models.CharField(blank=True, max_length=128)),
                ('fluorines', models.CharField(blank=True, max_length=128)),
                ('chlorines', models.CharField(blank=True, max_length=128)),
                ('bromines', models.CharField(blank=True, max_length=128)),
                ('remark', models.CharField(blank=True, max_length=256)),
                ('annex', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='substances', to='core.Annex')),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='substances', to='core.Group')),
            ],
            options={
                'ordering': ('group', 'substance_id'),
            },
        ),
        migrations.CreateModel(
            name='Treaty',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('treaty_id', models.CharField(max_length=16, unique=True)),
                ('name', models.CharField(max_length=64, unique=True)),
                ('date', models.DateField()),
                ('entry_into_force_date', models.DateField()),
                ('base_year', models.IntegerField(null=True)),
                ('description', models.CharField(blank=True, max_length=256)),
                ('meeting_id', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='treaty', to='core.Meeting')),
            ],
            options={
                'verbose_name_plural': 'treaties',
            },
        ),
        migrations.AddField(
            model_name='party',
            name='subregion',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='parties', to='core.Subregion'),
        ),
        migrations.AddField(
            model_name='group',
            name='control_treaty',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='control_substance_groups', to='core.Treaty'),
        ),
        migrations.AddField(
            model_name='group',
            name='report_treaty',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='report_substance_groups', to='core.Treaty'),
        ),
        migrations.AddField(
            model_name='decision',
            name='meeting',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='decisions', to='core.Meeting'),
        ),
        migrations.AddField(
            model_name='blendcomponent',
            name='substance',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='blends', to='core.Substance'),
        ),
        migrations.AddField(
            model_name='article7questionnaire',
            name='blend',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='core.Blend'),
        ),
        migrations.AddField(
            model_name='article7questionnaire',
            name='submission',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='article7questionnaires', to='core.Submission'),
        ),
        migrations.AddField(
            model_name='article7questionnaire',
            name='substance',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='core.Substance'),
        ),
        migrations.AddField(
            model_name='article7production',
            name='blend',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='core.Blend'),
        ),
        migrations.AddField(
            model_name='article7production',
            name='decision',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='core.Decision'),
        ),
        migrations.AddField(
            model_name='article7production',
            name='submission',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='article7productions', to='core.Submission'),
        ),
        migrations.AddField(
            model_name='article7production',
            name='substance',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='core.Substance'),
        ),
        migrations.AddField(
            model_name='article7nonpartytrade',
            name='blend',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='core.Blend'),
        ),
        migrations.AddField(
            model_name='article7nonpartytrade',
            name='submission',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='article7nonpartytrades', to='core.Submission'),
        ),
        migrations.AddField(
            model_name='article7nonpartytrade',
            name='substance',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='core.Substance'),
        ),
        migrations.AddField(
            model_name='article7nonpartytrade',
            name='trade_party',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='core.Party'),
        ),
        migrations.AddField(
            model_name='article7import',
            name='blend',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='core.Blend'),
        ),
        migrations.AddField(
            model_name='article7import',
            name='decision',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='core.Decision'),
        ),
        migrations.AddField(
            model_name='article7import',
            name='submission',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='article7imports', to='core.Submission'),
        ),
        migrations.AddField(
            model_name='article7import',
            name='substance',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='core.Substance'),
        ),
        migrations.AddField(
            model_name='article7flags',
            name='group',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='incomplete_flags', to='core.Group'),
        ),
        migrations.AddField(
            model_name='article7flags',
            name='submission',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='incomplete_flags', to='core.Submission'),
        ),
        migrations.AddField(
            model_name='article7export',
            name='blend',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='core.Blend'),
        ),
        migrations.AddField(
            model_name='article7export',
            name='decision',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='core.Decision'),
        ),
        migrations.AddField(
            model_name='article7export',
            name='submission',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='article7exports', to='core.Submission'),
        ),
        migrations.AddField(
            model_name='article7export',
            name='substance',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='core.Substance'),
        ),
        migrations.AddField(
            model_name='article7emission',
            name='submission',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='article7emissions', to='core.Submission'),
        ),
        migrations.AddField(
            model_name='article7destruction',
            name='blend',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='core.Blend'),
        ),
        migrations.AddField(
            model_name='article7destruction',
            name='submission',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='article7destructions', to='core.Submission'),
        ),
        migrations.AddField(
            model_name='article7destruction',
            name='substance',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='core.Substance'),
        ),
        migrations.AlterUniqueTogether(
            name='subregion',
            unique_together={('abbr', 'region')},
        ),
        migrations.AlterUniqueTogether(
            name='submission',
            unique_together={('party', 'reporting_period', 'obligation', 'version')},
        ),
        migrations.AlterUniqueTogether(
            name='partyhistory',
            unique_together={('party', 'year')},
        ),
    ]
