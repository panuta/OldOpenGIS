AJAX_NO_USER = "no-user"
AJAX_NOT_AUTHENTICATED = "not-authenticated"

AJAX_RESOURCE_NOT_FOUND = "not-found"


def return_resource_not_found(table_name, record_id):
	return '{"response":"' + AJAX_RESOURCE_NOT_FOUND + '","response_meta":{"table":"' + table_name + '","id":"' + record_id + '"}}'

class OpenGISNotLoginError(Exception):
	def __init__(self):
		pass

