from django import forms

class ImportDataToTableForm(forms.Form):
	source_type			= forms.ChoiceField(choices=(('1','CSV'),), required=False)
	file				= forms.FileField()
