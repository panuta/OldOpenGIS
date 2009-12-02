AJAX_SUCCESS = "success"

AJAX_NO_USER = "no-user"
AJAX_NOT_AUTHENTICATED = "not-authenticated"
AJAX_ACCESS_DENIED = "access-denied"

AJAX_RESOURCE_NOT_FOUND = "not-found"


def return_resource_not_found(table_name, record_id):
	return '{"response":"' + AJAX_RESOURCE_NOT_FOUND + '","response_meta":{"table":"' + table_name + '","id":"' + record_id + '"}}'

class OpenGISNotLoginError(Exception):
	pass

from django.utils import simplejson

# Return format: '{"response":"[response code]", "response_meta":{[dict]}, }'
def format_ajax_return(response_code, *args):
	try:
		response_meta = args[0]
	except IndexError:
		response_meta = ""
		response_json = ""
	else:
		try:
			response_json = args[1]
		except IndexError:
			response_json = ""
	
	response_meta_json = ""
	if type(response_meta).__name__ == 'dict':
		for key in response_meta.keys():
			if response_meta_json: response_meta_json += ","
			response_meta_json += '"' + key + '":' + simplejson.dumps(response_meta[key])
		
		if response_meta_json: response_meta_json = ',{' + response_meta_json + '}'
	
	else:
		response_meta_json = ',' + response_meta_json
	
	if response_json: response_json = ',' + response_json
	
	return '{"response":"' + response_code + '"' + response_meta_json + response_json + '}'
	