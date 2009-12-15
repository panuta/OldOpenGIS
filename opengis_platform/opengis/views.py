import datetime, time
import csv

from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render_to_response, redirect
from django.template import RequestContext
from django.utils import simplejson
from django.utils.translation import ugettext as _

import opengis
from opengis import constants, sql, query, utilities
from opengis.models import *
from opengis.forms import *
from opengis.shortcuts import *
from opengis import views_api as api

def registered_user_callback(sender, **kwargs):
	# Create a new Account model instance
	Account.objects.create(user=kwargs['user'])

##############################
# HOMEPAGE
##############################
from registration.forms import RegistrationForm
from django.contrib.auth.forms import AuthenticationForm

def view_homepage(request):
	if request.user.is_authenticated(): return redirect(settings.LOGIN_REDIRECT_URL)

	if request.method == "POST":
		submit_type = request.POST.get('submit_button')

		if submit_type == "register":
			from registration.views import register
			return register(request, 'registration.backends.default.DefaultBackend')

		elif submit_type == "login":
			from django.contrib.auth.views import login
			return login(request)

		else:
			return redirect("/")

	else:
		register_form = RegistrationForm(auto_id=False)
		login_form = AuthenticationForm(auto_id=False)

	return render_to_response(settings.OPENGIS_TEMPLATE_PREFIX + "homepage.html", {'register_form':register_form, 'login_form':login_form}, context_instance=RequestContext(request))

##############################
# PROFILE
##############################
def view_user_home(request, username):
	(user, account, is_owner) = get_user_auth(request, username)
	if is_owner: return redirect(reverse("opengis_view_my_home"))
	
	if user == request.user:
		user_tables = UserTable.objects.filter(account=account).order_by('-created')[:5]
		user_queries = UserQuery.objects.filter(account=account).order_by('-created')[:5]
	else:
		user_tables = UserTable.objects.filter(account=account, share_level=9).order_by('-created')
		user_queries = UserQuery.objects.filter(account=account).order_by('-created')
	
	for table in user_tables: table.columns = [column.column_name for column in UserTableColumn.objects.filter(table=table).order_by('created')]
	for table in user_tables: table.tags = [tag.tag_name for tag in UserTableTag.objects.filter(table=table)]
	
	return render_to_response(settings.OPENGIS_TEMPLATE_PREFIX + "user_home.html", {'account':account, 'user_tables':user_tables, 'user_queries':user_queries}, context_instance=RequestContext(request))

##############################
# USER TABLE
##############################
def list_user_table(request, username):
	(user, account, is_owner) = get_user_auth(request, username)
	if is_owner: return redirect(reverse("opengis_list_my_table"))
	
	user_tables = UserTable.objects.filter(account=account)
	for table in user_tables: table.columns = [column.column_name for column in UserTableColumn.objects.filter(table=table).order_by('created')]
	for table in user_tables: table.tags = [tag.tag_name for tag in UserTableTag.objects.filter(table=table)]
	
	return render_to_response(settings.OPENGIS_TEMPLATE_PREFIX + "table_list.html", {'account':account, 'user_tables':user_tables}, context_instance=RequestContext(request))

def view_user_table(request, username, table_name):
	account = Account.objects.get(user=request.user)
	
	user_table = get_object_or_404(UserTable, account=account, table_name=table_name)
	user_table.columns = UserTableColumn.objects.filter(table=user_table).order_by('created')
	user_table.tags = UserTableTag.objects.filter(table=user_table)
	
	table_model = opengis.create_model(user_table)
	table_data = table_model.objects.all()

	return render_to_response(settings.OPENGIS_TEMPLATE_PREFIX + "table_view.html", {'account':account, 'user_table':user_table, 'table_data':table_data}, context_instance=RequestContext(request))

@login_required
def create_user_table(request):
	account = Account.objects.get(user=request.user)
	
	return render_to_response(settings.OPENGIS_TEMPLATE_PREFIX + "table_create.html", {'account':account}, context_instance=RequestContext(request))

@login_required
def edit_user_table(request, table_name):
	account = Account.objects.get(user=request.user)
	
	user_table = get_object_or_404(UserTable, account=account, table_name=table_name)
	user_table.columns = UserTableColumn.objects.filter(table=user_table).order_by('created')
	
	user_table.tags_text = ','.join([tag.tag_name for tag in UserTableTag.objects.filter(table=user_table)])
		
	return render_to_response(settings.OPENGIS_TEMPLATE_PREFIX + "table_edit.html", {'account':account, 'user_table':user_table}, context_instance=RequestContext(request))

@login_required
def import_user_table(request, table_name):
	account = Account.objects.get(user=request.user)

	user_table = get_object_or_404(UserTable, account=account, table_name=table_name)

	if request.method == "POST":
		form = ImportDataToTableForm(request.POST, request.FILES)
		if form.is_valid():
			api.import_table(user_table, account, request)

			return redirect(reverse('opengis_import_my_table', args=[table_name]))

	else:
		form = ImportDataToTableForm(auto_id=False)

	return render_to_response(settings.OPENGIS_TEMPLATE_PREFIX + "table_import.html", {'account':account, 'user_table':user_table, 'form':form}, context_instance=RequestContext(request))

def search_public_table(request):
	return render_to_response(settings.OPENGIS_TEMPLATE_PREFIX + "table_search.html", {}, context_instance=RequestContext(request))

##############################
# TABLE QUERY
##############################
def list_user_query(request, username):
	(user, account, is_owner) = get_user_auth(request, username)
	if is_owner: return redirect(reverse("opengis_list_my_query"))
	
	user_queries = UserQuery.objects.filter(account=account)
	return render_to_response(settings.OPENGIS_TEMPLATE_PREFIX + "query_list.html", {'account':account, 'user_queries':user_queries}, context_instance=RequestContext(request))

def view_user_query(request, username, query_name):
	(user, account, is_owner) = get_user_auth(request, username)
	if is_owner: return redirect(reverse("opengis_view_my_query"))
	
	user_query = get_object_or_404(UserQuery, account=account, query_name=query_name)
	query_result = api.execute_query(user_query, request.GET)
	
	return render_to_response(settings.OPENGIS_TEMPLATE_PREFIX + "query_view.html", {'account':account, 'user_query':user_query, 'query_result':query_result}, context_instance=RequestContext(request))

def visualize_user_query(request, username, query_name):
	(user, account, is_owner) = get_user_auth(request, username)
	if is_owner: return redirect(reverse("opengis_visualize_my_query"))
	
	return render_to_response(settings.OPENGIS_TEMPLATE_PREFIX + "query_visualize.html", {'account':account, }, context_instance=RequestContext(request))

@login_required
def create_user_query(request):
	account = Account.objects.get(user=request.user)
	return render_to_response(settings.OPENGIS_TEMPLATE_PREFIX + "query_create.html", {'account':account}, context_instance=RequestContext(request))

@login_required
def edit_user_query(request, query_name):
	account = Account.objects.get(user=request.user)
	return render_to_response(settings.OPENGIS_TEMPLATE_PREFIX + "query_edit.html", {'account':account}, context_instance=RequestContext(request))







def simplify_shape(request):
	for province in ThailandProvince.objects.all():
		
		from django.contrib.gis.geos import GEOSGeometry
		
		try:
			province.region_simple = GEOSGeometry(province.region.simplify(0.03, True).wkt)
			province.save()
		except:
			province.region_simple = GEOSGeometry(province.region.simplify(0.03, True).wkt.replace('POLYGON ', 'MULTIPOLYGON (') + ')')
			province.save()
	
	return HttpResponse('')

def load_shape(request):
	from django.contrib.gis.utils.layermapping import LayerMapping
	from django.contrib.gis.gdal import DataSource
	from opengis.models import ThailandProvince

	ds = DataSource('/Users/apple/Projects/OpenGIS/OpenGIS/opengis_platform/files/shape/thailand_province/changwat_region_Project.shp')

	mapping = {
		'geocode' : 'CODE',
	    'name_th' : 'TNAME',
	    'name' : 'ENAME',
	    'region' : 'POLYGON',
	}

	lm = LayerMapping(ThailandProvince, ds, mapping, encoding='tis-620')
	lm.save(verbose=True)
	
	return HttpResponse('')

def get_user_table_json(request, table_name):
	account = Account.objects.get(user=request.user)
	
	user_table = get_object_or_404(UserTable, table_name=table_name)
	user_table.columns = UserTableColumn.objects.filter(table=user_table)
	
	model_class = opengis.create_model(user_table)
	data = model_class.objects.all()
	
	result = list()
	for datum in model_class.objects.all():
		row_dict = dict()
		
		for index, column in enumerate(user_table.columns):
			row_dict[column.column_name] = getattr(datum, column.column_name)
		
		result.append(row_dict)
	
	return HttpResponse(simplejson.dumps(result), content_type='text/plain; charset=UTF-8')

def get_user_table_visualize(request, table_name):
	account = Account.objects.get(user=request.user)
	return render_to_response(settings.OPENGIS_TEMPLATE_PREFIX + "visualization/flu_home.html", {'account':account, 'table_name':table_name}, context_instance=RequestContext(request))
