from django.conf import settings
from django.contrib.auth.models import User

from opengis.models import Account
from opengis.models import UserTable
from opengis.models import REGISTERED_BUILT_IN_TABLES

def after_syncdb(sender, **kwargs):
	
	# Create system user
	try:
		user = User.objects.get(username=settings.SYSTEM_USERNAME)
		
	except User.DoesNotExist:
		user = User.objects.create_user(settings.SYSTEM_USERNAME, settings.SYSTEM_EMAIL_ADDRESS, settings.SYSTEM_PASSWORD)
	
		user.is_staff = True
		user.is_superuser = True
		user.save()
	
	# Create system account
	try:
		account = Account.objects.get(user=user)
		
	except Account.DoesNotExist:
		print "create account"
		account = Account.objects.create(user=user)
	
	# Create Built-in tables
	installed_models = dict()
	for table_class in REGISTERED_BUILT_IN_TABLES:
		try:
			UserTable.objects.get(account=account, table_class_name=table_class.CLASS_NAME)
		except UserTable.DoesNotExist:
			installed_models[table_class.CLASS_NAME] = table_class().initialize(account, installed_models)

# Signal after syncdb
from django.db.models.signals import post_syncdb
post_syncdb.connect(after_syncdb)

