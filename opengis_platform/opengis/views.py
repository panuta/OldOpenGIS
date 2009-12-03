import datetime, time
import csv

from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render_to_response, redirect
from django.template import RequestContext
from django.utils import simplejson
from django.utils.translation import ugettext as _

import opengis
from opengis import constants, sql, errors, query, utilities
from opengis.models import *
from opengis.forms import *
from opengis.shortcuts import *

def registered_user_callback(sender, **kwargs):
	# Create a new Account model instance
	Account.objects.create(user=kwargs['user'])

##############################
# HOMEPAGE
##############################
from registration.forms import RegistrationForm
from django.contrib.auth.forms import AuthenticationForm

def view_homepage(request):
	if request.user.is_authenticated(): return redirect(settings.LOGIN_REDIRECT_URL)

	if request.method == "POST":
		submit_type = request.POST.get('submit_button')

		if submit_type == "register":
			from registration.views import register
			return register(request, 'registration.backends.default.DefaultBackend')

		elif submit_type == "login":
			from django.contrib.auth.views import login
			return login(request)

		else:
			return redirect("/")

	else:
		register_form = RegistrationForm(auto_id=False)
		login_form = AuthenticationForm(auto_id=False)

	return render_to_response(settings.OPENGIS_TEMPLATE_PREFIX + "homepage.html", {'register_form':register_form, 'login_form':login_form}, context_instance=RequestContext(request))

##############################
# PROFILE
##############################
def view_user_home(request, username):
	(user, account, is_owner) = get_user_auth(request, username)
	if is_owner: return redirect(reverse("opengis_view_my_home"))
	
	if user == request.user:
		user_tables = UserTable.objects.filter(account=account).order_by('-created')[:5]
		user_queries = UserQuery.objects.filter(account=account).order_by('-created')[:5]
	else:
		user_tables = UserTable.objects.filter(account=account, share_level=9).order_by('-created')
		user_queries = UserQuery.objects.filter(account=account).order_by('-created')
	
	for table in user_tables: table.columns = [column.column_name for column in UserTableColumn.objects.filter(table=table)]
	
	return render_to_response(settings.OPENGIS_TEMPLATE_PREFIX + "user_home.html", {'account':account, 'user_tables':user_tables, 'user_queries':user_queries}, context_instance=RequestContext(request))

##############################
# DYNAMIC TABLE
##############################
def list_user_table(request, username):
	(user, account, is_owner) = get_user_auth(request, username)
	if is_owner: return redirect(reverse("opengis_list_my_table"))
	
	user_tables = UserTable.objects.filter(account=account)
	for table in user_tables: table.columns = [column.column_name for column in UserTableColumn.objects.filter(table=table)]
	
	return render_to_response(settings.OPENGIS_TEMPLATE_PREFIX + "table_list.html", {'account':account, 'user_tables':user_tables}, context_instance=RequestContext(request))

def ajax_list_user_table(request):
	username = request.GET.get('username')
	
	try:
		(user, account, is_owner) = get_user_auth(request, username)
	except errors.OpenGISNotLoginError:
		return HttpResponse(errors.format_ajax_return(errors.AJAX_NOT_AUTHENTICATED))
	
	if user == request.user:
		user_tables = UserTable.objects.filter(account=account)
	else:
		user_tables = UserTable.objects.filter(account=account, share_level=9)
	
	result = [{'id':table.id,'name':table.table_name,'description':table.description if table.description else ''} for table in user_tables]
	
	return HttpResponse(errors.format_ajax_return(errors.AJAX_SUCCESS,{},"tables:" + simplejson.dumps(result)))

def view_user_table(request, username, table_name):
	account = Account.objects.get(user=request.user)
	
	user_table = get_object_or_404(UserTable, account=account, table_name=table_name)
	user_table.columns = UserTableColumn.objects.filter(table=user_table).order_by('created')

	table_model = opengis._create_model(user_table, user_table.columns)
	table_data = table_model.objects.all()

	return render_to_response(settings.OPENGIS_TEMPLATE_PREFIX + "table_view.html", {'account':account, 'user_table':user_table, 'table_data':table_data}, context_instance=RequestContext(request))

# FORMAT: columns=[column_name]:[column_type]:[option_name]--[option_value]&columns=[column_name]:[column_type]:[option_name]--[option_value]
@login_required
def create_user_table(request):
	account = Account.objects.get(user=request.user)
	
	columns = list()
	columns_errors = list()
	
	if request.method == "POST":
		form = ModifyTableForm(request, request.POST)
		
		(columns, error_flag) = _extract_user_table_columns_string(request.POST.getlist('columns'))
		
		if not columns:
			columns_errors.append("Table must have at least one column")
			
		elif form.is_valid() and not error_flag:
			table_name = form.cleaned_data['table_name']
			description = form.cleaned_data['description']
			tags = form.cleaned_data['tags']
			share_level = form.cleaned_data['share_level']
			display_column = form.cleaned_data['display_column']
		
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
					column_name=column.get('name'), 
					physical_column_name=column.get('physical_name'), 
					data_type=column.get('type'), 
					related_table=column.get('related')
					))

			# Create table at database server
			sql.sql_create_table(user_table, user_table_columns)

			return redirect(reverse("opengis_view_my_table", args=[table_name]))
				
	else:
		form = ModifyTableForm(request)
	
	user_tables = UserTable.objects.filter(account=account)
	
	return render_to_response(settings.OPENGIS_TEMPLATE_PREFIX + "table_create.html", {'account':account, 'form':form, 'columns':columns, 'columns_errors':columns_errors}, context_instance=RequestContext(request))

def ajax_input_user_table(request):
	pass

@login_required
def edit_user_table(request, table_name):
	account = Account.objects.get(user=request.user)
	
	user_table = get_object_or_404(UserTable, account=account, table_name=table_name)
	user_table.columns = UserTableColumn.objects.filter(table=user_table).order_by('created')
	
	columns_errors = list()
	
	if request.method == "POST":
		form = ModifyTableForm(request, request.POST)
		
		rename_columns = request.POST.getlist("rename_column")
		delete_columns = request.POST.getlist("delete_column")
		
		(columns, error_flag) = _extract_user_table_columns_string(request.POST.getlist('columns'))
		
		if not columns and len(delete_columns) >= len(user_table.columns):
			columns_errors.append("Table must have at least one column")
			
		elif form.is_valid() and not error_flag:
			table_name = form.cleaned_data['table_name']
			description = form.cleaned_data['description']
			tags = form.cleaned_data['tags']
			share_level = form.cleaned_data['share_level']
			display_column = form.cleaned_data['display_column']
			
			pass
		
		
		
		
		"""
		(columns, error_flag) = _extract_user_table_columns_string(request.POST.getlist('columns'))
		
		if not columns:
			columns_errors.append("Table must have at least one column")

		elif form.is_valid() and not error_flag:
			table_name = form.cleaned_data['table_name']
			description = form.cleaned_data['description']
			tags = form.cleaned_data['tags']
			share_level = form.cleaned_data['share_level']
			display_column = form.cleaned_data['display_column']
			
			# Check table name duplication
			table_name = request.POST['table_name']
			if UserTable.objects.filter(account=account, table_name=table_name).count():
				form.errors.table_name = _("This table name is already existed.")
			
			else:
				
				
				# Update table metadata
				user_table = UserTable.objects.create(account=account, table_name=table_name, description=description, share_level=share_level, display_column=display_column)
				user_table.save()
				
				return redirect(reverse("opengis_view_my_table", args=[table_name]))
				
		"""
		
	else:
		form = ModifyTableForm(request, initial={
			'table_name':user_table.table_name,
			'description':user_table.description,
			'share_level':user_table.share_level,
			'display_column':user_table.display_column,
			'existing_table_id':user_table.id,
		})
		
		# TODO Convert user_table.columns to columns
		
	
	return render_to_response(settings.OPENGIS_TEMPLATE_PREFIX + "table_edit.html", {'account':account, 'form':form, 'user_table':user_table}, context_instance=RequestContext(request))

def _extract_user_table_columns_string(raw_columns):
	columns = list()
	error_flag = False
	column_count = 1 # Did not use enumerate because this way it will not count if column format in invalid
	
	for raw_column in raw_columns:
		splited = raw_column.split(':')
	
		if len(splited) < 2: continue # Ignore if column information is missing
		
		column = {'name':splited[0]}
		type_string = splited[1]
	
		for column_option in splited[2:]:
			(option_name, splitter, option_value) = column_option.partition(constants.CREATE_TABLE_COLUMN_OPTION_SPLITTER)
			if option_value.isdigit(): option_value = int(option_value)
			column[option_name] = option_value
		
		if type_string == "mine" or type_string == "others": type_string = "table"
	
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
		
		if type_string == "table": # Check both 'mine' and 'others'
			related_table = UserTable.objects.get(table_id=column['related'])
			
			if related_table.account != account and related_table.share_level != 9:
				column['error'] = _("This table is private table")
				error_flag = True
		
		if column_type != 0:
			column['type'] = column_type
			column['physical_name'] = "column_" + str(column_count)
			columns.append(column)
		
			column_count = column_count + 1
	
	return (columns, error_flag)

@login_required
def delete_user_table(request, table_name):
	pass

@login_required
def import_user_table(request, table_name):
	account = Account.objects.get(user=request.user)
	
	user_table = get_object_or_404(UserTable, account=account, table_name=table_name)
	
	if request.method == "POST":
		form = ImportDataToTableForm(request.POST, request.FILES)
		if form.is_valid():
			temp_csv_file = settings.TEMP_CSV_PATH + '/temp_' + str(account.user.id) + "_" + str(long(round(time.time()))) + '.csv'
			
			destination = open(temp_csv_file, 'wb')
			for chunk in request.FILES['file'].chunks(): destination.write(chunk)
			destination.close()
			
			destination = open(temp_csv_file, 'rb')
			csv_reader = csv.reader(destination)
			
			user_table = UserTable.objects.get(account=account, table_name=table_name)
			table_columns = UserTableColumn.objects.filter(table=user_table)
			
			target_model = opengis._create_model(user_table, table_columns)
			target_model.objects.all().delete()
			
			column_mapping = list()
			
			for row in csv_reader:
				if not column_mapping:
					# Map logical column name used in CSV to physical database column name
					for index, column_name in enumerate(row):
						to_physical_name = ""
						for table_column in table_columns:
							if table_column.column_name == column_name: to_physical_name = table_column.physical_column_name
						
						column_mapping.append(to_physical_name)
					
				else:
					model_obj = target_model()
					
					for index, column_data in enumerate(row):
						if column_mapping[index]:
							setattr(model_obj, column_mapping[index], column_data)
					
					model_obj.save()
			
			destination.close()
			
			import os
			os.remove(temp_csv_file)
			
			return redirect(reverse('opengis_import_my_table', args=[table_name]))
		
	else:
		form = ImportDataToTableForm(auto_id=False)
	
	return render_to_response(settings.OPENGIS_TEMPLATE_PREFIX + "table_import.html", {'account':account, 'user_table':user_table, 'form':form}, context_instance=RequestContext(request))

def ajax_get_table_columns(request):
	table_codes = request.GET.getlist('table_code')
	
	result = list()
	for table_code in table_codes:
		if table_code in REGISTERED_BUILT_IN_TABLES:
			table_columns = REGISTERED_BUILT_IN_TABLES[table_code].Info.columns
		
			columns = [{'name':table_columns[column_code]['name'],'value':table_columns[column_code]['physical_name']} for column_code in table_columns.keys()]
		
		elif table_code:
			user_table = UserTable.objects.get(pk=table_code)
			table_columns = UserTableColumn.objects.filter(table=user_table)
		
			columns = [{'name':column.column_name,'value':column.physical_column_name} for column in table_columns]
		
		result = {'table':table_code,'columns':columns}
	
	if result:
		return HttpResponse(errors.format_ajax_return(errors.AJAX_SUCCESS,{},"columns:" + simplejson.dumps(result)))
	else:
		return HttpResponse(errors.format_ajax_return(errors.AJAX_RESOURCE_NOT_FOUND))

def search_public_table(request):
	return render_to_response(settings.OPENGIS_TEMPLATE_PREFIX + "table_search.html", {}, context_instance=RequestContext(request))

##############################
# TABLE QUERY
##############################
def list_user_query(request, username):
	(user, account, is_owner) = get_user_auth(request, username)
	if is_owner: return redirect(reverse("opengis_list_my_query"))
	
	user_queries = UserQuery.objects.filter(account=account)
	return render_to_response(settings.OPENGIS_TEMPLATE_PREFIX + "query_list.html", {'account':account, 'user_queries':user_queries}, context_instance=RequestContext(request))

def view_user_query(request, query_name):
	pass

def visualize_user_query(request, query_name):
	pass

@login_required
def create_user_query(request):
	account = Account.objects.get(user=request.user)
	
	if request.method == "POST":
		
		return redirect(reverse("opengis_view_my_query", args=[query_name]))
	else:
		form = CreateQueryForm()
	
	user_queries = UserQuery.objects.filter(account=account)
	
	return render_to_response(settings.OPENGIS_TEMPLATE_PREFIX + "query_create.html", {'account':account, 'form':form, 'user_queries':user_queries}, context_instance=RequestContext(request))
	

@login_required
def edit_user_query(request, query_name):
	pass

@login_required
def delete_user_query(request, query_name):
	pass






# Format: {'query_name':'query_name', columns:['column1',column2], values:[['value1', 'value2'],['value1', 'value2']]}
def query_user_table(request, username, query_name):
	"""
	try:
		(user, account) = check_user_auth(request)
	except errors.OpenGISNotLoginError:
		return shortcuts.redirect_to_login(request)
	"""
	
	# TEMP: Does not check user authentication
	user = User.objects.get(username=username)
	account = Account.objects.get(user=user)
	

	user_query = get_object_or_404(UserQuery, query_name=query_name)
	display_columns = UserQueryDisplayColumn.objects.filter(query=user_query)
	
	column_manager = opengis.UserTableColumnManager(user_query.starter_table) # For caching user table columns information (less database hit)
	
	# Generate 'columns' JSON
	result_columns = list()
	
	for display_column in display_columns:
		if display_column.display_name: # Custom display name will have more priority than user table column name
			column = display_column.display_name
		else:
			column = column_manager.get_column_info(display_column.column_hierarchy, display_column.column_name)['name']
		
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
			filter.filter_value = request.GET.get(filter.filter_value)
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
	
	# data_objects = list(data_objects)
	# from django.db import connection
	# print connection.queries[len(connection.queries)-1]['sql']
	
	# Dump result in a list of list
	result = list()
	
	if aggregate_columns and not group_by_columns: # using aggregate without group by will have query result as a dict
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
				
					else: # result return as a list of dict, and has hierarchy columns
				
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
	if user_query.result_limit or request.GET.get('limit'):
		limit = user_query.result_limit
		if request.GET.get('limit'): limit = int(request.GET.get('limit'))
		result = result[0:limit]
	
	# Different result format (default is JSON)
	if request.GET.get('format') == "jsonp" and request.GET.get('callback'):
		return HttpResponse(request.GET.get('callback') + '({"query":"' + query_name + '","columns":["' + '","'.join(result_columns) + '"],"values":' + utilities.json_dumps(result) + '})')
	
	elif request.GET.get('format') == "geojson":
		return HttpResponse(utilities.convert_query_result_to_geojson(request, result_columns, result))

	else:
		return HttpResponse('{"query":"' + query_name + '","columns":["' + '","'.join(result_columns) + '"],"values":' + utilities.json_dumps(result) + '}')



@login_required
def build_user_table_query(request):
	account = Account.objects.get(user=request.user)
	user_tables = UserTable.objects.filter(account=account)
	
	return render_to_response(settings.OPENGIS_TEMPLATE_PREFIX + "table_query_builder.html", {'account':account, 'user_tables':user_tables}, context_instance=RequestContext(request))

def ajax_get_tables_for_query_builder(request):
	account = Account.objects.get(user=request.user)
	
	table_ids = request.GET.getlist('table_ids')
	tables = list()
	
	for table_id in table_ids:
		columns = list()
		
		try:
			user_table = UserTable.objects.get(pk=table_id)
		except UserTable.DoesNotExist:
			return HttpResponse(errors.return_resource_not_found("UserTable", table_ids))
		else:
			user_table_columns = UserTableColumn.objects.filter(table=user_table)
			
			for user_table_column in user_table_columns:
				columns.append({'name':user_table_column.column_name, 'physical_name':user_table_column.physical_column_name, 'type':user_table_column.data_type, 'related_table':user_table_column.related_table})
		
		tables.append({'table_name':user_table.table_name, 'columns':columns})
		
		# TODO: add filters
		# TODO: add visible columns
		# TODO: add order by columns
		# TODO: add new columns
		# TODO: add aggregate functions
		
	
	return HttpResponse(simplejson.dumps({'tables':tables}))

def ajax_save_building_query(request):
	account = Account.objects.get(user=request.user)
	
	if request.method == "POST":
		query_name = request.POST.get("query_name")
		
		try:
			user_query = UserQuery.objects.get(query_name=query_name)
		except UserQuery.DoesNotExist:
			user_query = UserQuery()
			user_query.account = account
		
		user_query.query_name = query_name
		user_query.starter_table = request.POST.get("starter_table")
		user_query.save()
		
		display_columns = request.POST.getlist("display_columns")
		
		# TODO: Will change to another method that won't waste auto-increment index, if auto-save is in use
		UserQueryDisplayColumn.objects.filter(query=user_query).delete()
		
		for display_column in display_columns:
			UserQueryDisplayColumn.objects.create(query=user_query, column_name=display_column, column_hierarchy="")
		
		return HttpResponse('{"response":"success"}')
	
	else:
		return redirect(reverse('opengis_build_my_query'))

def simplify_shape(request):
	for province in ThailandProvince.objects.all():
		
		from django.contrib.gis.geos import GEOSGeometry
		
		try:
			province.region_simple = GEOSGeometry(province.region.simplify(0.03, True).wkt)
			province.save()
		except:
			province.region_simple = GEOSGeometry(province.region.simplify(0.03, True).wkt.replace('POLYGON ', 'MULTIPOLYGON (') + ')')
			province.save()
	
	return HttpResponse('')

def load_shape(request):
	from django.contrib.gis.utils.layermapping import LayerMapping
	from django.contrib.gis.gdal import DataSource
	from opengis.models import ThailandProvince

	ds = DataSource('/Users/apple/Projects/OpenGIS/OpenGIS/opengis_platform/files/shape/thailand_province/changwat_region_Project.shp')

	mapping = {
	    'name_th' : 'TNAME',
	    'name' : 'ENAME',
	    'region' : 'POLYGON',
	}

	lm = LayerMapping(ThailandProvince, ds, mapping, encoding='tis-620')
	lm.save(verbose=True)
	
	return HttpResponse('')

def get_user_table_json(request, table_name):
	account = Account.objects.get(user=request.user)
	
	user_table = get_object_or_404(UserTable, table_name=table_name)
	user_table.columns = UserTableColumn.objects.filter(table=user_table)
	
	model_class = opengis._create_model(user_table, user_table.columns)
	data = model_class.objects.all()
	
	result = list()
	for datum in model_class.objects.all():
		row_dict = dict()
		
		for index, column in enumerate(user_table.columns):
			row_dict[column.column_name] = getattr(datum, column.column_name)
		
		result.append(row_dict)
	
	return HttpResponse(simplejson.dumps(result), content_type='text/plain; charset=UTF-8')

def get_user_table_visualize(request, table_name):
	account = Account.objects.get(user=request.user)
	return render_to_response(settings.OPENGIS_TEMPLATE_PREFIX + "visualization/flu_home.html", {'account':account, 'table_name':table_name}, context_instance=RequestContext(request))
