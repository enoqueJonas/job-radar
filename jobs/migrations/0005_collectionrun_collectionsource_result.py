from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("jobs", "0004_jobsource_last_validated_at_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="CollectionRun",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("status", models.CharField(choices=[("running", "Running"), ("completed", "Completed"), ("completed_with_errors", "Completed with errors"), ("failed", "Failed")], default="running", max_length=30)),
                ("requested_sources", models.JSONField(blank=True, default=list)),
                ("fail_fast", models.BooleanField(default=False)),
                ("source_count", models.PositiveIntegerField(default=0)),
                ("successful_sources", models.PositiveIntegerField(default=0)),
                ("failed_sources", models.PositiveIntegerField(default=0)),
                ("collected_count", models.PositiveIntegerField(default=0)),
                ("persisted_count", models.PositiveIntegerField(default=0)),
                ("started_at", models.DateTimeField(auto_now_add=True)),
                ("finished_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={"ordering": ["-started_at"]},
        ),
        migrations.CreateModel(
            name="CollectionSourceResult",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("status", models.CharField(choices=[("success", "Success"), ("failed", "Failed")], max_length=20)),
                ("collected_count", models.PositiveIntegerField(default=0)),
                ("persisted_count", models.PositiveIntegerField(default=0)),
                ("error_type", models.CharField(blank=True, max_length=255)),
                ("error_message", models.TextField(blank=True)),
                ("started_at", models.DateTimeField(auto_now_add=True)),
                ("finished_at", models.DateTimeField(blank=True, null=True)),
                ("run", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="source_results", to="jobs.collectionrun")),
                ("source", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="collection_results", to="jobs.jobsource")),
            ],
            options={"ordering": ["source__name"]},
        ),
        migrations.AddConstraint(
            model_name="collectionsourceresult",
            constraint=models.UniqueConstraint(fields=("run", "source"), name="unique_collection_result_per_source"),
        ),
    ]
