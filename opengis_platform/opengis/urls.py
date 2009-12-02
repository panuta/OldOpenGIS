from django.conf.urls.defaults import *

urlpatterns = patterns('opengis.views',

	url(r'^load_shape/$', 'load_shape'),
	url(r'^simplify_shape/$', 'simplify_shape'),
	
	url(r'^$', 'view_homepage', name="opengis_view_homepage"),
	
	url(r'^my/$', 'view_user_home', name="opengis_view_my_home", kwargs={'username':''}),
	url(r'^my/tables/$', 'list_user_table', name="opengis_list_my_table", kwargs={'username':''}),
	url(r'^my/queries/$', 'list_user_query', name="opengis_list_my_query", kwargs={'username':''}),
	
	url(r'^user/(?P<username>\w+)/$', 'view_user_home', name="opengis_view_user_home"),
	url(r'^user/(?P<username>\w+)/tables/$', 'list_user_table', name="opengis_list_user_table"),
	url(r'^user/(?P<username>\w+)/queries/$', 'list_user_query', name="opengis_list_user_query"),
	
	# ----- User Table ----- #
	url(r'^my/tables/create/$', 'create_user_table', name="opengis_create_my_table"),
	
	url(r'^my/table/(?P<table_name>[^\/]+)/$', 'view_user_table', name="opengis_view_my_table", kwargs={'username':''}),
	url(r'^my/table/(?P<table_name>[^\/]+)/import/$', 'import_user_table', name="opengis_import_my_table"),
	url(r'^my/table/(?P<table_name>[^\/]+)/edit/$', 'edit_user_table', name="opengis_edit_my_table"),
	url(r'^my/table/(?P<table_name>[^\/]+)/delete/$', 'delete_user_table', name="opengis_delete_my_table"),
	
	url(r'^user/(?P<username>\w+)/table/(?P<table_name>[^\/]+)/$', 'view_user_table', name="opengis_view_user_table"),
	
	
	# ----- User Query ----- #
	url(r'^my/queries/create/$', 'create_user_query', name="opengis_create_my_query"),
	
	url(r'^my/query/(?P<query_name>[^\/]+)/$', 'view_user_query', name="opengis_view_my_query", kwargs={'username':''}),
	url(r'^my/query/(?P<query_name>[^\/]+)/visualize/$', 'visualize_user_query', name="opengis_visualize_my_query"),
	url(r'^my/query/(?P<query_name>[^\/]+)/edit/$', 'edit_user_query', name="opengis_edit_my_query"),
	url(r'^my/query/(?P<query_name>[^\/]+)/delete/$', 'delete_user_query', name="opengis_delete_my_query"),
	
	url(r'^user/(?P<username>\w+)/query/(?P<query_name>[^\/]+)/$', 'view_user_query', name="opengis_view_user_query"),
	url(r'^user/(?P<username>\w+)/query/(?P<query_name>[^\/]+)/visualize/$', 'visualize_user_query', name="opengis_visualize_user_query"),
	
	# Internal Ajax Call #
	url(r'^ajax/internal/tables/list/$', 'ajax_list_user_table', name="opengis_ajax_list_user_table"),
	
	
	
	
	
	
	url(r'^ajax/internal/get_tables_for_query_builder/$', 'ajax_get_tables_for_query_builder', name="opengis_ajax_get_tables_for_query_builder"),
	url(r'^ajax/internal/save_building_query/$', 'ajax_save_building_query', name="opengis_ajax_save_building_query"),
	
	
	
	
	
	# url(r'^user/(?P<account_username>\w+)/table/(?P<table_name>\w+)/visualize/$', 'get_user_table_visualize', name="opengis_get_user_table_visualize"),
)

# urlpatterns += patterns('',)
