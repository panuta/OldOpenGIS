from django.core.management.color import no_style
from django.core.management.sql import custom_sql_for_model
from django.db import connection, transaction, models

import opengis

DEFAULT_CHARACTER_LENGTH = 512

TYPE_CHARACTER = 1
TYPE_INTEGER = 2
TYPE_DATETIME = 3
TYPE_DATE = 4
TYPE_TIME = 5
TYPE_REGION = 6
TYPE_LOCATION = 7
TYPE_USER = 8
TYPE_MY_TABLE = 9
TYPE_PREDEFINED_TABLE = 10

AGGREGATE_FUNC_AVG = 1
AGGREGATE_FUNC_COUNT = 2
AGGREGATE_FUNC_MAX = 3
AGGREGATE_FUNC_MIN = 4
AGGREGATE_FUNC_STANDARD_DEVIATION = 5
AGGREGATE_FUNC_SUM = 6
AGGREGATE_FUNC_VARIANCE = 7

AGGREGATE_FUNC_SUFFIX = ['','avg','count','max']




def sql_create_table(user_table, user_table_columns):
	model_class = opengis._create_model(user_table, user_table_columns)
	
	style = no_style()
	
	tables = connection.introspection.table_names()
	seen_models = connection.introspection.installed_models(tables)
	pending_references = {}
	
	sql, references = connection.creation.sql_create_model(model_class, style)
	
	for refto, refs in references.items():
		pending_references.setdefault(refto, []).extend(refs)
		if refto in seen_models:
			sql.extend(connection.creation.sql_for_pending_references(refto, style, pending_references))
	
	sql.extend(connection.creation.sql_for_pending_references(model_class, style, pending_references))
	
	cursor = connection.cursor()
	
	for statement in sql:
		cursor.execute(statement)
	
	transaction.commit_unless_managed()
	
	custom_sql = custom_sql_for_model(model_class, style)
	
	if custom_sql:
		try:
			for sql in custom_sql:
				cursor.execute(sql)
		except Exception, e:
			transaction.rollback_unless_managed()
		else:
			transaction.commit_unless_managed()
	
	# Return physical table name
	return connection.introspection.table_name_converter(model_class._meta.db_table)

def add_new_column(account):
	pass

def delete_column(account):
	pass

def delete_table(account):
	pass
