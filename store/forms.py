from django import forms
from .models import Employee

class EmployeeForm(forms.ModelForm):
    def clean_password(self):
        password = self.cleaned_data.get('password')
        return password if password else ''

    def save(self, commit=True):
        instance = super().save(commit=False)
        if password := self.cleaned_data.get('password'):
            from django.contrib.auth.hashers import make_password
            instance.password = make_password(password)
        if commit:
            instance.save()
        return instance
    class Meta:
        model = Employee
        fields = ['emp_name', 'surname', 'tel', 'position', 'password']
        labels = {
            'emp_name': 'ຊື່ພະນັກງານ',
            'surname': 'ນາມສະກຸນ',
            'tel': 'ເບີໂທລະສັບ',
            'position': 'ຕຳແໜ່ງ',
            'password': 'ລະຫັດຜ່ານ (Password)',
        }
        widgets = {
            'emp_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ປ້ອນຊື່...'}),
            'surname': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ປ້ອນນາມສະກຸນ...'}),
            'tel': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ປ້ອນເບີໂທ...'}),
            'position': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ປ້ອນຕຳແໜ່ງ...'}),
            'password': forms.PasswordInput(render_value=True, attrs={'class': 'form-control', 'placeholder': 'ປ້ອນລະຫັດຜ່ານ...'}),
        }