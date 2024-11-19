from django.db import models


class Test(models.Model):
    age = models.FloatField(blank=True, null=True)
    name = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'test'


class UserAccount(models.Model):
    id_role = models.ForeignKey('UserRole', models.DO_NOTHING, db_column='id_role')
    login = models.CharField(max_length=100)
    password = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'user_account'


class UserRole(models.Model):
    name = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'user_role'
