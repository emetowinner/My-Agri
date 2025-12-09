from django.db import models
from django.utils import timezone


class CrawlJob(models.Model):
    """Model for managing web crawling jobs"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    keywords = models.TextField(
        help_text="Keywords to search for (comma-separated)"
    )
    country = models.CharField(
        max_length=100,
        help_text="Country to filter news from"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    articles_found = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Crawl Job #{self.id} - {self.keywords[:50]} ({self.country})"

    def mark_completed(self):
        """Mark the job as completed"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()

    def mark_failed(self, error_msg):
        """Mark the job as failed"""
        self.status = 'failed'
        self.error_message = error_msg
        self.completed_at = timezone.now()
        self.save()


class NewsArticle(models.Model):
    """Model for storing scraped news articles"""
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('published', 'Published'),
    ]

    title = models.CharField(max_length=500)
    url = models.URLField(max_length=1000, unique=True)
    summary = models.TextField(help_text="Three paragraph summary")
    source_name = models.CharField(max_length=200, blank=True)
    country = models.CharField(max_length=100)
    keywords_matched = models.TextField(
        help_text="Keywords that matched this article"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    crawl_job = models.ForeignKey(
        CrawlJob,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='articles'
    )
    is_manual = models.BooleanField(
        default=False,
        help_text="Was this article manually added?"
    )

    # Timestamps
    scraped_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-scraped_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['published_at']),
        ]

    def __str__(self):
        return f"{self.title[:50]}... ({self.status})"

    def approve(self, auto_publish=True):
        """Approve the article and optionally publish it"""
        self.status = 'approved'
        self.reviewed_at = timezone.now()
        if auto_publish:
            self.publish()
        else:
            self.save()

    def reject(self):
        """Reject the article"""
        self.status = 'rejected'
        self.reviewed_at = timezone.now()
        self.save()

    def publish(self):
        """Publish the article"""
        self.status = 'published'
        self.published_at = timezone.now()
        if not self.reviewed_at:
            self.reviewed_at = timezone.now()
        self.save()

    @property
    def summary_paragraphs(self):
        """Split summary into paragraphs"""
        return [p.strip() for p in self.summary.split('\n\n') if p.strip()]
