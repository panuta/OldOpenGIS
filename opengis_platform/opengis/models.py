from django.contrib.gis.db import models
from django.contrib.auth.models import User

from opengis import sql

class Account(models.Model):
	user = models.ForeignKey(User, primary_key=True)
	account_type = models.IntegerField(default=0)
	
	def __unicode__(self):
		return self.user.username

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
	
	class Info(object):
		code = 'thailand_region'
		table_name = 'ThailandRegion'
		name = 'Thailand Region'
		columns = {
			'id':{
				'name':'ID','physical_name':'id','type':sql.TYPE_SERIAL,'related_table':'',
			},
			'name':{
				'name':'Name','physical_name':'name','type':sql.TYPE_CHARACTER,'related_table':'',
			},
			'name_th':{
				'name':'Name in Thai','physical_name':'name_th','type':sql.TYPE_CHARACTER,'related_table':'',
			},
			'region':{
				'name':'Region','physical_name':'region','type':sql.TYPE_REGION,'related_table':'',
			},
		}
		

class ThailandProvince(models.Model):
	name = models.CharField(max_length=256)
	name_th = models.CharField(max_length=256)
	region = models.MultiPolygonField(null=True)
	region_simple = models.MultiPolygonField(null=True)
	location = models.PointField(null=True)
	in_region = models.ForeignKey(ThailandRegion, null=True)
	objects = models.GeoManager()
	
	def __unicode__(self):
		return self.name
	
	class Info(object):
		code = 'thailand_province'
		table_name = 'ThailandProvince'
		name = 'Thailand Province'
		columns = {
			'id':{
				'name':'ID','physical_name':'id','type':sql.TYPE_SERIAL,'related_table':'',
			},
			'name':{
				'name':'Name','physical_name':'name','type':sql.TYPE_CHARACTER,'related_table':'',
			},
			'name_th':{
				'name':'Name in Thai','physical_name':'name_th','type':sql.TYPE_CHARACTER,'related_table':'',
			},
			'region':{
				'name':'Region','physical_name':'region','type':sql.TYPE_REGION,'related_table':'',
			},
			'region_simple':{
				'name':'Simplified Region','physical_name':'region_simple','type':sql.TYPE_REGION,'related_table':'',
			},
			'location':{
				'name':'Location','physical_name':'location','type':sql.TYPE_LOCATION,'related_table':'',
			},
			'in_region':{
				'name':'In Region','physical_name':'in_region','type':sql.TYPE_BUILT_IN_TABLE,'related_table':'thailand_region',
			},
		}

REGISTERED_BUILT_IN_TABLES = {
	ThailandRegion.Info.code:ThailandRegion,
	ThailandProvince.Info.code:ThailandProvince,
}

######################################################
# USER TABLE
######################################################

class UserTable(models.Model):
	account = models.ForeignKey(Account)
	table_name = models.CharField(max_length=512)
	table_class_name = models.CharField(max_length=512, null=True)
	description = models.CharField(max_length=512, null=True)
	share_level = models.IntegerField(default=0) # 0-Private, 9-Public
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
	starter_table = models.CharField(max_length=128)
	is_distinct = models.BooleanField(default=False)
	result_limit = models.IntegerField(default=0, null=True)
	created = models.DateTimeField(auto_now_add=True)
	modified = models.DateTimeField(auto_now=True)

class UserQueryDisplayColumn(models.Model):
	query = models.ForeignKey(UserQuery)
	column_hierarchy = models.CharField(max_length=512, null=True, blank=True)
	column_name = models.CharField(max_length=512)
	is_aggregate = models.BooleanField(default=False)
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


