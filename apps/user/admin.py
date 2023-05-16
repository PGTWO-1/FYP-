from django.contrib import admin
from .models import User, Address


# Register your models here.
class UserInfoAdmin(admin.ModelAdmin):
    list_display = ['id', 'password', 'last_login', 'is_superuser', 'username', 'first_name', 'last_name', 'email',
                    'is_staff']
    # admin后台展示相应信息


admin.site.register(User, UserInfoAdmin)
admin.site.register(Address)
