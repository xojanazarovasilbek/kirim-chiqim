from django.db import models
from django.db.models import Sum, F

from django.db import models

# 1. Hamkorlar
class Partner(models.Model):
    name = models.CharField(max_length=255, verbose_name="Hamkor nomi")
    phone = models.CharField(max_length=20, verbose_name="Telefon")
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Balans (Qarz)")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Hamkor"
        verbose_name_plural = "Hamkorlar"

# 2. Kategoriyalar
class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="Kategoriya nomi")
    # related_name qo'shish tavsiya etiladi
    parent = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='children',
        verbose_name="Ota kategoriya"
    )

    def __str__(self):
        # Agar ota kategoriyasi bo'lsa, "Oziq-ovqat > Ichimliklar" ko'rinishida chiqarish
        if self.parent:
            return f"{self.parent.name} -> {self.name}"
        return self.name

    class Meta:
        verbose_name = "Kategoriya"
        verbose_name_plural = "Kategoriyalar"

# 3. Mahsulotlar
class Product(models.Model):
    # O'lchov birliklari uchun variantlar
    UNIT_CHOICES = [
        ('dona', 'Dona'),
        ('kg', 'Kilogramm'),
    ]

    name = models.CharField(max_length=255)
    category = models.ForeignKey('Category', on_delete=models.CASCADE)
    barcode = models.CharField(max_length=100, blank=True, null=True)
    
    # Qoldiq (kg bo'lishi mumkinligi uchun DecimalField ishlatamiz)
    stock = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    cost_price = models.DecimalField(max_digits=12, decimal_places=2)
    selling_price = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Tanlovli maydon
    unit = models.CharField(
        max_length=10, 
        choices=UNIT_CHOICES, 
        default='dona'
    )

    def __str__(self):
        return self.name

# 4. Kirim (Hamkordan mahsulot kelishi)
class Inbound(models.Model):
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    buy_price = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Kelgan tovar sonini omborga qo'shish
        self.product.stock += self.quantity
        self.product.cost_price = self.buy_price
        self.product.save()
        
        # Hamkor balansiga qarz sifatida yozish
        total_cost = self.quantity * self.buy_price
        self.partner.balance += total_cost
        self.partner.save()
        
        super().save(*args, **kwargs)

# 5. Sotuv (Chiqim)
class Sale(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=2) # Integer o'rniga Decimal yaxshi (kg uchun)
    sold_at_price = models.DecimalField(max_digits=12, decimal_places=2)
    profit = models.DecimalField(max_digits=12, decimal_places=2, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # FAQAT foydani hisoblaymiz, ombordan ayirmaymiz!
        self.profit = (self.sold_at_price - self.product.cost_price) * self.quantity
        super().save(*args, **kwargs)

# 6. Vozvrat (Hamkorga qaytarish)
class ReturnToPartner(models.Model):
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Ombordan ayirish
        self.product.stock -= self.quantity
        self.product.save()
        
        # Hamkorning balansidan (qarzimizdan) ayirish
        return_value = self.quantity * self.product.cost_price
        self.partner.balance -= return_value
        self.partner.save()
        
        super().save(*args, **kwargs)

from decimal import Decimal

class Payment(models.Model):
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, verbose_name="Hamkor")
    amount = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="To'lov summasi")
    comment = models.TextField(blank=True, null=True, verbose_name="Izoh")
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # To'lov qilinganda hamkorning qarzini kamaytiramiz
        self.partner.balance -= Decimal(self.amount)
        self.partner.save()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "To'lov"
        verbose_name_plural = "To'lovlar"