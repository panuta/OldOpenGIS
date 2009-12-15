from django.db.models import *

from opengis import sql
from opengis.query.filters import *

def sql_filter(filter, column_info, data_objects):
	
	if filter.filter_function == "equal":
		return EqualFilter().sql_filter(filter, column_info, data_objects)
	
	elif filter.filter_function == "notequal":
		pass
	
	return data_objects

def sql_aggregate(aggregate_info, column_info):

	if aggregate_info.aggregate_func == sql.AGGREGATE_FUNC_AVG:
		return Avg(column_info['physical_name'])

	elif aggregate_info.aggregate_func == sql.AGGREGATE_FUNC_COUNT:
		return Count(column_info['physical_name'])

	return None