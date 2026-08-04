from django import forms
from django.contrib.auth.hashers import make_password

from .models import Employee, Promotion, Supplier, Product

class EmployeeForm(forms.ModelForm):
    password = forms.CharField(
        required=False,
        label='ລະຫັດຜ່ານ (Password)',
        help_text='ປະໄວ້ຫວ່າງເປົ່າ ຖ້າບໍ່ຕ້ອງການປ່ຽນລະຫັດຜ່ານ',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'ປ້ອນລະຫັດຜ່ານ...'}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._current_password = self.instance.password

    def save(self, commit=True):
        instance = super().save(commit=False)
        new_password = self.cleaned_data.get('password')
        instance.password = make_password(new_password) if new_password else self._current_password
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
        }
        widgets = {
            'emp_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ປ້ອນຊື່...'}),
            'surname': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ປ້ອນນາມສະກຸນ...'}),
            'tel': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ປ້ອນເບີໂທ...'}),
            'position': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ປ້ອນຕຳແໜ່ງ...'}),
        }


class PromotionForm(forms.ModelForm):
    class Meta:
        model = Promotion
        fields = ['code', 'discount_type', 'value', 'start_date', 'end_date', 'active']
        labels = {
            'code': 'ລະຫັດໂປຣໂມຊັ່ນ',
            'discount_type': 'ປະເພດສ່ວນຫຼຸດ',
            'value': 'ມູນຄ່າ',
            'start_date': 'ວັນເລີມ',
            'end_date': 'ວັນສິ້ນສິດ',
            'active': 'ເປີດໃຊ້ງານ'
        }
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ປ້ອນລະຫັດໂປຣໂມຊັ່ນ...'}),
            'discount_type': forms.Select(attrs={'class': 'form-select'}),
            'value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class StockImportForm(forms.Form):
    sup_id = forms.ModelChoiceField(
        queryset=Supplier.objects.all(),
        label='ຜູ້ສະໜອງ',
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label='--- ເລືອກຜູ້ສະໜອງ ---',
        required=False,
    )
    pro_id = forms.ModelChoiceField(
        queryset=Product.objects.all(),
        label='ສິນຄ້າ',
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label='--- ເລືອກສິນຄ້າ ---',
        required=False,
    )
    qty = forms.IntegerField(
        label='ລວງ',
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
        required=False,
    )
    price = forms.DecimalField(
        label='ລາຄາ',
        min_value=0.01,
        decimal_places=2,
        max_digits=12,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        required=False,
    )
    import_file = forms.FileField(
        required=False,
        label='ໄຟລ໌ CSV (Bulk Import)',
        widget=forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': '.csv,text/csv'})
    )

    def clean(self):
        cleaned_data = super().clean()
        import_file = cleaned_data.get('import_file')
        sup_id = cleaned_data.get('sup_id')
        pro_id = cleaned_data.get('pro_id')
        qty = cleaned_data.get('qty')
        price = cleaned_data.get('price')

        if import_file:
            return cleaned_data

        if not sup_id or not pro_id or qty is None or price is None:
            raise forms.ValidationError('ກະລຸນາເລືອກຂໍ້ມູນ ແລະ ປ້ອນຈຳນວນໃຫ້ຄົບຖ້ວນ, ຫຼືອັບໂຫຼດໄຟລ໌ CSV ເພື່ອນຳເຂົ້າຫຼາຍລາຍການ')

        return cleaned_data

    def clean_qty(self):
        qty = self.cleaned_data['qty']
        if qty > 10000:
            raise forms.ValidationError('ຈໍານວນຫຼາຍເກີນໄປ (ສູງສຸດ 10,000)')
        return qty

    def clean_price(self):
        price = self.cleaned_data['price']
        if price > 100000:
            raise forms.ValidationError('ລາຄາເກີນໄປ (ສູງສຸດ 100,000)')
        return price