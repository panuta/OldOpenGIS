# Response Code
API_RESPONSE_SUCCESS = 'success'

API_RESPONSE_ERROR = 'error'
API_RESPONSE_ERROR_LIST = 'errorlist'

API_RESPONSE_GETONLY = 'get-only'
API_RESPONSE_POSTONLY = 'post-only'
API_RESPONSE_RESOURCE_NOT_FOUND = "resource-not-found"


from django.http import HttpResponse
from django.utils import simplejson

class APIResponse(HttpResponse):
	def __init__(self, response_code, response_meta=dict(), result=None, str_result=""):
		
		meta_json = ''
		if response_meta: meta_json = ',response_meta:' + simplejson.dumps(response_meta)
		
		result_json = ''
		if result: result_json = ',result:' + simplejson.dumps(result)
		
		if str_result: str_result = ',result:' + str_result
		
		HttpResponse.__init__(self, '{response:"' + response_code + '"' + meta_json + result_json + str_result + '}')

# Exception Class
class TableColumnException(Exception):
	def __init__(self, error_code):
		self.error_code = error_code

class MissingColumnName(Exception):
	pass
	
class InvalidColumnName(Exception):
	def __init__(self, column_name):
		self.column_name = column_name

class InvalidColumnDataType(Exception):
	def __init__(self, column_name):
		self.column_name = column_name

class MissingColumnArgument(Exception):
	def __init__(self, column_name):
		self.column_name = column_name

