from django.contrib.gis import admin

import opengis
from opengis.models import *

admin.site.register(Account)
admin.site.register(ThailandRegion, admin.GeoModelAdmin)
admin.site.register(ThailandProvince, admin.GeoModelAdmin)
admin.site.register(UserTable)
admin.site.register(UserTableColumn)
admin.site.register(UserQuery)
admin.site.register(UserQueryDisplayColumn)
admin.site.register(UserQueryFilter)
admin.site.register(UserQueryAggregateColumn)
admin.site.register(UserQueryAggregateColumnGroupBy)

# Register user tables

user_tables = UserTable.objects.all()

for user_table in user_tables:
	user_table_columns = UserTableColumn.objects.filter(table=user_table)
	
	model_class = opengis._create_model(user_table, user_table_columns)
	admin.site.register(model_class, admin.GeoModelAdmin)

