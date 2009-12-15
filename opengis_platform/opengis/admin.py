from django.contrib.gis import admin

import opengis
from opengis.models import *

admin.site.register(Account)
admin.site.register(UserTable)
admin.site.register(UserTableColumn)
admin.site.register(UserQuery)
admin.site.register(UserQueryDisplayColumn)
admin.site.register(UserQueryFilter)
admin.site.register(UserQueryAggregateColumn)
admin.site.register(UserQueryGroupByColumn)

# Register user tables

user_tables = UserTable.objects.all()

for user_table in user_tables:
	model_class = opengis.create_model(user_table)
	admin.site.register(model_class, admin.GeoModelAdmin)

