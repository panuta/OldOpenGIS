from django.contrib.auth.models import User

from opengis import OpenGISNotLoginError
from opengis.models import Account

def get_user_auth(request, username):
	if username:
		user = User.objects.get(username=username)
		account = Account.objects.get(user=user)
	else:
		if request.user.is_authenticated():
			user = request.user
			account = Account.objects.get(user=request.user)
		else:
			raise OpenGISNotLoginError
	
	return (user, account, username == request.user.username)

def redirect_to_login(request):
	from django.conf import settings
	login_url = settings.LOGIN_URL

	from django.contrib.auth import REDIRECT_FIELD_NAME
	from django.http import HttpResponseRedirect
	from django.utils.http import urlquote

	path = urlquote(request.get_full_path())
	return HttpResponseRedirect('%s?%s=%s' % (settings.LOGIN_URL, REDIRECT_FIELD_NAME, path))