from django.conf.urls.defaults import *

urlpatterns = patterns('opengis.views',

	# url(r'^load_shape/$', 'load_shape'),
	# url(r'^simplify_shape/$', 'simplify_shape'),
	
	url(r'^$', 'view_homepage', name="opengis_view_homepage"),
	
	url(r'^my/$', 'view_user_home', name="opengis_view_my_home"),
	
	# User Table
	url(r'^my/tables/$', 'list_user_table', name="opengis_list_my_table"),
	url(r'^my/tables/create/$', 'create_user_table', name="opengis_create_my_table"),
	
	url(r'^my/table/(?P<table_name>\w+)/$', 'view_user_table', name="opengis_view_my_table"),
	url(r'^my/table/(?P<table_name>\w+)/add/$', 'input_user_table', name="opengis_input_my_table"),
	
	url(r'^my/table/(?P<table_name>\w+)/import/$', 'import_user_table', name="opengis_import_my_table"),
	url(r'^my/table/(?P<table_name>\w+)/json/$', 'get_user_table_json', name="opengis_get_my_table_json"),
	
	url(r'^my/tables/query/(?P<query_name>\w+)/$', 'query_user_table', name="opengis_query_my_table", kwargs={'username':''}),
	
	url(r'^user/(?P<username>\w+)/tables/query/(?P<query_name>\w+)/$', 'query_user_table', name="opengis_query_user_table"),
	
	# Query
	url(r'^my/queries/$', 'list_user_query', name="opengis_list_my_query"),
	
	url(r'^my/query/(?P<query_name>\w+)/$', 'view_user_query', name="opengis_view_my_query"),
	
	
	
	url(r'^my/tables/query-builder/$', 'build_user_table_query', name="opengis_build_my_query"),
	
	url(r'^ajax/internal/get_tables_for_query_builder/$', 'ajax_get_tables_for_query_builder', name="opengis_ajax_get_tables_for_query_builder"),
	url(r'^ajax/internal/save_building_query/$', 'ajax_save_building_query', name="opengis_ajax_save_building_query"),
	
	
	
	
	
	# url(r'^user/(?P<account_username>\w+)/table/(?P<table_name>\w+)/visualize/$', 'get_user_table_visualize', name="opengis_get_user_table_visualize"),
)
