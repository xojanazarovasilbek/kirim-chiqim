
# views.py boshida
from .models import Product, Partner, Inbound  # Supplier o'rniga Partner yozildi # <--- Supplier qo'shilganiga ishonch hosil qiling



from django.shortcuts import render, redirect
from .models import Product, Partner, Sale, Inbound, Category
from django.db.models import Sum, F

def dashboard(request):
    # 1. Tepada turadigan umumiy raqamlar
    total_sales = Sale.objects.aggregate(total=Sum(F('quantity') * F('sold_at_price')))['total'] or 0
    total_profit = Sale.objects.aggregate(total=Sum('profit'))['total'] or 0
    total_debt = Partner.objects.aggregate(total=Sum('balance'))['total'] or 0
    low_stock = Product.objects.filter(stock__lt=10).count()

    # 2. Hamkorlar bo'yicha hisobot (Jadval uchun)
    partners = Partner.objects.all()
    
    # 3. Oxirgi kirimlar
    recent_inbounds = Inbound.objects.select_related('partner', 'product').order_by('-created_at')[:10]

    context = {
        'total_sales': total_sales,
        'total_profit': total_profit,
        'total_debt': total_debt,
        'low_stock': low_stock,
        'partners': partners,
        'recent_inbounds': recent_inbounds,
    }
    return render(request, 'dashboard.html', context)

# def product_list(request):
#     # Kategoriyalar bo'yicha barcha mahsulotlar
#     categories = Category.objects.all()
#     products = Product.objects.select_related('category').all()
#     return render(request, 'products.html', {'products': products, 'categories': categories})

def product_list(request):
    category_id = request.GET.get('category')
    categories = Category.objects.all()

    if category_id:
        products = Product.objects.filter(category_id=category_id)
    else:
        products = Product.objects.all()

    return render(request, 'products.html', {
        'products': products, 
        'categories': categories
    })
# Umumiy hisobotlar uchun misol
def get_general_report():
    total_profit = Sale.objects.aggregate(Sum('profit'))['profit__sum'] or 0
    total_stock_value = Product.objects.aggregate(total=Sum(F('stock') * F('cost_price')))['total'] or 0
    total_partner_debts = Partner.objects.aggregate(Sum('balance'))['balance__sum'] or 0
    
    return {
        "Jami sof foyda": total_profit,
        "Ombordagi tovar qiymati": total_stock_value,
        "Hamkorlardan jami qarz": total_partner_debts
    }

from django.http import JsonResponse
from .models import Product, Sale
import json

from django.shortcuts import get_object_or_404

from django.db import transaction # Xavfsiz hisob-kitob uchun

from django.views.decorators.cache import never_cache

import json
from decimal import Decimal
from django.http import JsonResponse
from django.db import transaction
from django.views.decorators.cache import never_cache
from .models import Product, Sale

@never_cache
def pos_view(request):
    categories = Category.objects.all()
    products = Product.objects.filter(stock__gt=0)
    return render(request, 'pos.html', {
        'categories': categories,
        'products': products
    })

@transaction.atomic
def api_sale(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            items = data.get('items', [])

            if not items:
                return JsonResponse({'error': 'Savatcha bo\'sh'}, status=400)

            for item in items:
                # Mahsulotni ID orqali bazadan olish
                product = Product.objects.select_for_update().get(id=item['id'])
                qty = Decimal(str(item['qty']))

                # 1. Ombor qoldig'ini aynan View ichida tekshiramiz
                if product.stock < qty:
                    return JsonResponse({
                        'error': f"{product.name} yetarli emas. Mavjud: {product.stock}"
                    }, status=400)

                # 2. Sotuv tarixini yaratish
                Sale.objects.create(
                    product=product,
                    quantity=qty,
                    sold_at_price=product.selling_price
                )

                # 3. Ombor qoldig'ini kamaytirish va saqlash
                product.stock -= qty
                product.save()

            return JsonResponse({'status': 'ok'})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

# Mahsulotni shtrix-kod orqali topish (AJAX uchun)
def get_product_by_barcode(request, barcode):
    try:
        product = Product.objects.get(barcode=barcode)
        data = {
            'id': product.id,
            'name': product.name,
            'price': float(product.selling_price),
            'stock': product.stock
        }
        return JsonResponse({'success': True, 'product': data})
    except Product.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Mahsulot topilmadi'})

# Sotuvni bazaga yozish
def complete_sale(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        cart = data.get('cart', [])
        
        for item in cart:
            product = Product.objects.get(id=item['id'])
            Sale.objects.create(
                product=product,
                quantity=item['quantity'],
                sold_at_price=item['price']
            )
        return JsonResponse({'success': True})
    

def partner_list(request):
    partners = Partner.objects.all()
    return render(request, 'partners.html', {'partners': partners})

def partner_detail(request, pk):
    partner = Partner.objects.get(pk=pk)
    # Shu hamkorga tegishli barcha kirimlar (tovarlar)
    inbounds = Inbound.objects.filter(partner=partner).order_by('-created_at')
    return render(request, 'partner_detail.html', {'partner': partner, 'inbounds': inbounds})

from django.shortcuts import render, redirect, get_object_or_404
from .models import Product, Partner, Inbound, ReturnToPartner
from decimal import Decimal, InvalidOperation # <--- Shuni to'g'rilab qo'ying
# 1. Tovar qabul qilish (Kirim)
from decimal import Decimal

from django.shortcuts import render, redirect
from decimal import Decimal, InvalidOperation
from .models import Product, Partner, Inbound  # Supplier emas, Partner!

def inbound_create(request):
    if request.method == "POST":
        partner_id = request.POST.get('supplier') # HTMLda name="supplier" bo'lsa
        product_id = request.POST.get('product')
        quantity_str = request.POST.get('quantity') or "0"
        cost_price_str = request.POST.get('cost_price') or "0"

        try:
            # Modelning save() metodi avtomatik hisob-kitob qilgani uchun
            # biz faqat Inbound obyektini yaratishimiz kifoya
            Inbound.objects.create(
                partner_id=partner_id,
                product_id=product_id,
                quantity=Decimal(quantity_str),
                buy_price=Decimal(cost_price_str)
            )
            # Endi bu yerda product.save() qilish shart emas, 
            # chunki Inbound modelining save() metodi buni bajaradi.

            return redirect('/pos/') # O'zingizga kerakli URL

        except (InvalidOperation, Exception) as e:
            products = Product.objects.all()
            partners = Partner.objects.all()
            return render(request, 'inbound_form.html', {
                'products': products,
                'partners': partners,
                'error': f"Xatolik yuz berdi: {e}"
            })

    # GET so'rovi uchun
    products = Product.objects.all()
    partners = Partner.objects.all()
    return render(request, 'inbound_form.html', {
        'products': products, 
        'partners': partners
    })
# 2. Hamkorga qaytarish (Vozvrat)
def return_create(request):
    partners = Partner.objects.all()
    products = Product.objects.filter(stock__gt=0)
    
    if request.method == "POST":
        partner_id = request.POST.get('partner')
        product_id = request.POST.get('product')
        quantity = int(request.POST.get('quantity'))
        
        partner = get_object_or_404(Partner, id=partner_id)
        product = get_object_or_404(Product, id=product_id)
        
        if product.stock >= quantity:
            ReturnToPartner.objects.create(
                partner=partner,
                product=product,
                quantity=quantity
            )
            return redirect('partners')
        else:
            return render(request, 'return_form.html', {'error': "Omborda yetarli tovar yo'q!"})

    return render(request, 'return_form.html', {'partners': partners, 'products': products})

from .models import Payment

def payment_create(request):
    partners = Partner.objects.all()
    if request.method == "POST":
        partner_id = request.POST.get('partner')
        amount = Decimal(request.POST.get('amount'))
        comment = request.POST.get('comment')
        
        partner = get_object_or_404(Partner, id=partner_id)
        
        Payment.objects.create(
            partner=partner,
            amount=amount,
            comment=comment
        )
        return redirect('partners') # Hamkorlar ro'yxatiga qaytish

    return render(request, 'payment_form.html', {'partners': partners})

# Yangi mahsulot yaratish
from decimal import Decimal

from django.shortcuts import render, redirect
from .models import Product, Category
from decimal import Decimal

def product_create(request):
    if request.method == "POST":
        try:
            # Formadan ma'lumotlarni olish
            name = request.POST.get('name')
            category_id = request.POST.get('category')
            cost_price = request.POST.get('cost_price') or "0"
            selling_price = request.POST.get('selling_price') or "0"
            quantity = request.POST.get('quantity') or "0"
            unit = request.POST.get('unit') or "dona"

            # Bazaga saqlash
            Product.objects.create(
                name=name,
                category_id=category_id,
                cost_price=Decimal(cost_price),
                selling_price=Decimal(selling_price),
                stock=Decimal(quantity),
                unit=unit,
                barcode=None  # Shtrix-kod shart emas
            )
            return redirect('products') # Mahsulotlar ro'yxati sahifasiga

        except Exception as e:
            categories = Category.objects.all()
            return render(request, 'product_form.html', {
                'categories': categories,
                'error': f"Xatolik: {e}"
            })

    # GET so'rovi uchun
    categories = Category.objects.all()
    return render(request, 'product_form.html', {'categories': categories})
# Yangi kategoriya yaratish
def category_create(request):
    categories = Category.objects.all() # Parent tanlash uchun
    if request.method == "POST":
        name = request.POST.get('name')
        parent_id = request.POST.get('parent')
        
        parent = Category.objects.get(id=parent_id) if parent_id else None
        Category.objects.create(name=name, parent=parent)
        return redirect('dashboard')
    return render(request, 'category_form.html', {'categories': categories})

def get_product_unit(request, pk):
    product = Product.objects.get(pk=pk)
    return JsonResponse({'unit': product.unit})




from django.utils import timezone
from datetime import datetime

def transaction_history(request):
    # Sanaga qarab filtrlash (masalan: 2024-05-20)
    date_str = request.GET.get('date')
    
    inbounds = Inbound.objects.all().order_by('-created_at')
    outbounds = Sale.objects.all().order_by('-created_at')

    if date_str:
        inbounds = inbounds.filter(created_at__date=date_str)
        outbounds = outbounds.filter(created_at__date=date_str)

    # O'chirish logikasi (Tanlanganlarni o'chirish)
    if request.method == "POST" and "delete_ids" in request.POST:
        ids_to_delete = request.POST.getlist('selected_ids')
        type_to_delete = request.POST.get('type') # 'in' yoki 'out'
        
        if type_to_delete == 'in':
            Inbound.objects.filter(id__in=ids_to_delete).delete()
        else:
            Sale.objects.filter(id__in=ids_to_delete).delete()
        return redirect('transaction_history')

    return render(request, 'history.html', {
        'inbounds': inbounds,
        'outbounds': outbounds,
        'today': datetime.now().date()
    })