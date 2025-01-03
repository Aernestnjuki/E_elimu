from django.contrib import admin

# Register your models here.
from . import models

# class CourseModel(admin.ModelAdmin):
#     list_display = ['pk', 'title']

admin.site.register(models.Teacher)
admin.site.register(models.Category)
admin.site.register(models.Course)
admin.site.register(models.Variant)
admin.site.register(models.VariantItem)
admin.site.register(models.Question_Answer)
admin.site.register(models.Question_Answer_Message)
admin.site.register(models.Cart)
admin.site.register(models.CartOrder)
admin.site.register(models.CartOrderItem)
admin.site.register(models.Certificate)
admin.site.register(models.Completedlesson)
admin.site.register(models.EnrolledCourse)
admin.site.register(models.Notes)
admin.site.register(models.Review)
admin.site.register(models.Notification)
admin.site.register(models.Coupon)
admin.site.register(models.WishList)
admin.site.register(models.Country)