from django.contrib import admin
from django.utils.html import format_html
from .models import Partner, Category, Product, Inbound, Sale, ReturnToPartner

# 1. Hamkorlar (Partner) sozlamalari
@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'colored_balance')
    search_fields = ('name', 'phone')

    def colored_balance(self, obj):
        # Qarz bo'lsa qizil, bo'lmasa yashil rangda ko'rsatish
        color = 'red' if obj.balance > 0 else 'green'
        return format_html('<b style="color: {};">{} so\'m</b>', color, obj.balance)
    
    colored_balance.short_description = 'Balans (Qarzimiz)'

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent')
    search_fields = ('name',)
    # Bu qator parent tanlayotganda qidiruv berish imkonini beradi
    autocomplete_fields = ('parent',)

# 3. Mahsulotlar (Product) sozlamalari
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('barcode', 'name', 'category', 'colored_stock', 'cost_price', 'selling_price')
    list_filter = ('category',)
    search_fields = ('name', 'barcode')
    list_editable = ('selling_price',) # To'g'ridan-to'g'ri ro'yxatda narxni o'zgartirish

    def colored_stock(self, obj):
        if obj.stock < 10:
            return format_html('<b style="color: orange;">{} (Kam qolgan)</b>', obj.stock)
        return obj.stock
    
    colored_stock.short_description = 'Ombor qoldig\'i'

# 4. Kirim (Inbound) - Hamkorlardan tovar olish
@admin.register(Inbound)
class InboundAdmin(admin.ModelAdmin):
    list_display = ('product', 'partner', 'quantity', 'buy_price', 'total_cost', 'created_at')
    list_filter = ('partner', 'created_at')
    autocomplete_fields = ('product', 'partner') # Tovar ko'p bo'lsa qidiruv qulay bo'ladi

    def total_cost(self, obj):
        return obj.quantity * obj.buy_price
    
    total_cost.short_description = 'Jami summa'

# 5. Sotuv (Sale) - Chiqim
@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('product', 'quantity', 'sold_at_price', 'profit_display', 'created_at')
    list_filter = ('created_at',)
    readonly_fields = ('profit',) # Foyda avtomat hisoblanadi, qo'lda o'zgartirib bo'lmaydi

    def profit_display(self, obj):
        return format_html('<b style="color: blue;">+{}</b>', obj.profit)
    
    profit_display.short_description = 'Sof Foyda'

# 6. Vozvrat (ReturnToPartner) - Hamkorga qaytarish
@admin.register(ReturnToPartner)
class ReturnToPartnerAdmin(admin.ModelAdmin):
    list_display = ('product', 'partner', 'quantity', 'created_at')
    autocomplete_fields = ('product', 'partner')