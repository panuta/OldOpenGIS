from django import forms
from django.forms.util import ErrorList

from opengis.models import Account, UserTable

class ModifyTableForm(forms.Form):
	table_name			= forms.CharField()
	description			= forms.CharField(required=False, widget=forms.Textarea())
	tags				= forms.CharField(required=False)
	share_level			= forms.ChoiceField(choices=(('0','Private'),('9','Public'),), required=False)
	display_column		= forms.CharField(widget=forms.HiddenInput())
	existing_table_id	= forms.CharField(required=False, widget=forms.HiddenInput())
	
	def __init__(self, request, *args, **kwargs):
		self.request = request
		super(ModifyTableForm, self).__init__(*args, **kwargs)
	
	def clean(self):
		table_name = self.cleaned_data['table_name']
		account = Account.objects.get(user=self.request.user)
		
		data_object = UserTable.objects.filter(account=account, table_name=table_name)
		
		exclude_table_id = self.cleaned_data['existing_table_id']
		if exclude_table_id:
			data_object = data_object.exclude(pk=exclude_table_id)
		
		if data_object.count():
			msg = u"This table name is already existed."
			self._errors["table_name"] = ErrorList([msg])
			del self.cleaned_data["table_name"]
		
		return self.cleaned_data


class ImportDataToTableForm(forms.Form):
	source_type			= forms.ChoiceField(choices=(('1','CSV'),), required=False)
	file				= forms.FileField()

class CreateQueryForm(forms.Form):
	query_name			= forms.CharField()
	description			= forms.CharField(required=False, widget=forms.Textarea())
