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

"""
@register.simple_tag
def unicode_url(url_name, params):
	
	from django.utils.encoding import force_unicode, iri_to_uri
	from django.utils.http import urlquote

	table.table_url_name = iri_to_uri(urlquote(table.table_url_name))
	
	return reverse(url_name, args=())
	
	return getattr(data_row, column_name)
"""

@register.simple_tag
def print_value(data_row, column_name):
	return getattr(data_row, column_name)

# CREATE TABLE
@register.simple_tag
def generate_data_type_list():
	return '<option value="char">Character</option>' \
		+ '<option value="number">Number</option>' \
		+ '<option value="datetime">Date/Time</option>' \
		+ '<option value="region">Region</option>' \
		+ '<option value="location">Location</option>' \
		+ '<option value="builtin">Other data</option>' \
		+ '<option value="table">Table</option>'

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
		
		