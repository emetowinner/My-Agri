from django.contrib import admin
from .models import CrawlJob, NewsArticle


@admin.register(CrawlJob)
class CrawlJobAdmin(admin.ModelAdmin):
    list_display = ['id', 'keywords_preview', 'country', 'status', 'articles_found', 'created_at']
    list_filter = ['status', 'country', 'created_at']
    search_fields = ['keywords', 'country']
    readonly_fields = ['created_at', 'completed_at', 'articles_found']

    def keywords_preview(self, obj):
        return obj.keywords[:50] + '...' if len(obj.keywords) > 50 else obj.keywords
    keywords_preview.short_description = 'Keywords'


@admin.register(NewsArticle)
class NewsArticleAdmin(admin.ModelAdmin):
    list_display = ['id', 'title_preview', 'source_name', 'country', 'status', 'is_manual', 'scraped_at']
    list_filter = ['status', 'country', 'is_manual', 'scraped_at']
    search_fields = ['title', 'source_name', 'keywords_matched']
    readonly_fields = ['scraped_at', 'reviewed_at', 'published_at', 'crawl_job']

    fieldsets = (
        ('Article Information', {
            'fields': ('title', 'url', 'summary', 'source_name')
        }),
        ('Classification', {
            'fields': ('country', 'keywords_matched', 'status', 'is_manual')
        }),
        ('Relationships', {
            'fields': ('crawl_job',)
        }),
        ('Timestamps', {
            'fields': ('scraped_at', 'reviewed_at', 'published_at')
        }),
    )

    def title_preview(self, obj):
        return obj.title[:50] + '...' if len(obj.title) > 50 else obj.title
    title_preview.short_description = 'Title'

    actions = ['approve_and_publish', 'reject_articles']

    def approve_and_publish(self, request, queryset):
        count = 0
        for article in queryset:
            article.approve(auto_publish=True)
            count += 1
        self.message_user(request, f'{count} article(s) approved and published.')
    approve_and_publish.short_description = 'Approve and publish selected articles'

    def reject_articles(self, request, queryset):
        count = queryset.update(status='rejected')
        self.message_user(request, f'{count} article(s) rejected.')
    reject_articles.short_description = 'Reject selected articles'
