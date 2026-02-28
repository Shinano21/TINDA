from django import forms
from .models import Supplier, PurchaseProduct
from inventory.models import *

from django.core.exceptions import ValidationError
class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['name', 'contact_info']
        labels = {
            'name': 'Name (Person/Company)',
            'contact_info': 'Supplier Information',
        }
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Name / Company S.A.',
            }),
            'contact_info': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Enter information:\n Address\n Phone\n Category\n Etc',
                'rows': 6,  
            }),
        }
        error_messages = {
            'name': {
                'required': 'The supplier name is mandatory.',
                'max_length': 'The name cannot exceed 100 characters.',
            },
            'contact_info': {
                'required': 'Contact information is mandatory.',
                'max_length': 'Contact information cannot exceed 200 characters.',
            },
        }

class PurchaseForm(forms.ModelForm):
    class Meta:
        model = PurchaseProduct
        fields = ['supplier', 'product','cost','qty']
        labels = {
            'supplier': 'Supplier',
            'product': 'Products',
            'cost': 'Cost',
            'qty':'Quantity',
        }
        widgets = {
            'supplier': forms.Select(attrs={'class': 'form-control'}),
            'product': forms.Select(attrs={'class': 'form-control'}),
            'cost': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter the total amount',
            }),
            'qty': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter the total amount',
            }),
        }
        error_messages = {
            'qty': {
                'required': 'The quantity is mandatory.',
                'invalid': 'Enter a valid quantity.',
            },
            'cost':{
                'required': 'The cost must have 8 decimals.',
                'invalid': 'Enter a valid amount.',
            }
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Order the supplier/product queryset alphabetically
        self.fields['supplier'].queryset = Supplier.objects.all().order_by('name')
        self.fields['product'].queryset = Products.objects.all().order_by('name')
    
