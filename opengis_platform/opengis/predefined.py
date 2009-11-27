# When adding a new predefined table, don't forget to add JSON serialization in json.py

from opengis import sql

PREDEFINED_TABLES = {
	'thailand_province':{
		'code':'thailand_province',
		'table_name':'ThailandProvince',
		'name':'Thailand Province',
		'columns':{
			'id':{
				'name':'ID',
				'physical_name':'id',
				'type':sql.TYPE_INTEGER,
				'related_table':'',
			},
			'name':{
				'name':'Name',
				'physical_name':'name',
				'type':sql.TYPE_CHARACTER,
				'related_table':'',
			},
			'name_th':{
				'name':'Name in Thai',
				'physical_name':'name_th',
				'type':sql.TYPE_CHARACTER,
				'related_table':'',
			},
			'region':{
				'name':'Region',
				'physical_name':'region',
				'type':sql.TYPE_REGION,
				'related_table':'',
			},
			'location':{
				'name':'Location',
				'physical_name':'location',
				'type':sql.TYPE_LOCATION,
				'related_table':'',
			},
			'in_region':{
				'name':'In Region',
				'physical_name':'in_region',
				'type':sql.TYPE_PREDEFINED_TABLE,
				'related_table':'thailand_region',
			},
		},
	},
	'thailand_region':{
		'code':'thailand_region',
		'table_name':'ThailandRegion',
		'name':'Thailand Region',
		'columns':{
			'id':{
				'name':'ID',
				'physical_name':'id',
				'type':sql.TYPE_INTEGER,
				'related_table':'',
			},
			'name':{
				'name':'Name',
				'physical_name':'name',
				'type':sql.TYPE_CHARACTER,
				'related_table':'',
			},
			'name_th':{
				'name':'Name in Thai',
				'physical_name':'name_th',
				'type':sql.TYPE_CHARACTER,
				'related_table':'',
			},
			'region':{
				'name':'Region',
				'physical_name':'region',
				'type':sql.TYPE_REGION,
				'related_table':'',
			},
		},
	},
}
