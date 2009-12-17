from datetime import datetime, date, time
import re

from django.contrib.gis.geos.collections import *
from django.utils import simplejson

import opengis
from opengis.models import *

def _two_digit(value):
	if value < 10: return "0" + str(value)
	return str(value)

def list_find(f, seq):
	for item in seq:
		if f(item): 
			return item

# Dump a list of list to JSON
def json_dumps(result_list):
	json = ""

	for row in result_list:
		row_json = ""

		for value in row:
			if row_json: row_json += ","
			row_json += as_string(value)

		if json: json += ","
		json += '[%s]' % row_json

	return '[%s]' % json

# Convert any type to string representation
def as_string(value):
	if isinstance(value, MultiPolygon):
		return value.geojson

	elif isinstance(value, ThailandProvince):
		return str(value.id)

	elif isinstance(value, ThailandRegion):
		return str(value.id)

	elif type(value).__name__=='date':
		return str(value.year) + _two_digit(value.month) + _two_digit(value.day)

	else:
		return simplejson.dumps(value)

def convert_query_result_to_geojson(request, columns, result):
	geometry_field = request.GET.get('geometry') # Use display name, not database name

	features = list()
	for result_row in result:
		geometry_geojson = ""
		properties = list()

		for index, result_item in enumerate(result_row):

			if isinstance(result_item, MultiPolygon):
				if not geometry_field or columns[index] == geometry_field:
					geometry_geojson = '"geometry": %s' % result_item.geojson

			else:
				properties.append('"%s":%s' % (columns[index], simplejson.dumps(result_item)))

		if geometry_geojson: geometry_geojson = "," + geometry_geojson

		features.append('{"type":"Feature"%s,"properties":{%s}}' % (geometry_geojson, ','.join(properties)))

	return '{"type": "FeatureCollection","features":[%s]}' % ','.join(features)

def convert_string_to_data_with_format(column_data, table_column):
	data = {'value': column_data, 'error': ''}
	if column_data.strip():
		data_type = table_column.data_type
		try:
			if data_type == sql.TYPE_CHARACTER: data['value'] = str(column_data)
			elif data_type == sql.TYPE_NUMBER: data['value'] = float(column_data)
			elif data_type == sql.TYPE_DATETIME: data['value'] = datetime.strptime(column_data, '%Y-%m-%d %H:%M:%S')
			elif data_type == sql.TYPE_DATE: data['value'] = datetime.strptime(column_data, '%Y-%m-%d').date()
			elif data_type == sql.TYPE_TIME: data['value'] = datetime.strptime(column_data, '%H:%M:%S').time()
			elif data_type == sql.TYPE_REGION: data['value'] = GEOSGeometry(column_data)
			elif data_type == sql.TYPE_LOCATION: data['value'] = GEOSGeometry(column_data)
			elif data_type == sql.TYPE_USER_TABLE or data_type == sql.TYPE_BUILT_IN_TABLE: 
				related_user_table = UserTable.objects.get(pk=table_column.related_table)
				related_model = opengis.create_model(related_user_table)
				related_model_row_id = re.search(r'\[id\:(\d+)\]', column_data)
				column_data = related_model_row_id.group(1)
				data['value'] = related_model.objects.get(pk=column_data)
		except ValueError as error:
			data['error'] = table_column.column_name + ': ' + error.message
	else:
		data['value'] = None

	return data