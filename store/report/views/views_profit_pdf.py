from purchase.models import PurchaseProduct  # Import the PurchaseProduct model
from pos.models import Sales, salesItems
from inventory.models import Products
from report.forms import *
from datetime import datetime
from decimal import Decimal
import io
import uuid

from django.conf import settings
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.views.generic import ListView, View, FormView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm
from django.contrib.auth.models import User
from django.core.mail import send_mail, BadHeaderError
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib import messages
from django.utils import timezone

from xhtml2pdf import pisa

import openpyxl

class ProfitReportView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Sales
    template_name = 'report/profit_report.html'
    context_object_name = 'sales'
    form_class = SalesReportForm
    permission_required = 'report.view_profit' 

    def get_queryset(self):
        queryset = super().get_queryset()
        form = self.form_class(self.request.GET)

        if form.is_valid():
            start_date = form.cleaned_data.get('start_date')
            end_date = form.cleaned_data.get('end_date')

            if start_date:
                queryset = queryset.filter(date_added__gte=start_date)
            if end_date:
                queryset = queryset.filter(date_added__lte=end_date)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sales = self.get_queryset()

        total_income = self.calculate_total_income(sales)
        total_costs = self.calculate_total_costs(sales)

        total_income_decimal = Decimal(total_income) if total_income is not None else Decimal('0')
        total_costs_decimal = Decimal(total_costs) if total_costs is not None else Decimal('0')

        total_profit = total_income_decimal - total_costs_decimal

        context['total_income'] = total_income_decimal
        context['total_costs'] = total_costs_decimal
        context['total_profit'] = total_profit

        sales_data = self.get_sales_data(sales)
        context['sales_data'] = sales_data

        return context

    def calculate_total_income(self, sales_queryset):
        total_income = sales_queryset.aggregate(total=Sum('grand_total'))['total']
        return total_income or Decimal('0')

    def calculate_total_costs(self, sales_queryset):
        total_costs = Decimal('0')
        sales_items = salesItems.objects.filter(sale__in=sales_queryset)

        for item in sales_items:
            purchase_product = PurchaseProduct.objects.filter(product=item.product).first()
            if purchase_product:
                product_cost = purchase_product.cost
                total_costs += product_cost * Decimal(item.qty)

        return total_costs

    def get_sales_data(self, sales_queryset):
        sales_data = []
        for sale in sales_queryset:
            sale_cost = self.calculate_sale_cost(sale)
            sale_profit = Decimal(sale.grand_total) - sale_cost if sale.grand_total is not None else Decimal('0')
            for item in sale.salesitems_set.all():
                purchase_product = PurchaseProduct.objects.filter(product=item.product).first()
                cost_per_unit = Decimal(purchase_product.cost) if purchase_product else Decimal('0')
                qty_bought = sum([pp.qty for pp in PurchaseProduct.objects.filter(product=item.product)])

                # Add sales entry
                sales_data.append({
                    'date_added': sale.date_added,
                    'product_name': item.product.name,
                    'qty_sold': item.qty,
                    'qty_bought': 0,
                    'cost': cost_per_unit,
                    'total_sale': Decimal(item.qty) * Decimal(item.product.price),  # Total sale per product
                    'total_cost': sale_cost,
                    'profit': sale_profit,
                })


                if purchase_product:
                    sales_data.append({
                        'date_added': purchase_product.date_added,
                        'product_name': item.product.name,
                        'qty_sold': 0,
                        'qty_bought': qty_bought,
                        'cost': cost_per_unit,
                        'total_sale': 0,
                        'total_cost': qty_bought * cost_per_unit,
                        'profit': -qty_bought * cost_per_unit,
                    })


        sales_data.sort(key=lambda x: x['date_added'])

        return sales_data

    def calculate_sale_cost(self, sale):
        sale_cost = Decimal('0')
        for item in sale.salesitems_set.all():
            purchase_product = PurchaseProduct.objects.filter(product=item.product).first()
            if purchase_product:
                product_cost = Decimal(purchase_product.cost)
                sale_cost += product_cost * Decimal(item.qty)
        return sale_cost
    


class GeneratePDFProfitView(View):
    def get(self, request, *args, **kwargs):
        form = SalesReportForm(request.GET or None)
        sales_queryset = self.get_queryset(form)

        total_income = self.calculate_total_income(sales_queryset)
        total_costs = self.calculate_total_costs(sales_queryset)
        total_income_decimal = Decimal(total_income)
        total_costs_decimal = Decimal(total_costs)
        total_profit = total_income_decimal - total_costs_decimal


        sales_data, total_utilities = self.get_sales_data_and_utilities(sales_queryset)

        current_date = datetime.now()
        username = request.user.username
        unique_key = str(uuid.uuid4())

        context = {
            'sales_data': sales_data,
            'total_income': total_income,
            'total_costs': total_costs,
            'total_profit': total_profit,
            'total_utilities': total_utilities,
            'current_date': current_date,
            'username': username,
            'unique_key': unique_key,
        }

        html_string = render_to_string('report/profit_pdf.html', context)

        pdf_file = self.render_pdf(html_string)
        response = HttpResponse(pdf_file, content_type='application/pdf')
<<<<<<< HEAD
        response['Content-Disposition'] = f'attachment; filename="profit_report_general_{current_date.strftime("%Y%m%d_%H%M%S")}.pdf"'
=======
        response['Content-Disposition'] = f'attachment; filename="general_profit_report_{current_date.strftime("%Y%m%d_%H%M%S")}.pdf"'
>>>>>>> 34cc06a43306d90c1ec90c9b7ceefa3e8a99c7ea

        return response

    def get_queryset(self, form):
        queryset = Sales.objects.all()

        if form.is_valid():
            start_date = form.cleaned_data.get('start_date')
            end_date = form.cleaned_data.get('end_date')

            if start_date:
                queryset = queryset.filter(date_added__gte=start_date)
            if end_date:
                queryset = queryset.filter(date_added__lte=end_date)

        return queryset

    def calculate_total_income(self, sales_queryset):
        total_income = sales_queryset.aggregate(total=Sum('grand_total'))['total'] or Decimal('0')
        return total_income

    def calculate_total_costs(self, sales_queryset):
        total_costs = Decimal('0')

        for sale in sales_queryset:
            for item in sale.salesitems_set.all():
                purchase_product = PurchaseProduct.objects.filter(product=item.product).first()
                if purchase_product:
                    product_cost = purchase_product.cost
                    qty_bought = sum([pp.qty for pp in PurchaseProduct.objects.filter(product=item.product)])
                    total_cost = product_cost * Decimal(qty_bought)
                    total_costs += total_cost

        return total_costs

    
    def get_sales_data_and_utilities(self, sales_queryset):
        sales_data = []
        total_utilities = Decimal(0)
        
        for sale in sales_queryset:
            sale_cost = self.calculate_sale_cost(sale)
            sale_profit = Decimal(sale.grand_total) - sale_cost
            products_list = []

            for item in sale.salesitems_set.all():
                purchase_product = PurchaseProduct.objects.filter(product=item.product).first()
                if purchase_product:
                    cost_per_unit = purchase_product.cost
                    total_qty_bought = sum([pp.qty for pp in PurchaseProduct.objects.filter(product=item.product)])
                    total_qty_sold = item.qty
                    total_qty_bought = total_qty_bought

                    product_profit = (Decimal(item.qty) * sale_profit) / Decimal(total_qty_sold)
                    
                    total_purchase_expense = cost_per_unit * Decimal(total_qty_bought)
                    
                    gross_profit = (sale_cost + product_profit) - total_purchase_expense
                    total_utilities += gross_profit
                    products_list.append({
                        'product_name': item.product.name,
                        'cost_per_unit': cost_per_unit,
<<<<<<< HEAD
                        'total_qty_vendida': total_qty_vendida,
                        'total_qty_comprada': total_qty_comprada,
                        'product_ganancia': product_ganancia,
                        'ganancia_estado': 'Positive' if product_ganancia > 0 else ('Negative' if product_ganancia < 0 else 'Neutral'),
=======
                        'total_qty_sold': total_qty_sold,
                        'total_qty_bought': total_qty_bought,
                        'product_profit': product_profit,
                        'profit_status': 'Positive' if product_profit > 0 else ('Negative' if product_profit < 0 else 'Neutral'),
>>>>>>> 34cc06a43306d90c1ec90c9b7ceefa3e8a99c7ea
                        
                        'total_purchase_expense': total_purchase_expense,
                        'gross_profit': gross_profit,
                    })
            
            sales_data.append({
                'date_added': sale.date_added,
                'products_list': products_list,
                'total_sale': Decimal(sale.grand_total),
                'total_cost': sale_cost,
                'total_profit': sale_profit,
            })

        return sales_data,total_utilities

    def calculate_sale_cost(self, sale):
        sale_cost = Decimal('0')
        for item in sale.salesitems_set.all():
            purchase_product = PurchaseProduct.objects.filter(product=item.product).first()
            if purchase_product:
                product_cost = purchase_product.cost
                sale_cost += product_cost * Decimal(item.qty)
        return sale_cost

    def render_pdf(self, html_string):
        pdf_file = io.BytesIO()
        pisa.CreatePDF(io.BytesIO(html_string.encode("UTF-8")), dest=pdf_file, encoding='UTF-8')
        pdf_file.seek(0)
        return pdf_file

    

class YearlyPDFProfitView(FormView):
    form_class = YearForm
    template_name = 'report/profit_pdf_year.html'

    def form_valid(self, form):
        year = form.cleaned_data['year']

        # Get sales filtered by year
        sales_queryset = Sales.objects.filter(date_added__year=year)

        # Calculate totals
        total_income = sales_queryset.aggregate(total=Sum('grand_total'))['total'] or 0
        total_costs = self.calculate_total_costs(sales_queryset)
        total_income_decimal = Decimal(total_income)
        total_costs_decimal = Decimal(total_costs)
        total_profit = total_income_decimal - total_costs_decimal

        sales_data, total_utilities = self.get_sales_data_and_utilities(sales_queryset)


        current_date = timezone.now()
        username = self.request.user.username
        unique_key = uuid.uuid4()

    
        context = {
            'sales_data': sales_data,
            'total_income': total_income,
            'total_costs': total_costs,
            'total_profit': total_profit,
            'total_utilities': total_utilities,
            'current_date': current_date,
            'username': username,
            'unique_key': unique_key,
            'year': year,
        }

    
        html_string = render_to_string(self.template_name, context)

    
        pdf_file = io.BytesIO()
        pisa_status = pisa.CreatePDF(io.BytesIO(html_string.encode("UTF-8")), dest=pdf_file, encoding='UTF-8')

        if pisa_status.err:
<<<<<<< HEAD
            return HttpResponse('Errors occurred while generating the PDF.')
=======
            return HttpResponse('There were errors generating the PDF.')
>>>>>>> 34cc06a43306d90c1ec90c9b7ceefa3e8a99c7ea

        pdf_file.seek(0)


        response = HttpResponse(pdf_file, content_type='application/pdf')
<<<<<<< HEAD
        response['Content-Disposition'] = f'attachment; filename="profit_report_yearly_{current_date.strftime("%Y%m%d_%H%M%S")}.pdf"'
=======
        response['Content-Disposition'] = f'attachment; filename="yearly_profit_report_{current_date.strftime("%Y%m%d_%H%M%S")}.pdf"'
>>>>>>> 34cc06a43306d90c1ec90c9b7ceefa3e8a99c7ea

        return response

    def calculate_total_costs(self, sales_queryset):
        total_costs = 0

        for sale in sales_queryset:
            sale_cost = self.calculate_sale_cost(sale)
            total_costs += sale_cost

        return total_costs

    def get_sales_data_and_utilities(self, sales_queryset):
        sales_data = []
        total_utilities = Decimal(0)

        for sale in sales_queryset:
            sale_items = salesItems.objects.filter(sale=sale)
            products_list = []

            for item in sale_items:
                purchase_product = PurchaseProduct.objects.filter(product=item.product).first()

                if purchase_product:
                    cost_per_unit = purchase_product.cost
                    total_qty_bought = PurchaseProduct.objects.filter(product=item.product).aggregate(total_qty=Sum('qty'))['total_qty'] or 0
                    total_qty_sold = item.qty
                    total_purchase_expense = cost_per_unit * total_qty_bought
                    
    
                    product_profit = Decimal(sale.grand_total) - (cost_per_unit * total_qty_sold)
                    
    
                    total_cost = self.calculate_sale_cost(sale)

    
                    gross_profit = (total_cost + product_profit) - total_purchase_expense
                    total_utilities += gross_profit
                    products_list.append({
                        'product_name': item.product.name,
                        'cost_per_unit': cost_per_unit,
<<<<<<< HEAD
                        'total_qty_vendida': total_qty_vendida,
                        'total_qty_comprada': total_qty_comprada,
                        'product_ganancia': product_ganancia,
                        'ganancia_estado': 'Positive' if product_ganancia > 0 else ('Negative' if product_ganancia < 0 else 'Neutral'),
                        'total_gasto_compras': total_gasto_compras,
                        'ganancia_bruta': ganancia_bruta,
=======
                        'total_qty_sold': total_qty_sold,
                        'total_qty_bought': total_qty_bought,
                        'product_profit': product_profit,
                        'profit_status': 'Positive' if product_profit > 0 else ('Negative' if product_profit < 0 else 'Neutral'),
                        'total_purchase_expense': total_purchase_expense,
                        'gross_profit': gross_profit,
>>>>>>> 34cc06a43306d90c1ec90c9b7ceefa3e8a99c7ea
                    })

            sales_data.append({
                'date_added': sale.date_added,
                'products_list': products_list,
                'total_sale': Decimal(sale.grand_total),
                'total_cost': self.calculate_sale_cost(sale),
                'total_profit': Decimal(sale.grand_total) - self.calculate_sale_cost(sale),
            })

        return sales_data, total_utilities

    def calculate_sale_cost(self, sale):
        sale_cost = 0

        for item in sale.salesitems_set.all():
            purchase_product = PurchaseProduct.objects.filter(product=item.product).first()

            if purchase_product:
                sale_cost += purchase_product.cost * item.qty

        return sale_cost


class MonthlyPDFProfitView(FormView):
    form_class = MonthYearReportForm
    template_name = 'report/profit_pdf_month.html'

    def form_valid(self, form):
        year = form.cleaned_data['year']
        month = form.cleaned_data['month']

        
        try:
            month = int(month)
            month_name = MONTH_CHOICES[month - 1][1]
        except ValueError:
<<<<<<< HEAD
            return HttpResponseBadRequest("The provided year or month is not valid.")
=======
            return HttpResponseBadRequest("The provided year or month are not valid.")
>>>>>>> 34cc06a43306d90c1ec90c9b7ceefa3e8a99c7ea

    
        sales_queryset = Sales.objects.filter(date_added__year=year, date_added__month=month)


        total_income = sales_queryset.aggregate(total=Sum('grand_total'))['total'] or 0
        total_costs = self.calculate_total_costs(sales_queryset)
        total_income_decimal = Decimal(total_income)
        total_costs_decimal = Decimal(total_costs)
        total_profit = total_income_decimal - total_costs_decimal


        sales_data, total_utilities = self.get_sales_data_and_utilities(sales_queryset)

        current_date = timezone.now()
        username = self.request.user.username
        unique_key = uuid.uuid4()


        context = {
            'sales_data': sales_data,
            'total_income': total_income,
            'total_costs': total_costs,
            'total_profit': total_profit,
            'total_utilities': total_utilities,
            'current_date': current_date,
            'username': username,
            'unique_key': unique_key,
            'year': year,
            'month': month_name,
        }

    
        html_string = render_to_string(self.template_name, context)

    
        pdf_file = io.BytesIO()
        pisa_status = pisa.CreatePDF(io.BytesIO(html_string.encode("UTF-8")), dest=pdf_file, encoding='UTF-8')

        if pisa_status.err:
<<<<<<< HEAD
            return HttpResponse('Errors occurred while generating the PDF.')
=======
            return HttpResponse('There were errors generating the PDF.')
>>>>>>> 34cc06a43306d90c1ec90c9b7ceefa3e8a99c7ea

        pdf_file.seek(0)


        response = HttpResponse(pdf_file, content_type='application/pdf')
<<<<<<< HEAD
        response['Content-Disposition'] = f'attachment; filename="profit_report_monthly_{current_date.strftime("%Y%m%d_%H%M%S")}.pdf"'
=======
        response['Content-Disposition'] = f'attachment; filename="monthly_profit_report_{current_date.strftime("%Y%m%d_%H%M%S")}.pdf"'
>>>>>>> 34cc06a43306d90c1ec90c9b7ceefa3e8a99c7ea

        return response

    def calculate_total_costs(self, sales_queryset):
        total_costs = 0

        for sale in sales_queryset:
            sale_cost = self.calculate_sale_cost(sale)
            total_costs += sale_cost

        return total_costs

    
    def get_sales_data_and_utilities(self, sales_queryset):
        sales_data = []
        total_utilities = Decimal(0)

        for sale in sales_queryset:
            sale_items = salesItems.objects.filter(sale=sale)
            products_list = []

            for item in sale_items:
                purchase_product = PurchaseProduct.objects.filter(product=item.product).first()

                if purchase_product:
                    cost_per_unit = purchase_product.cost
                    total_qty_bought = PurchaseProduct.objects.filter(product=item.product).aggregate(total_qty=Sum('qty'))['total_qty'] or 0
                    total_qty_sold = item.qty
                    total_purchase_expense = cost_per_unit * total_qty_bought
                    
                
                    product_profit = Decimal(sale.grand_total) - (cost_per_unit * total_qty_sold)
                    
                
                    total_cost = self.calculate_sale_cost(sale)

                
                    gross_profit = (total_cost + product_profit) - total_purchase_expense

                    total_utilities += gross_profit
                    
                    products_list.append({
                        'product_name': item.product.name,
                        'cost_per_unit': cost_per_unit,
<<<<<<< HEAD
                        'total_qty_vendida': total_qty_vendida,
                        'total_qty_comprada': total_qty_comprada,
                        'product_ganancia': product_ganancia,
                        'ganancia_estado': 'Positive' if product_ganancia > 0 else ('Negative' if product_ganancia < 0 else 'Neutral'),
                        'total_gasto_compras': total_gasto_compras,
                        'ganancia_bruta': ganancia_bruta,
=======
                        'total_qty_sold': total_qty_sold,
                        'total_qty_bought': total_qty_bought,
                        'product_profit': product_profit,
                        'profit_status': 'Positive' if product_profit > 0 else ('Negative' if product_profit < 0 else 'Neutral'),
                        'total_purchase_expense': total_purchase_expense,
                        'gross_profit': gross_profit,
>>>>>>> 34cc06a43306d90c1ec90c9b7ceefa3e8a99c7ea
                    })

            sales_data.append({
                'date_added': sale.date_added,
                'products_list': products_list,
                'total_sale': Decimal(sale.grand_total),
                'total_cost': self.calculate_sale_cost(sale),
                'total_profit': Decimal(sale.grand_total) - self.calculate_sale_cost(sale),
            })

        return sales_data, total_utilities

    def calculate_sale_cost(self, sale):
        sale_cost = 0

        for item in sale.salesitems_set.all():
            purchase_product = PurchaseProduct.objects.filter(product=item.product).first()

            if purchase_product:
                sale_cost += purchase_product.cost * item.qty

        return sale_cost


class DailyPDFProfitView(FormView):
    form_class = DayMonthYearReportForm
    template_name = 'report/profit_pdf_day.html'

    def form_valid(self, form):
        year = form.cleaned_data['year']
        month = form.cleaned_data['month']
        day = form.cleaned_data['day']
        
        try:
            month = int(month)
            month_name = MONTH_CHOICES[month - 1][1]
        except ValueError:
<<<<<<< HEAD
            return HttpResponseBadRequest("The provided year or month is not valid.")
=======
            return HttpResponseBadRequest("The provided year or month are not valid.")
>>>>>>> 34cc06a43306d90c1ec90c9b7ceefa3e8a99c7ea

        
        sales_queryset = Sales.objects.filter(date_added__year=year, date_added__month=month, date_added__day=day)

        
        total_income = sales_queryset.aggregate(total=Sum('grand_total'))['total'] or 0
        total_costs = self.calculate_total_costs(sales_queryset)
        total_income_decimal = Decimal(total_income)
        total_costs_decimal = Decimal(total_costs)
        total_profit = total_income_decimal - total_costs_decimal


        
        sales_data, total_utilities = self.get_sales_data_and_utilities(sales_queryset)

        
        current_date = timezone.now()
        username = self.request.user.username
        unique_key = uuid.uuid4()

        
        context = {
            'sales_data': sales_data,
            'total_income': total_income,
            'total_costs': total_costs,
            'total_profit': total_profit,
            'total_utilities': total_utilities,
            'current_date': current_date,
            'username': username,
            'unique_key': unique_key,
            'year': year,
            'month': month_name,
            'day': day,
        }

    
        html_string = render_to_string(self.template_name, context)

    
        pdf_file = io.BytesIO()
        pisa_status = pisa.CreatePDF(io.BytesIO(html_string.encode("UTF-8")), dest=pdf_file, encoding='UTF-8')

        if pisa_status.err:
<<<<<<< HEAD
            return HttpResponse('Errors occurred while generating the PDF.')
=======
            return HttpResponse('There were errors generating the PDF.')
>>>>>>> 34cc06a43306d90c1ec90c9b7ceefa3e8a99c7ea

        pdf_file.seek(0)


        response = HttpResponse(pdf_file, content_type='application/pdf')
<<<<<<< HEAD
        response['Content-Disposition'] = f'attachment; filename="profit_report_daily_{current_date.strftime("%Y%m%d_%H%M%S")}.pdf"'
=======
        response['Content-Disposition'] = f'attachment; filename="daily_profit_report_{current_date.strftime("%Y%m%d_%H%M%S")}.pdf"'
>>>>>>> 34cc06a43306d90c1ec90c9b7ceefa3e8a99c7ea

        return response

    def calculate_total_costs(self, sales_queryset):
        total_costs = 0

        for sale in sales_queryset:
            sale_cost = self.calculate_sale_cost(sale)
            total_costs += sale_cost

        return total_costs

    def get_sales_data_and_utilities(self, sales_queryset):
        sales_data = []
        total_utilities = Decimal(0)

        for sale in sales_queryset:
            sale_items = salesItems.objects.filter(sale=sale)
            products_list = []

            for item in sale_items:
                purchase_product = PurchaseProduct.objects.filter(product=item.product).first()

                if purchase_product:
                    cost_per_unit = purchase_product.cost
                    total_qty_bought = PurchaseProduct.objects.filter(product=item.product).aggregate(total_qty=Sum('qty'))['total_qty'] or 0
                    total_qty_sold = item.qty
                    total_purchase_expense = cost_per_unit * total_qty_bought
                    
    
                    product_profit = Decimal(sale.grand_total) - (cost_per_unit * total_qty_sold)
                    
    
                    total_cost = self.calculate_sale_cost(sale)

    
                    gross_profit = (total_cost + product_profit) - total_purchase_expense

                    total_utilities += gross_profit

                    products_list.append({
                        'product_name': item.product.name,
                        'cost_per_unit': cost_per_unit,
<<<<<<< HEAD
                        'total_qty_vendida': total_qty_vendida,
                        'total_qty_comprada': total_qty_comprada,
                        'product_ganancia': product_ganancia,
                        'ganancia_estado': 'Positive' if product_ganancia > 0 else ('Negative' if product_ganancia < 0 else 'Neutral'),
                        'total_gasto_compras': total_gasto_compras,
                        'ganancia_bruta': ganancia_bruta,
=======
                        'total_qty_sold': total_qty_sold,
                        'total_qty_bought': total_qty_bought,
                        'product_profit': product_profit,
                        'profit_status': 'Positive' if product_profit > 0 else ('Negative' if product_profit < 0 else 'Neutral'),
                        'total_purchase_expense': total_purchase_expense,
                        'gross_profit': gross_profit,
>>>>>>> 34cc06a43306d90c1ec90c9b7ceefa3e8a99c7ea
                    })

            sales_data.append({
                'date_added': sale.date_added,
                'products_list': products_list,
                'total_sale': Decimal(sale.grand_total),
                'total_cost': self.calculate_sale_cost(sale),
                'total_profit': Decimal(sale.grand_total) - self.calculate_sale_cost(sale),
            })

        return sales_data, total_utilities
    
    def calculate_sale_cost(self, sale):
        sale_cost = 0

        for item in sale.salesitems_set.all():
            purchase_product = PurchaseProduct.objects.filter(product=item.product).first()

            if purchase_product:
                sale_cost += purchase_product.cost * item.qty

        return sale_cost
