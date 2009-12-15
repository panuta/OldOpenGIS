import datetime, time
import csv

from django.conf import settings
from django.contrib.auth.models import User
from django.db import connection, transaction
from django.utils import simplejson

import opengis
from opengis import api, sql, query, utilities
from opengis.models import *
from opengis.forms import *
from opengis.shortcuts import *

#######################################################################################
# USER TABLE
#######################################################################################

def api_table_create(request):
	if request.method == 'POST':
		account = Account.objects.get(user=request.user)
		
		table_name = request.POST.get('table_name')
		description = request.POST.get('table_description')
		tags = request.POST.get('table_tags')
		share_level = request.POST.get('share_level')
		display_column = request.POST.get('display_column')
		
		error_list = list()
		
		if not table_name: error_list.append('required-table_name')
		if not share_level: error_list.append('required-share_level')
		if not display_column: error_list.append('required-display_column')
		
		if UserTable.objects.filter(account=account, table_name=table_name).count():
			error_list.append('duplicated-table_name')
		
		raw_columns = request.POST.getlist('column')
		if not raw_columns: error_list.append('required-column')
		
		columns = list()
		column_count = 1
		for column in raw_columns:
			try:
				column = _decode_table_column(column, account)
				
			except api.InvalidColumnName as e:
				error_list.append('invalid_name-column-' + e.column_name)
			except api.InvalidColumnDataType as e:
				error_list.append('invalid_type-column-' + e.column_name)
			except api.MissingColumnName as e:
				error_list.append('missing_name-column')
			except api.MissingColumnArgument as e:
				error_list.append('missing_argument-column-' + e.column_name)
			except:
				error_list.append('unknown_error-column')
				
			else:
				column['physical_name'] = 'column_' + str(column_count)
				column_count = column_count + 1
				columns.append(column)
		
		# TODO: Detect duplicate column name
		
		if error_list:
			return api.APIResponse(api.API_RESPONSE_ERROR_LIST, response_meta={'errorlist':error_list})
			
		else:
			# Change display column to physical value
			for column in columns:
				if column['name'] == display_column: display_column = column['physical_name']
			
			# Create table metadata
			user_table = UserTable.objects.create(account=account, table_name=table_name, description=description, share_level=share_level, display_column=display_column)
			user_table.table_class_name = settings.USER_TABLE_PREFIX + "_" + str(user_table.account.user.id) + "_" + str(user_table.id)
			user_table.save()

			user_table_columns = list()
			for column in columns:
				user_table_columns.append(UserTableColumn.objects.create(
					table=user_table,
					column_name=column['name'], 
					physical_column_name=column['physical_name'], 
					data_type=column['type'], 
					related_table=column.get('related', None)
				))
			
			if tags:
				for tag in tags.split(','):
					UserTableTag.objects.create(table=user_table,tag_name=tag)
			
			# Create table at database server
			sql.sql_create_table(user_table)
			
			return api.APIResponse(api.API_RESPONSE_SUCCESS, result={'id':user_table.id})
		
	else:
		return api.APIResponse(api.API_RESPONSE_POSTONLY)

def api_table_edit(request):
	if request.method == 'POST':
		account = Account.objects.get(user=request.user)
		
		table_id = request.POST.get('table_id')
		if not table_id: return api.APIResponse(api.API_RESPONSE_ERROR, response_meta={'error':'required_table_id'})
		
		table_name = request.POST.get('table_name', None)
		description = request.POST.get('table_description', None)
		tags = request.POST.get('table_tags', None)
		share_level = request.POST.get('share_level', None)
		display_column = request.POST.get('display_column', None)
		
		if UserTable.objects.filter(account=account, table_name=table_name).exclude(pk=table_id).count():
			return api.APIResponse(api.API_RESPONSE_ERROR, response_meta={'error':'duplicated_table_name'})
		
		# Update table metadata
		user_table = UserTable.objects.get(pk=table_id)
		if table_name != None: user_table.table_name = table_name
		if description != None: user_table.description = description
		if share_level != None: user_table.share_level = share_level
		if display_column != None: user_table.display_column = display_column
		
		user_table.save()
		
		# Update table tags
		if tags != None:
			UserTableTag.objects.filter(table=user_table).delete()
		
			if tags:
				for tag in tags.split(','):
					UserTableTag.objects.create(table=user_table,tag_name=tag)
		
		return api.APIResponse(api.API_RESPONSE_SUCCESS, result={'id':user_table.id,'table_name':user_table.table_name})
		
	else:
		return api.APIResponse(api.API_RESPONSE_POSTONLY)

def api_table_add_columns(request):
	if request.method == 'POST':
		table_id = request.POST.get('table_id')
		raw_add_columns = request.POST.getlist('column')
		
		# Prepare add columns
		add_columns = list()
		for column in raw_add_columns:
			try:
				column = _decode_table_column(column, account)
			except api.TableColumnException as e:
				return api.APIResponse(api.API_RESPONSE_ERROR, response_meta={'error':e.error_code})
			else:
				add_columns.append(column)
		
		user_table = UserTable.objects.get(pk=table_id)
		user_table_columns = UserTableColumn.objects.filter(table=user_table)
		
		# TODO: Check permission
		
		# Generate add columns physical name
		max_column_number = 1
		for column in user_table_columns:
			column_number = int(column.physical_column_name.split("_")[1])
			if max_column_number < column_number: max_column_number = column_number
		
		for column in add_columns:
			max_column_number = max_column_number + 1
			column['physical_name'] = 'column_' + str(max_column_number)
		
		get_result = request.POST.get('result') == 'true'
		result = list()
		
		# Add columns
		for column in add_columns:
			added_column = UserTableColumn.objects.create(
				table=user_table,
				column_name=column.get('name'), 
				physical_column_name=column.get('physical_name'), 
				data_type=column.get('type'), 
				related_table=column.get('related', None)
			)

			sql.add_new_column(database_table_name, column.get('physical_name'), column.get('type'))
			
			if get_result: result.append({'id':added_column.id,'name':added_column.column_name,'type':added_column.data_type,'related':added_column.related_table})
	
		if get_result:
			return api.APIResponse(api.API_RESPONSE_SUCCESS, result=simplejson.dumps(result))
		else:
			return api.APIResponse(api.API_RESPONSE_SUCCESS)
		
	else:
		return api.APIResponse(api.API_RESPONSE_POSTONLY)

def api_table_rename_columns(request):
	"""
	Changes user table's column name
	"""
	if request.method == 'POST':
		raw_rename_columns = request.POST.getlist("column")
		
		# Prepare rename columns
		rename_columns = list()
		for column in raw_rename_columns:
			try:
				(column_id, separator, column_name) = column.partition(':')
			except:
				return api.APIResponse(api.API_RESPONSE_ERROR, response_meta={'error':'invalid-format'})
			else:
				rename_columns.append({'id':column_id,'name':column_name})
		
		# Rename columns
		for column in rename_columns:
			user_table_column = UserTableColumn.objects.get(pk=column['id'])
			
			# TODO: Check permission
			
			user_table_column.column_name = column['name']
			user_table_column.save()
		
		return api.APIResponse(api.API_RESPONSE_SUCCESS)
		
	else:
		return api.APIResponse(api.API_RESPONSE_POSTONLY)

def api_table_delete_columns(request):
	if request.method == 'POST':
		raw_delete_columns = request.POST.getlist("column")
		
		# Prepare delete columns
		delete_columns = list()
		for column in raw_delete_columns:
			delete_columns.append(column)
		
		# Delete columns
		for column in delete_columns:
			user_table_column = UserTableColumn.objects.get(pk=column)
			user_table = user_table_column.table
			
			# TODO: Check permission
			
			if user_table_column.physical_column_name == user_table.display_column: continue # Will not perform delete action on display column
			
			cursor = connection.cursor()
			
			database_table_name = settings.MAIN_APPLICATION_NAME + "_" + user_table.table_class_name
			
			if user_table_column.data_type in (sql.TYPE_REGION, sql.TYPE_LOCATION):
				cursor.execute("SELECT DropGeometryColumn ('%s','%s')" % (database_table_name,user_table_column.physical_column_name))
			else:
				cursor.execute("ALTER TABLE %s DROP COLUMN %s" % (database_table_name,user_table_column.physical_column_name))
			
			transaction.set_dirty()
			
			user_table_column.delete()
			
		return api.APIResponse(api.API_RESPONSE_SUCCESS)
		
	else:
		return api.APIResponse(api.API_RESPONSE_POSTONLY)

def api_table_empty(request):
	if request.method == 'POST':
		user_table = UserTable.objects.get(pk=request.POST.get('table_id'))
		user_table_columns = UserTableColumn.objects.filter(table=user_table)
		
		table_model = opengis.create_model(user_table)
		table_model.objects.all().delete()
		
		return api.APIResponse(api.API_RESPONSE_SUCCESS)
		
	else:
		return api.APIResponse(api.API_RESPONSE_POSTONLY)

def api_table_delete(request):
	if request.method == 'POST':
		user_table = UserTable.objects.get(pk=request.POST.get('table_id'))
		
		# TODO: Check permission
		
		cursor = connection.cursor()
		
		# Drop user table
		database_table_name = settings.MAIN_APPLICATION_NAME + "_" + user_table.table_class_name
		cursor.execute("SELECT DropGeometryTable ('%s')" % database_table_name)
		transaction.set_dirty()
		
		UserTableColumn.objects.filter(table=user_table).delete()
		UserTableTag.objects.filter(table=user_table).delete()
		user_table.delete()
		
		return api.APIResponse(api.API_RESPONSE_SUCCESS)
		
	else:
		return api.APIResponse(api.API_RESPONSE_POSTONLY)

def _decode_table_column(raw_column, current_account):
	column = simplejson.loads(raw_column)
	
	if 'name' not in column.keys(): raise api.MissingColumnName()
	if 'type' not in column.keys(): raise api.MissingColumnArgument(column['name'])
	
	type_string = column['type']
	
	if type_string == "table":
		related_table = UserTable.objects.get(pk=column['related'])

		if related_table.account != current_account and related_table.share_level != 9:
			pass
			# RAISE NO ACCESS to private table
	
	if type_string == "char": column_type = sql.TYPE_CHARACTER
	elif type_string == "number": column_type = sql.TYPE_NUMBER
	elif type_string == "datetime": column_type = sql.TYPE_DATETIME
	elif type_string == "date": column_type = sql.TYPE_DATE
	elif type_string == "time": column_type = sql.TYPE_TIME
	elif type_string == "region": column_type = sql.TYPE_REGION
	elif type_string == "location": column_type = sql.TYPE_LOCATION
	elif type_string == "table": column_type = sql.TYPE_USER_TABLE
	elif type_string == "builtin": column_type = sql.TYPE_USER_TABLE
	else: column_type = 0

	if column_type != 0:
		column['type'] = column_type
	
	return column

def api_table_info(request):
	if request.method == 'GET':
		table_ids = request.GET.getlist('table_id')
		result = list()
		
		for table_id in table_ids:
			user_table = UserTable.objects.get(pk=table_id)
			columns = [{'id':column.id,'name':column.column_name} for column in UserTableColumn.objects.filter(table=user_table)]
			result.append({'id':user_table.id, 'name':user_table.table_name,'columns':columns})
		
		if result:
			return api.APIResponse(api.API_RESPONSE_SUCCESS, result=result)
		else:
			return api.APIResponse(api.API_RESPONSE_RESOURCE_NOT_FOUND)
		
	else:
		return api.APIResponse(api.API_RESPONSE_GETONLY)

def api_table_data(request):
	pass

def api_table_list(request):
	if request.method == 'GET':
		username = request.GET.get('username')
		
		if username:
			account = Account.objects.get(user=User.objects.get(username=username))
			user_tables = UserTable.objects.filter(account=account, share_level=9)
		else:
			account = Account.objects.get(user=request.user)
			user_tables = UserTable.objects.filter(account=account)
		
		result = [{'id':table.id,'name':table.table_name,'description':table.description if table.description else ''} for table in user_tables]

		return api.APIResponse(api.API_RESPONSE_SUCCESS, result=result)
	
	else:
		return api.APIResponse(api.API_RESPONSE_GETONLY)

def api_table_import(request):
	if request.method == 'POST':
		import_table(request)
		return api.APIResponse(api.API_RESPONSE_SUCCESS, result=result)
	
	else:
		return api.APIResponse(api.API_RESPONSE_POSTONLY)

def import_table(user_table, account, request):
	temp_csv_file = settings.TEMP_CSV_PATH + '/temp_' + str(account.user.id) + "_" + str(long(round(time.time()))) + '.csv'
	
	destination = open(temp_csv_file, 'wb')
	for chunk in request.FILES['file'].chunks(): destination.write(chunk)
	destination.close()
	
	destination = open(temp_csv_file, 'rb')
	csv_reader = csv.reader(destination)
	
	table_columns = UserTableColumn.objects.filter(table=user_table)
	
	target_model = opengis.create_model(user_table)
	target_model.objects.all().delete()
	
	column_mapping = list()
	
	for row in csv_reader:
		if not column_mapping: # csv.reader object is unsubscriptable
			
			# Map logical column name used in CSV to physical database column name
			for index, column_name in enumerate(row):
				(parent_column, separator, child_column) = column_name.partition("---")
				column_info = dict()
				
				table_column = utilities.list_find(lambda table_column: table_column.column_name == parent_column, table_columns)
				
				if child_column:
					column_info['physical_column_name'] = table_column.physical_column_name
					column_info['related_table'] = table_column.related_table
					
					related_user_table = UserTable.objects.get(pk=table_column.related_table)
					related_table_columns = UserTableColumn.objects.filter(table=related_user_table)
					
					related_column = utilities.list_find(lambda related_column: related_column.column_name == child_column, related_table_columns)
					column_info['related_column'] = related_column.physical_column_name
					
				else:
					column_info['physical_column_name'] = table_column.physical_column_name
				
				column_mapping.append(column_info)
				
		else:
			model_obj = target_model()
			
			for index, column_data in enumerate(row):
				column_info = column_mapping[index]
				
				if column_info.get('related_table'):
					related_user_table = UserTable.objects.get(pk=column_info['related_table'])
					related_model = opengis.create_model(related_user_table)
					
					related_model_object = related_model.objects.get(**{str(column_info['related_column']):column_data})
					setattr(model_obj, column_info['physical_column_name'], related_model_object)
					
				else:
					setattr(model_obj, column_info['physical_column_name'], column_data)
			
			model_obj.save()
	
	destination.close()
	
	import os
	os.remove(temp_csv_file)

def api_table_builtin_list(request):
	if request.method == 'GET':
		user_tables = UserTable.objects.filter(is_builtin=True).order_by('table_name')
		
		result = [{'id':user_table.id,'name':user_table.table_name} for user_table in user_tables]
		
		return api.APIResponse(api.API_RESPONSE_SUCCESS, result=result)
	
	else:
		return api.APIResponse(api.API_RESPONSE_GETONLY)

#######################################################################################
# USER QUERY
#######################################################################################

def api_query_create(request):
	if request.method == 'POST':
		account = Account.objects.get(user=request.user)
		
		query_name = request.POST.get('query_name')
		query_description = request.POST.get('query_description')
		starter_table = request.POST.get('starter_table')
		
		# Prepare display columns -- hierarchy1.hierarchy2.field_name
		display_columns = list()
		for display_column in request.POST.getlist('display'):
			(column_hierarchy, separator, column_id) = display_column.rpartition('.')
			column_hierarchy = _convert_hierarchy_id_to_name(column_hierarchy)
			display_columns.append({'hierarchy':column_hierarchy,'id':column_id})
		
		# Prepare filter columns
		filter_columns = list()
		for filter_column in request.POST.getlist('filter'):
			filter_json = simplejson.loads(filter_column)
			filter_json['column_hierarchy'] = _convert_hierarchy_id_to_name(filter_json.get('column_hierarchy'))
			filter_columns.append(filter_json)
		
		# Aggregate columns + group by
		# TODO
		
		# Order by
		# TODO
		
		user_query = UserQuery.objects.create(account=account,query_name=query_name,description=query_description,starter_table=UserTable(id=starter_table))
		
		# Store display columns
		for column in display_columns:
			UserQueryDisplayColumn.objects.create(query=user_query,column_hierarchy=column['hierarchy'],column=UserTableColumn(id=column['id']))
		
		# Store filter columns
		for column in filter_columns:
			is_variable = "value" not in column
			
			UserQueryFilter.objects.create(
				query=user_query,
				column_hierarchy=column['column_hierarchy'],
				column=UserTableColumn(id=column['column_id']),
				filter_function=column['function'],
				filter_value=column.get('value'),
				is_variable=is_variable,
			)

		return api.APIResponse(api.API_RESPONSE_SUCCESS, result={'id':user_query.id,'query_name':user_query.query_name})
		
	else:
		return api.APIResponse(api.API_RESPONSE_POSTONLY)

def api_query_edit(request):
	pass

def _convert_hierarchy_id_to_name(hierarchy):
	named_hierarchy = ""
	for id in hierarchy.split(".") if hierarchy else list():
		column = UserTableColumn.objects.get(pk=id)
		if named_hierarchy: named_hierarchy = named_hierarchy + '.'
		named_hierarchy = named_hierarchy + column.physical_column_name

	return named_hierarchy

def api_query_delete(request):
	if request.method == 'POST':
		user_query = UserQuery.objects.get(pk=request.POST.get('query_id'))
		
		UserQueryDisplayColumn.objects.filter(query=user_query).delete()
		UserQueryFilter.objects.filter(query=user_query).delete()
		UserQueryAggregateColumn.objects.filter(query=user_query).delete()
		UserQueryAggregateColumnGroupBy.objects.filter(query=user_query).delete()
		UserQueryOrderByColumn.objects.filter(query=user_query).delete()
		
		user_query.delete()
		
		return api.APIResponse(api.API_RESPONSE_SUCCESS)
		
	else:
		return api.APIResponse(api.API_RESPONSE_POSTONLY)

def api_query_list(request):
	pass

def api_query_execute(request):
	if request.method == 'GET':
		account = Account.objects.get(user=request.user)
		query_name = request.GET.get('query_name')
		
		user_query = UserQuery.objects.get(account=account, query_name=query_name)
		
		query_result = execute_query(user_query, request.GET, request.GET.get('limit'))
		
		result_format = request.GET.get('format')
		
		if result_format == "jsonp" and request.GET.get('callback'):
			result_json = request.GET.get('callback') + '({"query":"' + user_query.query_name + '","columns":["' + '","'.join(query_result['columns']) + '"],"values":' + utilities.json_dumps(query_result['values']) + '})'

		elif result_format == "geojson":
			result_json = utilities.convert_query_result_to_geojson(request, query_result['columns'], query_result['values'])
		
		elif result_format == "update":
			result_json = ""
			for result in query_result['values']:
				print result
				result_json = result_json + 'UPDATE opengis_thailandprovince SET in_region_id = %s WHERE id = %s;' % (result[1].id,result[0])
				
		else:
			columns_json = ""
			for column in query_result['columns']:
				if columns_json: columns_json = columns_json + ","
				columns_json = columns_json + '"' + column['name'] + '"'
			
			result_json = '{"query":"' + query_name + '","columns":[' + columns_json + '],"values":' + utilities.json_dumps(query_result['values']) + '}'
		
		return api.APIResponse(api.API_RESPONSE_SUCCESS, str_result=result_json)
		
	else:
		return api.APIResponse(api.API_RESPONSE_GETONLY)

def execute_query(user_query, parameters, result_limit=None):
	# column_manager = opengis.TableColumnManager(user_query.starter_table)
	
	display_columns = UserQueryDisplayColumn.objects.filter(query=user_query)

	# Generate 'columns' JSON
	result_columns = list()
	
	for display_column in display_columns:
		if display_column.is_aggregate:
			column_info = {'id':display_column.column_id.id,'name':display_column.column_id.id,'type':sql.TYPE_NUMBER,'physical_name':display_column.column_id.id,'related_table':''}
		else:
			column_info = _to_column_dict(display_column.column)
		
		if display_column.display_name: column_info['name'] = display_column.display_name
		column_info['column_hierarchy'] = display_column.column_hierarchy
		
		result_columns.append(column_info)
	
	# Create Starter Model
	starter_model = opengis.create_model(user_query.starter_table)
	data_objects = starter_model.objects.all()

	# Virtual Columns -- WILL DO
	# Figure out how to store virtual column login in database
	# Entry.objects.extra(select={'is_recent': "pub_date > '2006-01-01'"})

	# Group By
	group_by_columns = UserQueryGroupByColumn.objects.filter(query=user_query)
	for group_by in group_by_columns:
		data_objects = data_objects.values(group_by.column.physical_column_name)

	# Aggregate Columns
	aggregate_columns = UserQueryAggregateColumn.objects.filter(query=user_query)
	if group_by_columns: # If using 'values', we must use annotate, instead of aggregate
		for aggregate_column in aggregate_columns:
			column_info = _to_column_dict(aggregate_column.column)
			data_objects = data_objects.annotate(query.sql_aggregate(aggregate_column, column_info))
	else:
		for aggregate_column in aggregate_columns:
			column_info = _to_column_dict(aggregate_column.column)
			data_objects = data_objects.aggregate(query.sql_aggregate(aggregate_column, column_info))

	# Filter
	for filter in UserQueryFilter.objects.filter(query=user_query):
		if filter.is_variable:
			filter.filter_value = parameters.get(filter.filter_value)
			if not filter.filter_value: continue

		column_info = _to_column_dict(filter.column)
		data_objects = query.sql_filter(filter, column_info, data_objects)

	# Order by
	order_by_columns = UserQueryOrderByColumn.objects.filter(query=user_query).order_by('order_priority') # Less has more priority

	order_fields = list()
	for order_by_column in order_by_columns:
		if order_by_column.column_hierarchy:
			column_hierarchy = order_by_column.column_hierarchy.replace(".", "__") + "__"
		else:
			column_hierarchy = ""

		order_fields.append('-' if order_by_column.is_desc else '' + column_hierarchy + order_by_column.column_name)

	if order_fields: data_objects = data_objects.order_by(*order_fields)
	
	# Distinct
	if user_query.is_distinct:
		args = list()
		for result_column in result_columns:
			if result_column['column_hierarchy']:
				column_hierarchy = result_column['column_hierarchy'].replace(".", "__") + "__"
			else:
				column_hierarchy = ""
			
			args.append(column_hierarchy + result_column['physical_name'])
		
		data_objects = data_objects.values(*args)
		data_objects = data_objects.distinct()
	
	# Dump result in a list of list
	result = list()
	
	print data_objects

	if aggregate_columns and not group_by_columns: # using aggregate without grouping by will have result as a dict
		result_row = list()
		
		for result_column in result_columns:
			try:
				result_row.append(data_objects[result_column['physical_name']])
			except KeyError:
				result_row.append("")

		result.append(result_row)

	elif user_query.is_distinct: # Using distinct, result will be a list of dict that has a key like 'link1__link2__column1'
		for datum in data_objects:
			result_row = list()

			for result_column in result_columns:
				if result_column['column_hierarchy']:
					column_hierarchy = result_column['column_hierarchy'].replace(".", "__") + "__"
				else:
					column_hierarchy = ""

				result_row.append(datum[column_hierarchy + result_column['physical_name']])

			if result_row: result.append(result_row)

	else:
		result = _extract_query_result(user_query.starter_table, data_objects, result_columns)

	# Result limitation -- either define it in user query table or 'limit' parameter in request URL
	if user_query.result_limit or result_limit:
		limit = user_query.result_limit
		if result_limit: limit = int(result_limit)
		result = result[0:limit]

	return {'columns':result_columns,'values':result}

def _to_column_dict(table_column):
	return {
		'id':table_column.id,
		'name':table_column.column_name,
		'type':table_column.data_type,
		'physical_name':table_column.physical_column_name,
		'related_table':table_column.related_table,
	}

def _extract_query_result(starter_table, query_result, result_columns):
	result = list()
	
	for datum in query_result:
		result_row = list()
		
		for result_column in result_columns:
			if result_column['column_hierarchy']:
				hierarchy_list = result_column['column_hierarchy'].split(".")
				
				if type(datum).__name__ != 'dict':
					try:
						attr = datum
						for hierarchy in hierarchy_list: attr = getattr(attr, hierarchy)
						result_row.append(getattr(attr, result_column['physical_name']))
					except:
						result_row.append("")
					
				else: # query_result returns as a list of dict (cause by using group by)
					
					growing_hierarchy = ""
					hierarchy_user_table = starter_table
					hierarchy_data = None
					
					for index, hierarchy in enumerate(hierarchy_list):
						
						try:
							value = hierarchy_data.id
						except:
							value = datum[hierarchy]
						
						table_column = utilities.list_find(lambda table_column: table_column.physical_column_name==hierarchy, UserTableColumn.objects.filter(table=hierarchy_user_table))
						related_table = table_column.related_table
						
						hierarchy_user_table = UserTable.objects.get(pk=related_table)
						hierarchy_model_object = opengis.create_model(hierarchy_user_table)
						
						hierarchy_data = hierarchy_model_object.objects.get(pk=value)

					result_row.append(getattr(hierarchy_data, result_column['physical_name']))
					
			else:
				try:
					result_row.append(getattr(datum, result_column['physical_name']))
				except:
					try:
						result_row.append(datum[result_column['physical_name']])
					except:
						result_row.append("")
		
		if result_row: result.append(result_row)

	return result


def api_testbed(request):
	delete_column_id = request.GET.get("id")
	
	# Delete columns
	user_table_column = UserTableColumn.objects.get(pk=delete_column_id)
	user_table = user_table_column.table
	
	# TODO: Check permission
	
	cursor = connection.cursor()
	
	database_table_name = settings.MAIN_APPLICATION_NAME + "_" + user_table.table_class_name
	
	if user_table_column.data_type in (sql.TYPE_REGION, sql.TYPE_LOCATION):
		cursor.execute("SELECT DropGeometryColumn ('%s','%s')" % (database_table_name,user_table_column.physical_column_name))
	else:
		cursor.execute("ALTER TABLE %s DROP COLUMN %s" % (database_table_name,user_table_column.physical_column_name))
	
	transaction.set_dirty()
	
	user_table_column.delete()
		
	return api.APIResponse(api.API_RESPONSE_SUCCESS)
	
	