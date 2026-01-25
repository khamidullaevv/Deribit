

from django.contrib import admin
from .models import Price


@admin.register(Price)
class PriceAdmin(admin.ModelAdmin):
    
    list_display = ('ticker', 'price', 'timestamp', 'created_at')
    list_filter = ('ticker', 'created_at')
    search_fields = ('ticker',)
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Price Data', {
            'fields': ('ticker', 'price', 'timestamp')
        }),
        ('Meta Information', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    ordering = ('-timestamp',)
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
