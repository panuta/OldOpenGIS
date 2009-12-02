
# from http://www.djangosnippets.org/snippets/650/
from django.conf import settings
from django.http import HttpResponseServerError

class AJAXSimpleExceptionResponse:
    def process_exception(self, request, exception):
        if settings.DEBUG:
            if request.is_ajax():
                import sys, traceback
                (exc_type, exc_info, tb) = sys.exc_info()
                response = "%s\n" % exc_type.__name__
                response += "%s\n\n" % exc_info
                response += "TRACEBACK:\n"    
                for tb in traceback.format_tb(tb):
                    response += "%s\n" % tb
                return HttpResponseServerError(response)

from opengis import errors
from opengis.shortcuts import redirect_to_login

class OpenGISExceptionMiddleware:
	def process_exception(self, request, exception):
		if type(exception).__name__ == type(errors.OpenGISNotLoginError()).__name__: # Have no idea why isinstance is always return False here, use name comparison instead
			return redirect_to_login(request)
