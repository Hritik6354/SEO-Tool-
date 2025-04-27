from django.contrib.auth.models import User
from django.db import models


# Create your models here.

class MyDB(models.Model):
    email = models.EmailField(max_length=30)
    password = models.CharField(max_length=50)
        
class signup(models.Model):
    username=models.CharField(max_length=200,default='')
    umobile=models.CharField(max_length=200,default='')
    uemail=models.EmailField(max_length=200,default='')
    password=models.CharField(max_length=200,default='')
    
    objects = models.Manager()
    
    def __str__(self):
        return f'{self.username} {self.umobile} {self.uemail} {self.password}'


class add(models.Model):
    user = models.ForeignKey(signup, on_delete=models.CASCADE)
    url = models.URLField()
    title = models.CharField(max_length=100)
    
    objects = models.Manager()
    
    def __str__(self):
        return f'{self.title} - {self.user.username}'
    
class crawl(models.Model):
    user = models.ForeignKey(signup, on_delete=models.CASCADE, null=False, blank=False)
    url = models.URLField()
    title = models.CharField(max_length=255, blank=True, null=True)
    meta_description = models.TextField(blank=True, null=True)
    h1_tags = models.TextField(blank=True, null=True)
    internal_links = models.TextField(blank=True, null=True)
    external_links = models.TextField(blank=True, null=True)
    keyword_density = models.JSONField(blank=True, null=True)
    #page_speed = models.IntegerField(blank=True, null=True)
    broken_links = models.JSONField(blank=True, null=True)
    crawled_at = models.DateTimeField(auto_now_add=True)


    objects = models.Manager()

    def __str__(self):
        return self.url    
    
class Profile(models.Model):
    user = models.ForeignKey(signup, on_delete=models.CASCADE)
    forget_password_token = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.user.username
    
    
class CrawlResult(models.Model):
    project = models.ForeignKey(add, on_delete=models.CASCADE, related_name='crawl_results')
    crawl_time = models.DateTimeField(auto_now_add=True)
    page_title = models.CharField(max_length=255, null=True, blank=True)
    meta_description = models.TextField(null=True, blank=True)
    h1_tags = models.TextField(null=True, blank=True)
    internal_links = models.IntegerField(default=0)
    external_links = models.IntegerField(default=0)
    broken_links = models.IntegerField(default=0)
    file_size = models.IntegerField(default=0)  # In KB
    word_count = models.IntegerField(default=0)
    media_files = models.IntegerField(default=0)
    page_speed = models.FloatField(default=0.5)  # 0-1 scale (placeholder, integrate with PageSpeed API for real data)
    suggested_keywords = models.TextField(blank=True)
    seo_suggestions = models.TextField(blank=True)
    
    def __str__(self):
        return f"Crawl on {self.crawl_time} for {self.project.title}"