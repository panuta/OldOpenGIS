from django.conf import settings
from django.contrib.gis.db import models
from django.contrib.auth.models import User

from opengis import sql

class Account(models.Model):
	user = models.ForeignKey(User, primary_key=True)
	account_type = models.IntegerField(default=0)
	
	def __unicode__(self):
		return self.user.username

######################################################
# USER TABLE
######################################################

class UserTable(models.Model):
	account = models.ForeignKey(Account)
	table_name = models.CharField(max_length=512)
	table_class_name = models.CharField(max_length=512, null=True)
	description = models.CharField(max_length=512, null=True)
	share_level = models.IntegerField(default=1) # 1-Private, 9-Public
	display_column = models.CharField(max_length=512) # Store as physical column name
	is_builtin = models.BooleanField(default=False)
	created = models.DateTimeField(auto_now_add=True)
	modified = models.DateTimeField(auto_now=True)

	def __unicode__(self):
		return self.table_name

class UserTableColumn(models.Model):
	table = models.ForeignKey(UserTable)
	column_name = models.CharField(max_length=512)
	physical_column_name = models.CharField(max_length=512, null=True)
	data_type = models.IntegerField(default=0)
	related_table = models.CharField(max_length=512, null=True)
	created = models.DateTimeField(auto_now_add=True)
	modified = models.DateTimeField(auto_now=True)

class UserTableTag(models.Model):
	table = models.ForeignKey(UserTable)
	tag_name = models.CharField(max_length=512)

######################################################
# USER QUERY
######################################################

class UserQuery(models.Model):
	account = models.ForeignKey(Account)
	query_name = models.CharField(max_length=512)
	description = models.CharField(max_length=512, null=True)
	starter_table = models.ForeignKey(UserTable)
	is_distinct = models.BooleanField(default=False)
	result_limit = models.IntegerField(default=0, null=True)
	created = models.DateTimeField(auto_now_add=True)
	modified = models.DateTimeField(auto_now=True)

class UserQueryDisplayColumn(models.Model):
	query = models.ForeignKey(UserQuery)
	column_hierarchy = models.CharField(max_length=512, null=True, blank=True)
	column = models.ForeignKey(UserTableColumn)
	is_aggregate = models.BooleanField(default=False)
	display_name = models.CharField(max_length=512, null=True, blank=True)

class UserQueryFilter(models.Model):
	query = models.ForeignKey(UserQuery)
	column_hierarchy = models.CharField(max_length=512, null=True, blank=True)
	column = models.ForeignKey(UserTableColumn)
	filter_function = models.CharField(max_length=128)
	filter_value = models.CharField(max_length=512, null=True, blank=True)
	is_variable = models.BooleanField(default=False)

class UserQueryAggregateColumn(models.Model):
	query = models.ForeignKey(UserQuery)
	aggregate_func = models.IntegerField(default=0)
	column = models.ForeignKey(UserTableColumn)

class UserQueryGroupByColumn(models.Model):
	query = models.ForeignKey(UserQuery)
	column = models.ForeignKey(UserTableColumn)

class UserQueryOrderByColumn(models.Model):
	query = models.ForeignKey(UserQuery)
	column_hierarchy = models.CharField(max_length=512, null=True, blank=True)
	column = models.ForeignKey(UserTableColumn)
	order_priority = models.IntegerField(default=0) # Lesser number means higher priority
	is_desc = models.BooleanField(default=False)

"""
class UserQueryVirtualColumn(models.Model):
	query = models.ForeignKey(UserQuery)
	column_hierarchy = models.CharField(max_length=512)
	column_name = models.CharField(max_length=512)
"""

######################################################
# BUILT-IN TABLE
######################################################

class ThailandRegion(models.Model):
	name = models.CharField(max_length=128)
	name_th = models.CharField(max_length=128)
	region = models.MultiPolygonField(null=True)
	objects = models.GeoManager()
	
	def __unicode__(self):
		return self.name
	
	CLASS_NAME = 'thailandregion'
	
	def initialize(self, account, installed_models):
		user_table = UserTable.objects.create(
			account = account,
			table_name = "Thailand Region",
			table_class_name = self.CLASS_NAME,
			share_level = 9,
			display_column = "name",
			is_builtin = True,
		)
		
		UserTableColumn.objects.create(table=user_table, column_name="ID", physical_column_name="id", data_type=sql.TYPE_NUMBER,)
		UserTableColumn.objects.create(table=user_table, column_name="Name", physical_column_name="name", data_type=sql.TYPE_CHARACTER,)
		UserTableColumn.objects.create(table=user_table, column_name="Thai Name", physical_column_name="name_th", data_type=sql.TYPE_CHARACTER,)
		UserTableColumn.objects.create(table=user_table, column_name="Region", physical_column_name="region", data_type=sql.TYPE_REGION,)
		
		return user_table.id

class ThailandProvince(models.Model):
	geocode = models.IntegerField()
	name = models.CharField(max_length=256)
	name_th = models.CharField(max_length=256)
	region = models.MultiPolygonField(null=True)
	region_simple = models.MultiPolygonField(null=True)
	location = models.PointField(null=True)
	in_region = models.ForeignKey(ThailandRegion, null=True)
	objects = models.GeoManager()

	def __unicode__(self):
		return self.name
	
	CLASS_NAME = 'thailandprovince'
	
	def initialize(self, account, installed_models):
		user_table = UserTable.objects.create(
			account = account,
			table_name = "Thailand Province",
			table_class_name = self.CLASS_NAME,
			share_level = 9,
			display_column = "name",
			is_builtin = True,
		)
		
		UserTableColumn.objects.create(table=user_table, column_name="ID", physical_column_name="id", data_type=sql.TYPE_NUMBER,)
		UserTableColumn.objects.create(table=user_table, column_name="GeoCode", physical_column_name="geocode", data_type=sql.TYPE_NUMBER,)
		UserTableColumn.objects.create(table=user_table, column_name="Name", physical_column_name="name", data_type=sql.TYPE_CHARACTER,)
		UserTableColumn.objects.create(table=user_table, column_name="Thai Name", physical_column_name="name_th", data_type=sql.TYPE_CHARACTER,)
		UserTableColumn.objects.create(table=user_table, column_name="In Region", physical_column_name="in_region", data_type=sql.TYPE_NUMBER,related_table=installed_models[ThailandRegion.CLASS_NAME])
		UserTableColumn.objects.create(table=user_table, column_name="Region", physical_column_name="region", data_type=sql.TYPE_REGION,)
		UserTableColumn.objects.create(table=user_table, column_name="Simple Region", physical_column_name="region_simple", data_type=sql.TYPE_REGION,)
		UserTableColumn.objects.create(table=user_table, column_name="Location", physical_column_name="location", data_type=sql.TYPE_LOCATION,)
		
		return user_table.id

REGISTERED_BUILT_IN_TABLES = [
	ThailandRegion,
	ThailandProvince,
]


