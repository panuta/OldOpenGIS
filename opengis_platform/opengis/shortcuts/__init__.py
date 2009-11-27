from opengis import errors
from opengis.models import Account

def check_user_auth(request):
	username = request.REQUEST.get('username')
	
	if username:
		# TODO Check authorization
		user = User.objects.get(username=username)
		account = Account.objects.get(user=user)
	else:
		if request.user.is_authenticated():
			user = request.user
			account = Account.objects.get(user=request.user)
		else:
			raise errors.OpenGISNotLoginError()
	
	return (user, account)

def redirect_to_login(request):
	from django.conf import settings
	login_url = settings.LOGIN_URL

	from django.contrib.auth import REDIRECT_FIELD_NAME
	from django.http import HttpResponseRedirect
	from django.utils.http import urlquote

	path = urlquote(request.get_full_path())
	return HttpResponseRedirect('%s?%s=%s' % (settings.LOGIN_URL, REDIRECT_FIELD_NAME, path))