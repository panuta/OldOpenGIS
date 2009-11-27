from django.contrib.gis.db import models
from django.contrib.auth.models import User

class Account(models.Model):
	user = models.ForeignKey(User, primary_key=True)
	account_type = models.IntegerField(default=0)
	
	def __unicode__(self):
		return self.user.username

######################################################
# PREDEFINED TABLE
######################################################
class ThailandRegion(models.Model):
	name = models.CharField(max_length=128)
	name_th = models.CharField(max_length=128)
	region = models.MultiPolygonField(null=True)
	objects = models.GeoManager()
	
	def __unicode__(self):
		return self.name

class ThailandProvince(models.Model):
	name = models.CharField(max_length=256)
	name_th = models.CharField(max_length=256)
	region = models.MultiPolygonField(null=True)
	location = models.PointField(null=True)
	in_region = models.ForeignKey(ThailandRegion)
	objects = models.GeoManager()
	
	def __unicode__(self):
		return self.name

######################################################
# USER TABLE
######################################################

class UserTable(models.Model):
	account = models.ForeignKey(Account)
	table_name = models.CharField(max_length=512)
	table_class_name = models.CharField(max_length=512, null=True)
	share_level = models.IntegerField(default=0) # 0-Private, 9-Public
	
	def __unicode__(self):
		return self.table_name

class UserTableColumn(models.Model):
	table = models.ForeignKey(UserTable)
	column_name = models.CharField(max_length=512)
	physical_column_name = models.CharField(max_length=512, null=True)
	data_type = models.IntegerField(default=0)
	related_table = models.CharField(max_length=512, null=True)

######################################################
# USER QUERY
######################################################

class UserQuery(models.Model):
	account = models.ForeignKey(Account)
	query_name = models.CharField(max_length=512)
	starter_table = models.CharField(max_length=128)
	is_distinct = models.BooleanField(default=False)
	result_limit = models.IntegerField(default=0, null=True)

class UserQueryDisplayColumn(models.Model):
	query = models.ForeignKey(UserQuery)
	column_hierarchy = models.CharField(max_length=512, null=True, blank=True)
	column_name = models.CharField(max_length=512)
	is_aggregate = models.BooleanField(default=False)
	is_virtual = models.BooleanField(default=False)
	display_name = models.CharField(max_length=512, null=True, blank=True)

class UserQueryFilter(models.Model):
	query = models.ForeignKey(UserQuery)
	column_hierarchy = models.CharField(max_length=512, null=True, blank=True)
	column_name = models.CharField(max_length=512)
	filter_function = models.CharField(max_length=128)
	filter_value = models.CharField(max_length=512, null=True, blank=True)
	is_variable = models.BooleanField(default=False)

class UserQueryAggregateColumn(models.Model):
	query = models.ForeignKey(UserQuery)
	aggregate_func = models.IntegerField(default=0)
	column_name = models.CharField(max_length=512)

class UserQueryAggregateColumnGroupBy(models.Model):
	query = models.ForeignKey(UserQuery)
	column_name = models.CharField(max_length=512)

class UserQueryOrderByColumn(models.Model):
	query = models.ForeignKey(UserQuery)
	column_hierarchy = models.CharField(max_length=512, null=True, blank=True)
	column_name = models.CharField(max_length=512)
	order_priority = models.IntegerField(default=0) # Lesser number means higher priority
	is_desc = models.BooleanField(default=False)

"""
class UserQueryVirtualColumn(models.Model):
	query = models.ForeignKey(UserQuery)
	column_hierarchy = models.CharField(max_length=512)
	column_name = models.CharField(max_length=512)
"""


