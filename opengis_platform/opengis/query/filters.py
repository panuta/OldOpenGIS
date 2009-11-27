from opengis import utilities, sql

class EqualFilter(object):
	
	def sql_filter(self, filter, data_objects, column_info):
		if filter.column_hierarchy:
			hierarchy = filter.column_hierarchy.replace(".", "__") + "__"
		else:
			hierarchy = ""
		
		if column_info['type'] == sql.TYPE_DATE:
			filter.filter_value = filter.filter_value[0:4] + "-" + filter.filter_value[4:6] + "-" + filter.filter_value[6:8]
			
		kwargs = {str(hierarchy + filter.column_name):filter.filter_value}
		return data_objects.filter(**kwargs)
	
	def logic_filter(self):
		pass