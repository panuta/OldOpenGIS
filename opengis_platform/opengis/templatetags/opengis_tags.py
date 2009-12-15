from django import template
from django.core.urlresolvers import reverse
from django.template import Node


from opengis.models import *

register = template.Library()

# To choose between 2 urls whether it's on user's page or another user's page
class MyURLNode(Node):
	def __init__(self, my_url_name, user_url_name, params):
		self.my_url_name = my_url_name
		self.user_url_name = user_url_name
		
		self.params = list()
		for param in params:
			self.params.append(template.Variable(param))
	
	def render(self, context):
		user = context['user']
		account = context['account']
		
		url_args = list()
		for param in self.params:
			url_args.append(param.resolve(context))
		
		if user and account and user.username == account.user.username:
			return reverse(self.my_url_name, args=url_args)
		else:
			url_args.insert(0, account.user.username)
			return reverse(self.user_url_name, args=url_args)

@register.tag(name="my_url")
def my_url(parser, token):
	try:
		tag_name, my_url_name, user_url_name, params = token.split_contents()
	except ValueError:
		try:
			tag_name, my_url_name, user_url_name = token.split_contents()
		except ValueError:
			raise template.TemplateSyntaxError, "%r tag requires three or four arguments" % token.contents[0]
		else:
			return MyURLNode(my_url_name, user_url_name, list())
	else:
		params = params.split(":")
		return MyURLNode(my_url_name, user_url_name, params)

@register.simple_tag
def print_value(data_row, column_info):
	
	if column_info.data_type == sql.TYPE_USER_TABLE:
		obj = getattr(data_row, column_info.physical_column_name)
		display_column = UserTable.objects.get(pk=column_info.related_table).display_column
		return getattr(obj, display_column)
		
	else:
		return getattr(data_row, column_info.physical_column_name)

@register.simple_tag
def print_share_level_html(MEDIA_URL, level_number):
	if level_number == 9: return '<img src="' + MEDIA_URL + '/images/share_public.png" title="Public Table"/> Public Table'
	return 'Private Table'

@register.simple_tag
def print_datetime(datetime):
	return "%d/%d/%d %02d:%02d" % (datetime.day,datetime.month,datetime.year,datetime.hour,datetime.minute)

@register.simple_tag
def print_query_column_name(column):
	return column['name']

@register.simple_tag
def print_column_data_type(data_type):
	if data_type == sql.TYPE_CHARACTER: return "Character"
	elif data_type == sql.TYPE_NUMBER: return "Number"
	elif data_type == sql.TYPE_DATETIME: return "Date/Time"
	elif data_type == sql.TYPE_DATE: return "Date"
	elif data_type == sql.TYPE_TIME: return "Time"
	elif data_type == sql.TYPE_REGION: return "Region"
	elif data_type == sql.TYPE_LOCATION: return "Location"
	elif data_type == sql.TYPE_USER_TABLE: return "Table"
	elif data_type == sql.TYPE_BUILT_IN_TABLE: return "Built-in Table"
	return "Unknown"

# CREATE TABLE
@register.simple_tag
def generate_data_type_list(type_value):
	if not type_value:
		return '<option value="char">Character</option>' \
			+ '<option value="number">Number</option>' \
			+ '<option value="datetime">Date/Time</option>' \
			+ '<option value="region">Region</option>' \
			+ '<option value="location">Location</option>' \
			+ '<option value="builtin">Other data</option>' \
			+ '<option value="table">Table</option>'
	else:
		html = '<option value="char" ' + ('selected="selected"' if type_value==sql.TYPE_CHARACTER else '') + '>Character</option>'
		html += '<option value="number" ' + ('selected="selected"' if type_value==sql.TYPE_NUMBER else '') + '>Number</option>'
		html += '<option value="datetime" ' + ('selected="selected"' if type_value in (sql.TYPE_DATETIME,sql.TYPE_DATE,sql.TYPE_TIME) else '') + '>Date/Time</option>'
		html += '<option value="region" ' + ('selected="selected"' if type_value==sql.TYPE_REGION else '') + '>Region</option>'
		html += '<option value="location" ' + ('selected="selected"' if type_value==sql.TYPE_LOCATION else '') + '>Location</option>'
		html += '<option value="builtin" ' + ('selected="selected"' if type_value==sql.TYPE_BUILT_IN_TABLE else '') + '>Other data</option>'
		html += '<option value="table" ' + ('selected="selected"' if type_value==sql.TYPE_USER_TABLE else '') + '>Table</option>'
		
		return html

@register.simple_tag
def generate_user_table_list(user_tables):
	html = ""
	for user_table in user_tables:
		html += '<option value="' + str(user_table.id) + '">' + user_table.table_name + "</option>"
	return html


	
		