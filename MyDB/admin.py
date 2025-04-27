from django.contrib import admin
from .models import signup, add, crawl

# Register your models here.

admin.site.register(signup)
admin.site.register(add)
admin.site.register(crawl)
