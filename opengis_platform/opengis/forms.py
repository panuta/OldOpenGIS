from django import forms

class CreateTableForm(forms.Form):
	table_name			= forms.CharField()
	description			= forms.CharField(required=False, widget=forms.Textarea())
	tags				= forms.CharField(required=False)
	share_level			= forms.ChoiceField(choices=(('9','Public'),('0','Private'),), required=False)

class ImportDataToTableForm(forms.Form):
	source_type			= forms.ChoiceField(choices=(('1','CSV'),), required=False)
	file				= forms.FileField()
