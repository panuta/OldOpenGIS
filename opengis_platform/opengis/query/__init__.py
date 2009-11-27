from django.db.models import *

from opengis import sql
from opengis.query.filters import *

def sql_filter(filter, data_objects, column_info):
	
	if filter.filter_function == "equal":
		return EqualFilter().sql_filter(filter, data_objects, column_info)
	
	elif filter.filter_function == "notequal":
		pass
	
	return data_objects

def sql_aggregate(aggregate_info):

	if aggregate_info.aggregate_func == sql.AGGREGATE_FUNC_AVG:
		return Avg(aggregate_info.column_name)

	elif aggregate_info.aggregate_func == sql.AGGREGATE_FUNC_COUNT:
		return Count(aggregate_info.column_name)

	return None