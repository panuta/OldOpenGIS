from opengis import constants

# Callback after user registered
from registration.signals import user_activated
from opengis.views import registered_user_callback

user_activated.connect(registered_user_callback)

# Create django model class from variable
from django.contrib.auth.models import User
from django.contrib.gis.db import models
from opengis.models import *
from opengis import sql

from django.utils.encoding import *

def _create_model(user_table, user_table_columns):
	class Meta:
		pass

	# setattr(Meta, 'app_label', APPLICATION_NAME)
	
	attrs = {'__module__': constants.APPLICATION_NAME + ".models", 'Meta': Meta}
	
	for column in user_table_columns:
		
		column.physical_column_name = smart_str(column.physical_column_name)
		
		if column.data_type == sql.TYPE_CHARACTER:
			attrs[column.physical_column_name] = models.CharField(max_length=sql.DEFAULT_CHARACTER_LENGTH, null=True)
			
		elif column.data_type == sql.TYPE_NUMBER:
			attrs[column.physical_column_name] = models.FloatField(null=True)
			
		elif column.data_type == sql.TYPE_DATETIME:
			attrs[column.physical_column_name] = models.DateTimeField(null=True)
		
		elif column.data_type == sql.TYPE_DATE:
			attrs[column.physical_column_name] = models.DateField(null=True)
		
		elif column.data_type == sql.TYPE_TIME:
			attrs[column.physical_column_name] = models.TimeField(null=True)
		
		elif column.data_type == sql.TYPE_REGION:
			attrs[column.physical_column_name] = models.MultiPolygonField(null=True)
		
		elif column.data_type == sql.TYPE_LOCATION:
			attrs[column.physical_column_name] = models.PointField(null=True)
		
		elif column.data_type == sql.TYPE_USER_TABLE:
			my_table = UserTable.objects.get(pk=column.related_table)
			my_table_columns = UserTableColumn.objects.filter(table=user_table)
			
			attrs[column.physical_column_name] = models.ForeignKey(_create_model(my_table, my_table_columns), null=True)
		
		elif column.data_type == sql.TYPE_BUILT_IN_TABLE:
			attrs[column.physical_column_name] = models.ForeignKey(REGISTERED_BUILT_IN_TABLES[column.related_table], null=True)
	
	attrs['objects'] = models.GeoManager()
	
	model_class = type(str(user_table.table_class_name), (models.Model,), attrs) # user_table.table_class_name return as 'unicode', convert to string

	return model_class

# Caching manager for user table columns
class UserTableColumnManager(object):

	def __init__(self, starter_table):
		self.starter_table = starter_table
		
		starter_column_mapping = dict()
		
		if starter_table in REGISTERED_BUILT_IN_TABLES:
			self.is_start_with_built_in = True
			self.columns_cache = None
			
		else:
			# TODO: Check if starter table is exist
			
			for table_column in UserTableColumn.objects.filter(table=UserTable(pk=starter_table)):
				starter_column_mapping[table_column.physical_column_name] = table_column
			
			self.is_start_with_built_in = False
			self.columns_cache = {starter_table:starter_column_mapping}
	
	
	def get_column_info(self, column_hierarchy, column_name):
	
		if self.is_start_with_built_in:
			column_mapping = REGISTERED_BUILT_IN_TABLES[self.starter_table].Info.columns
			
			for hierarchy in column_hierarchy.split(".") if column_hierarchy else list():
				column_info = column_mapping[hierarchy]
				column_mapping = REGISTERED_BUILT_IN_TABLES[column_info['related_table']].Info.columns
		
			return {
				'name':column_mapping[column_name]['name'],
				'type':column_mapping[column_name]['type'],
				'physical_name':column_mapping[column_name]['physical_name'],
				'related_table':column_mapping[column_name]['related_table']
				}
		
		else:
			column_mapping = self.columns_cache[self.starter_table]
			
			BUILT_IN_TABLE_CHAIN_STARTED = False
			
			for hierarchy in column_hierarchy.split(".") if column_hierarchy else list():
				if not BUILT_IN_TABLE_CHAIN_STARTED:
					column_info = column_mapping[hierarchy]
				
					if sql.TYPE_USER_TABLE == column_info.data_type:
						if column_info.related_table not in self.columns_cache: # Not in cache
							column_mapping = dict()
							for table_column in UserTableColumn.objects.filter(table=UserTable(pk=column_info.related_table)):
								column_mapping[table_column.physical_column_name] = table_column
							self.columns_cache[column_info.related_table] = column_mapping
						
						else:
							column_mapping = self.columns_cache[column_info.related_table]
				
					elif sql.TYPE_BUILT_IN_TABLE == column_info.data_type:
						BUILT_IN_TABLE_CHAIN_STARTED = True
						column_mapping = REGISTERED_BUILT_IN_TABLES[column_info.related_table].Info.columns
				
				else:
					column_info = column_mapping[hierarchy]
					column_mapping = REGISTERED_BUILT_IN_TABLES[column_info['related']].Info.columns
			
			if BUILT_IN_TABLE_CHAIN_STARTED:
				# Column data from built in table columns dict
				return {
					'name':column_mapping[column_name]['name'], 
					'type':column_mapping[column_name]['type'], 
					'physical_name':column_mapping[column_name]['physical_name'], 
					'related_table':column_mapping[column_name]['related_table']
					}
			
			else:
				# Column data from UserTableColumn model
				return {
					'name':column_mapping[column_name].column_name, 
					'type':column_mapping[column_name].data_type, 
					'physical_name':column_mapping[column_name].physical_column_name, 
					'related_table':column_mapping[column_name].related_table,
					}


