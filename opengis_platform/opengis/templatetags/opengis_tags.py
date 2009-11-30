from django import template

from opengis.models import *

register = template.Library()

@register.simple_tag
def print_value(data_row, column_name):
	return getattr(data_row, column_name)

# CREATE TABLE
@register.simple_tag
def generate_data_type_list():
	return '<option value="char">Character</option>' \
		+ '<option value="int">Integer</option>' \
		+ '<option value="datetime">Date/Time</option>' \
		+ '<option value="date">Date</option>' \
		+ '<option value="time">Time</option>' \
		+ '<option value="region">Region</option>' \
		+ '<option value="location">Location</option>' \
		+ '<option value="user">User</option>' \
		+ '<option value="mine">My Table</option>' \
		+ '<option value="builtin">Built In Table</option>'

@register.simple_tag
def generate_user_table_list(user_tables):
	html = ""
	for user_table in user_tables:
		html += '<option value="' + str(user_table.id) + '">' + user_table.table_name + "</option>"
	return html

@register.simple_tag
def generate_built_in_table_list():
	html = ""
	for table_key in REGISTERED_BUILT_IN_TABLES.keys():
		table_model = REGISTERED_BUILT_IN_TABLES[table_key]
		html += '<option value="' + table_model.Info.code + '">' + table_model.Info.name + '</option>'
	
	return html
		
		