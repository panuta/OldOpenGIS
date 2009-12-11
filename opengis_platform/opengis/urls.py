from django.conf.urls.defaults import *

urlpatterns = patterns('opengis.views',

	url(r'^load_shape/$', 'load_shape'),
	url(r'^simplify_shape/$', 'simplify_shape'),
	
	url(r'^$', 'view_homepage', name="opengis_view_homepage"),
	
	url(r'^my/$', 'view_user_home', name="opengis_view_my_home", kwargs={'username':''}),
	url(r'^my/tables/$', 'list_user_table', name="opengis_list_my_table", kwargs={'username':''}),
	url(r'^my/queries/$', 'list_user_query', name="opengis_list_my_query", kwargs={'username':''}),
	
	url(r'^user/(?P<username>\w+)/$', 'view_user_home', name="opengis_view_user_home"),
	
	# ----- User Table ----- #
	url(r'^my/tables/create/$', 'create_user_table', name="opengis_create_my_table"),
	url(r'^my/tables/search/$', 'search_public_table', name="opengis_search_public_table"),
	
	url(r'^my/table/(?P<table_name>[^\/]+)/$', 'view_user_table', name="opengis_view_my_table", kwargs={'username':''}),
	url(r'^my/table/(?P<table_name>[^\/]+)/import/$', 'import_user_table', name="opengis_import_my_table"),
	url(r'^my/table/(?P<table_name>[^\/]+)/edit/$', 'edit_user_table', name="opengis_edit_my_table"),
	
	url(r'^user/(?P<username>\w+)/table/(?P<table_name>[^\/]+)/$', 'view_user_table', name="opengis_view_user_table"),
	
	
	# ----- User Query ----- #
	url(r'^my/queries/create/$', 'create_user_query', name="opengis_create_my_query"),
	
	url(r'^my/query/(?P<query_name>[^\/]+)/$', 'view_user_query', name="opengis_view_my_query", kwargs={'username':''}),
	url(r'^my/query/(?P<query_name>[^\/]+)/visualize/$', 'visualize_user_query', name="opengis_visualize_my_query"),
	url(r'^my/query/(?P<query_name>[^\/]+)/edit/$', 'edit_user_query', name="opengis_edit_my_query"),
	
	url(r'^user/(?P<username>\w+)/query/(?P<query_name>[^\/]+)/$', 'view_user_query', name="opengis_view_user_query"),
	url(r'^user/(?P<username>\w+)/query/(?P<query_name>[^\/]+)/visualize/$', 'visualize_user_query', name="opengis_visualize_user_query"),
	
)
