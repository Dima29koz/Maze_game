def test_submitted_and_valid(self):
    data = dict(username='Tester', pwd='1', pwd2='1')
    with self.request(method='POST', data=data):
        f = forms.RegistrationForm(request.form)
        self.assertEqual(f.validate_on_submit(), True)

    data = dict(username='Tester', pwd='1', pwd2='2')
    with self.request(method='POST', data=data):
        f = forms.RegistrationForm(request.form)
        self.assertEqual(f.validate_on_submit(), False)
        self.assertEqual(f.errors, {'pwd2': ['Пароли не совпадают']})