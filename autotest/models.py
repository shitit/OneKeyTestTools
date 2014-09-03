from django.db import models

class TestQueue(models.Model):
	id = models.IntegerField(primary_key=True)
	exec_info = models.CharField(max_length=1024, blank=True)
	exec_time = models.DateTimeField(blank=True, null=True)
	exec_ornot = models.IntegerField(blank=True, null=True)
	class Meta:
		managed = False
		db_table = 'test_queue'

class PidRecord(models.Model):
	pid = models.IntegerField(primary_key=True)
	run_ornot = models.IntegerField(blank=True, null=True)
	class Meta:
		managed = False
		db_table = 'pid_record'
