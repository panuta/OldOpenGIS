from django.conf import settings
from django.contrib.auth.models import User
from django.db import connection, transaction
from django.utils import simplejson

import opengis
from opengis import api, constants, sql, errors, query, utilities
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
			user_table.table_class_name = constants.USER_TABLE_PREFIX + "_" + str(user_table.account.user.id) + "_" + str(user_table.id)
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
			sql.sql_create_table(user_table, user_table_columns)
			
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
			
			database_table_name = constants.APPLICATION_NAME + "_" + user_table.table_class_name
			
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
		
		table_model = opengis._create_model(user_table, user_table_columns)
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
		database_table_name = constants.APPLICATION_NAME + "_" + user_table.table_class_name
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
	
	if type_string == "char": column_type = sql.TYPE_CHARACTER
	elif type_string == "number": column_type = sql.TYPE_NUMBER
	elif type_string == "datetime": column_type = sql.TYPE_DATETIME
	elif type_string == "date": column_type = sql.TYPE_DATE
	elif type_string == "time": column_type = sql.TYPE_TIME
	elif type_string == "region": column_type = sql.TYPE_REGION
	elif type_string == "location": column_type = sql.TYPE_LOCATION
	elif type_string == "table": column_type = sql.TYPE_USER_TABLE
	elif type_string == "builtin": column_type = sql.TYPE_BUILT_IN_TABLE
	else: column_type = 0

	if type_string == "table":
		related_table = UserTable.objects.get(pk=column['related'])

		if related_table.account != current_account and related_table.share_level != 9:
			pass
			# RAISE NO ACCESS to private table
	
	if column_type != 0:
		column['type'] = column_type
	
	return column

def api_table_info(request):
	if request.method == 'GET':
		table_codes = request.GET.getlist('table_code')
		result = list()
		
		for table_code in table_codes:
			if table_code in REGISTERED_BUILT_IN_TABLES:
				table_columns = REGISTERED_BUILT_IN_TABLES[table_code].Info.columns

				table_id = REGISTERED_BUILT_IN_TABLES[table_code].Info.code
				name = REGISTERED_BUILT_IN_TABLES[table_code].Info.name
				columns = [{'id':table_columns[column_code]['physical_name'],'name':table_columns[column_code]['name'],'physical_name':table_columns[column_code]['physical_name']} for column_code in table_columns.keys()]

			elif table_code:
				user_table = UserTable.objects.get(pk=table_code)
				table_columns = UserTableColumn.objects.filter(table=user_table)

				table_id = user_table.id
				name = user_table.table_name
				columns = [{'id':column.id,'name':column.column_name,'physical_name':column.physical_column_name} for column in table_columns]

			result.append({'id':table_id, 'name':name,'code':table_code,'columns':columns})
		
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
			(column_hierarchy, separator, column_name) = display_column.rpartition('.')
			display_columns.append({'hierarchy':column_hierarchy,'name':column_name})
		
		
		# Prepare filter columns
		filter_columns = list()
		for filter_column in request.POST.getlist('filter'):
			filter_columns.append(simplejson.loads(filter_column))
		
		# Aggregate columns + group by
		
		# Order by
		
		user_query = UserQuery.objects.create(account=account,query_name=query_name,description=query_description,starter_table=starter_table)
		
		# Store display columns
		for column in display_columns:
			UserQueryDisplayColumn.objects.create(query=user_query,column_hierarchy=column['hierarchy'],column_name=column['name'])
		
		# Store filter columns
		for column in filter_columns:
			is_variable = "value" not in column
			UserQueryFilter.objects.create(
				query=user_query,
				column_hierarchy='',
				column_name=UserTableColumn.objects.get(pk=column['column_id']).physical_column_name, # Quick hack!
				filter_function=column['function'],
				filter_value=column.get('value'),
				is_variable=is_variable,
			)

		return api.APIResponse(api.API_RESPONSE_SUCCESS, result={'id':user_query.id,'name':user_query.query_name})
		
	else:
		return api.APIResponse(api.API_RESPONSE_POSTONLY)

def api_query_edit(request):
	pass

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

		else:
			result_json = '{"query":"' + query_name + '","columns":["' + '","'.join(query_result['columns']) + '"],"values":' + utilities.json_dumps(query_result['values']) + '}'
		
		return api.APIResponse(api.API_RESPONSE_SUCCESS, str_result=result_json)
		
	else:
		return api.APIResponse(api.API_RESPONSE_GETONLY)

def execute_query(user_query, parameters, result_limit=None):
	display_columns = UserQueryDisplayColumn.objects.filter(query=user_query)
	
	column_manager = opengis.UserTableColumnManager(user_query.starter_table) # For caching user table columns information (less database hit)
	
	# Generate 'columns' JSON
	result_columns = list()

	for display_column in display_columns:
		column = column_manager.get_column_info(display_column.column_hierarchy, display_column.column_name)
		column['display_name'] = display_column.display_name
		result_columns.append(column)
	
	# Create Starter Model
	if user_query.starter_table in REGISTERED_BUILT_IN_TABLES:
		starter_model = REGISTERED_BUILT_IN_TABLES[user_query.starter_table]

	else:
		user_table = UserTable.objects.get(pk=user_query.starter_table)
		table_columns = UserTableColumn.objects.filter(table=user_table)

		starter_model = opengis._create_model(user_table, table_columns)

	data_objects = starter_model.objects.all()
	
	# Virtual Columns -- WILL DO
	# Figure out how to store virtual column login in database
	# Entry.objects.extra(select={'is_recent': "pub_date > '2006-01-01'"})
	
	# Group By
	group_by_columns = UserQueryAggregateColumnGroupBy.objects.filter(query=user_query)
	for group_by in group_by_columns:
		data_objects = data_objects.values(group_by.column_name)
	
	# Aggregate Columns
	aggregate_columns = UserQueryAggregateColumn.objects.filter(query=user_query)
	if group_by_columns: # If using 'values', we must use annotate, instead of aggregate
		for aggregate_column in aggregate_columns:
			data_objects = data_objects.annotate(query.sql_aggregate(aggregate_column))
	else:
		for aggregate_column in aggregate_columns:
			data_objects = data_objects.aggregate(query.sql_aggregate(aggregate_column))
	
	# Filter
	for filter in UserQueryFilter.objects.filter(query=user_query):
		if filter.is_variable:
			filter.filter_value = parameters.get(filter.filter_value)
			if not filter.filter_value: continue
		
		column_info = column_manager.get_column_info(filter.column_hierarchy, filter.column_name)
		data_objects = query.sql_filter(filter, data_objects, column_info)
	
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
	
	if user_query.is_distinct:
		for display_column in display_columns:
			if display_column.column_hierarchy:
				column_hierarchy = display_column.column_hierarchy.replace(".", "__") + "__"
			else:
				column_hierarchy = ""
			
			data_objects = data_objects.values(column_hierarchy + display_column.column_name)
		
		data_objects = data_objects.distinct()
	
	# Dump result in a list of list
	result = list()
	
	if aggregate_columns and not group_by_columns: # using aggregate without grouping by will have result as a dict
		result_row = list()
		
		for display_column in display_columns:
			try:
				result_row.append(data_objects[display_column.column_name])
			except KeyError:
				pass
		
		result.append(result_row)
	
	elif user_query.is_distinct: # Using distinct, result will be a list of dict that has a key like 'link1__link2__column1'
		for datum in data_objects:
			result_row = list()
			
			for display_column in display_columns:
				if display_column.column_hierarchy:
					column_hierarchy = display_column.column_hierarchy.replace(".", "__") + "__"
				else:
					column_hierarchy = ""
				
				result_row.append(datum[column_hierarchy + display_column.column_name])
			
			if result_row: result.append(result_row)
	
	else:
	 	for datum in data_objects:
			result_row = list()

			for display_column in display_columns:
				if display_column.column_hierarchy:
					hierarchy_list = display_column.column_hierarchy.split(".")

					if not group_by_columns:
						try:
							attr = getattr(datum, hierarchy_list[0])
							for hierarchy in hierarchy_list[1:]: attr = getattr(attr, hierarchy)
							result_row.append(getattr(attr, display_column.column_name))
						except:
							result_row.append("") # something bad happened, return empty string instead
					
					else: # result return as a list of dict, and display column has hierarchy information

						related_table = column_manager.get_column_info('', hierarchy_list[0])['related_table']

						for index, hierarchy in enumerate(hierarchy_list):

							if index == 0:
								related_table = column_manager.get_column_info('', hierarchy_list[0])['related_table']

							else:
								column_info = column_mapping[hierarchy]

								if type(column_info).__name__ == 'dict':
									related_table = column_info['related_table']
								else:
									related_table = column_info.related_table

							if related_table in REGISTERED_BUILT_IN_TABLES:
								hierarchy_model_object = REGISTERED_BUILT_IN_TABLES[related_table]
								column_mapping = hierarchy_model_object.columns

							else:
								hierarchy_user_table = UserTable.objects.get(pk=related_table)
								hierarchy_table_columns = UserTableColumn.objects.filter(table=user_table)

								column_mapping = dict()
								for table_column in hierarchy_table_columns: column_mapping[table_column.physical_column_name] = table_column

								hierarchy_model_object = opengis._create_model(hierarchy_user_table, hierarchy_table_columns)

							hierarchy_data = hierarchy_model_object.objects.get(pk=datum[hierarchy])

						result_row.append(getattr(hierarchy_data, display_column.column_name))

				else:
					try:
						result_row.append(getattr(datum, display_column.column_name))
					except:
						try:
							result_row.append(datum[display_column.column_name])
						except:
							result_row.append("") # Can't find a proper value for you, give you an empty string instead, ok?

			if result_row: result.append(result_row)

	# Result limitation -- either define it in user query table or 'limit' parameter in request URL
	if user_query.result_limit or result_limit:
		limit = user_query.result_limit
		if result_limit: limit = int(result_limit)
		result = result[0:limit]
	
	return {'columns':result_columns,'values':result}

def api_testbed(request):
	delete_column_id = request.GET.get("id")
	
	# Delete columns
	user_table_column = UserTableColumn.objects.get(pk=delete_column_id)
	user_table = user_table_column.table
	
	# TODO: Check permission
	
	cursor = connection.cursor()
	
	database_table_name = constants.APPLICATION_NAME + "_" + user_table.table_class_name
	
	if user_table_column.data_type in (sql.TYPE_REGION, sql.TYPE_LOCATION):
		cursor.execute("SELECT DropGeometryColumn ('%s','%s')" % (database_table_name,user_table_column.physical_column_name))
	else:
		cursor.execute("ALTER TABLE %s DROP COLUMN %s" % (database_table_name,user_table_column.physical_column_name))
	
	transaction.set_dirty()
	
	user_table_column.delete()
		
	return api.APIResponse(api.API_RESPONSE_SUCCESS)
	
	