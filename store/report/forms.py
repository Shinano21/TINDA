from django import forms
from pos.models import Sales
from datetime import datetime
from django import forms

from purchase.models import *
MONTH_NAMES = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
]


MONTH_CHOICES = [(str(i), month) for i, month in enumerate(MONTH_NAMES, 1)]


DAYS_OF_WEEK = {
    'Monday': 'Monday',
    'Tuesday': 'Tuesday',
    'Wednesday': 'Wednesday',
    'Thursday': 'Thursday',
    'Friday': 'Friday',
    'Saturday': 'Saturday',
    'Sunday': 'Sunday'
}

class SalesReportForm(forms.Form):
    start_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    customer = forms.CharField(max_length=100, required=False)


class YearMonthForm(forms.Form):
    year = forms.IntegerField(label="Year", min_value=1900, max_value=2100)
    month = forms.ChoiceField(label="Month", choices=MONTH_CHOICES)


class YearForm(forms.Form):
    year = forms.IntegerField(label="Year", min_value=1900, max_value=2100)


class DayForm(forms.Form):
    year = forms.IntegerField(label="Year", min_value=1900, max_value=2100)
    month = forms.ChoiceField(label="Month", choices=MONTH_CHOICES)
    day = forms.IntegerField(label="Day", min_value=1, max_value=31)


class DateRangeForm(forms.Form):
    start_date = forms.DateField(label="Date from", widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(label="Date to", widget=forms.DateInput(attrs={'type': 'date'}))


class ReportForm(forms.Form):
    pass

class MonthReportForm(forms.Form):
    year = forms.IntegerField(label='Year', min_value=1900, max_value=datetime.now().year)
    month = forms.IntegerField(label='Month', min_value=1, max_value=12)

class DayReportForm(forms.Form):
    year = forms.IntegerField(label='Year', min_value=1900, max_value=datetime.now().year)
    month = forms.IntegerField(label='Month', min_value=1, max_value=12)
    day = forms.IntegerField(label='Day', min_value=1, max_value=31)

class PurchaseReportForm(forms.Form):
    start_date = forms.DateField(required=False, widget=forms.TextInput(attrs={'type': 'date'}))
    end_date = forms.DateField(required=False, widget=forms.TextInput(attrs={'type': 'date'}))
    supplier = forms.ModelChoiceField(queryset=Supplier.objects.all(), required=False)


class YearReportForm(forms.Form):
    current_year = datetime.now().year
    YEAR_CHOICES = [(year, year) for year in range(current_year - 10, current_year + 1)]

    year = forms.ChoiceField(choices=YEAR_CHOICES, required=True, label="Select Year", widget=forms.Select)

class MonthYearReportForm(forms.Form):
    year = forms.IntegerField(min_value=2000, max_value=timezone.now().year, label='Year')
    month = forms.IntegerField(min_value=1, max_value=12, label='Month')

class DayMonthYearReportForm(forms.Form):
    year = forms.IntegerField(min_value=2000, max_value=timezone.now().year, label='Year')
    month = forms.IntegerField(min_value=1, max_value=12, label='Month')
    day = forms.IntegerField(min_value=1, max_value=31, label='Day')  # Note: Does not validate specific days for each month

class DayTramoForm(forms.Form):
    start_year = forms.IntegerField(label='Start Year', min_value=2023)
    start_month = forms.ChoiceField(label='Start Month', choices=[
        ('', 'Month'),
        (1, 'January'),
        (2, 'February'),
        (3, 'March'),
        (4, 'April'),
        (5, 'May'),
        (6, 'June'),
        (7, 'July'),
        (8, 'August'),
        (9, 'September'),
        (10, 'October'),
        (11, 'November'),
        (12, 'December'),
    ])
    start_day = forms.IntegerField(label='Start Day', min_value=1, max_value=31)

    end_year = forms.IntegerField(label='End Year', min_value=2023)
    end_month = forms.ChoiceField(label='End Month', choices=[
        ('', 'Month'),
        (1, 'January'),
        (2, 'February'),
        (3, 'March'),
        (4, 'April'),
        (5, 'May'),
        (6, 'June'),
        (7, 'July'),
        (8, 'August'),
        (9, 'September'),
        (10, 'October'),
        (11, 'November'),
        (12, 'December'),
    ])
    end_day = forms.IntegerField(label='End Day', min_value=1, max_value=31)
