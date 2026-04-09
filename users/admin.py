from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['email', 'username', 'is_verified', 'is_active', 'date_joined']
    list_filter = ['is_verified', 'is_active', 'is_staff']
    search_fields = ['email', 'username']
    ordering = ['-date_joined']
    fieldsets = UserAdmin.fieldsets + (
        ('DataWizard', {'fields': ('is_verified',)}),
    )

# Register your models here.
