from django.test import TestCase

from django.contrib.auth.models import User
from opengis.models import *

class UserQueryTest(TestCase):
	
	fixtures = [
		'thailand_province.json',
		'thailand_region.json',
		'user_query_case1.json',
		]
	
	def setUp(self):
		# create tester user
		user = User.objects.create_user('query_tester', 'user_query_tester@example.com', 'password')
		user.is_staff = True
		user.save()
		
		Account.objects.create(user=user)
	
	def test_case1(self):
		"""
		Test
		- Query from built in table, no column hierarchy
		- Result limitation
		- Display column with custom display name
		- Filter 'equal'
		"""
		
		self.client.login(username='query_tester', password='password')
		
		response = self.client.get('/my/tables/query_exp/user_query_case1/')
		self.failUnlessEqual(response.content, '{"query":"user_query_case1","columns":"ID","Name in English","values":[[1,"Bangkok"]]}')
		