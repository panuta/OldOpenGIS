from opengis import utilities, sql

class EqualFilter(object):
	
	def sql_filter(self, filter, data_objects, column_manager):
		if filter.column_hierarchy:
			hierarchy = filter.column_hierarchy.replace(".", "__") + "__"
		else:
			hierarchy = ""
		
		column_info = column_manager.get_column_info(filter.column_hierarchy, filter.column_id)
		
		if column_info['type'] == sql.TYPE_DATE:
			filter.filter_value = filter.filter_value[0:4] + "-" + filter.filter_value[4:6] + "-" + filter.filter_value[6:8]
		
		kwargs = {str(hierarchy + column_info['physical_name']):filter.filter_value}
		return data_objects.filter(**kwargs)
	
	def logic_filter(self):
		pass