from django.contrib.gis.geos.collections import *
from django.utils import simplejson

from opengis.models import *

def _two_digit(value):
	if value < 10: return "0" + str(value)
	return str(value)

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
		return str(value.year) + utilities._two_digit(value.month) + utilities._two_digit(value.day)

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