from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Q

from .models import CrawlJob, NewsArticle
from .forms import CrawlJobForm, ManualArticleForm
from .utils.scraper import run_crawl_job
import threading


# ============= Dashboard Views =============

class DashboardView(ListView):
    """Main dashboard showing all crawl jobs"""
    model = CrawlJob
    template_name = 'news/dashboard.html'
    context_object_name = 'crawl_jobs'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_jobs'] = CrawlJob.objects.count()
        context['pending_articles'] = NewsArticle.objects.filter(status='pending').count()
        context['published_articles'] = NewsArticle.objects.filter(status='published').count()
        return context


class CrawlJobCreateView(CreateView):
    """Create a new crawl job"""
    model = CrawlJob
    form_class = CrawlJobForm
    template_name = 'news/crawl_job_form.html'
    success_url = reverse_lazy('dashboard')

    def form_valid(self, form):
        response = super().form_valid(form)
        crawl_job = self.object

        messages.success(self.request, f'Crawl job #{crawl_job.id} created! Starting scraping...')

        # Run the crawl job in a background thread
        thread = threading.Thread(target=run_crawl_job, args=(crawl_job,))
        thread.daemon = True
        thread.start()

        return response


class CrawlJobDetailView(DetailView):
    """View details of a specific crawl job"""
    model = CrawlJob
    template_name = 'news/crawl_job_detail.html'
    context_object_name = 'job'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['articles'] = self.object.articles.all()
        return context


# ============= Article Review Views =============

class PendingArticlesView(ListView):
    """View all pending articles for review"""
    model = NewsArticle
    template_name = 'news/pending_articles.html'
    context_object_name = 'articles'
    paginate_by = 20

    def get_queryset(self):
        return NewsArticle.objects.filter(status='pending').order_by('-scraped_at')


class ApprovedArticlesView(ListView):
    """View all approved articles ready to publish"""
    model = NewsArticle
    template_name = 'news/approved_articles.html'
    context_object_name = 'articles'
    paginate_by = 20

    def get_queryset(self):
        return NewsArticle.objects.filter(status='approved').order_by('-reviewed_at')


@require_POST
def approve_article(request, pk):
    """Approve an article and auto-publish it"""
    article = get_object_or_404(NewsArticle, pk=pk)
    article.approve(auto_publish=True)
    messages.success(request, f'Article "{article.title[:50]}..." approved and published!')

    # Return JSON response for AJAX requests
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success', 'message': 'Article approved and published'})

    return redirect(request.META.get('HTTP_REFERER', 'pending_articles'))


@require_POST
def reject_article(request, pk):
    """Reject an article"""
    article = get_object_or_404(NewsArticle, pk=pk)
    article.reject()
    messages.warning(request, f'Article "{article.title[:50]}..." rejected.')

    # Return JSON response for AJAX requests
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success', 'message': 'Article rejected'})

    return redirect(request.META.get('HTTP_REFERER', 'pending_articles'))


@require_POST
def publish_article(request, pk):
    """Manually publish an approved article"""
    article = get_object_or_404(NewsArticle, pk=pk)
    article.publish()
    messages.success(request, f'Article "{article.title[:50]}..." published!')

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success', 'message': 'Article published'})

    return redirect(request.META.get('HTTP_REFERER', 'approved_articles'))


# ============= Manual Article Submission =============

class ManualArticleCreateView(CreateView):
    """Manually add a news article"""
    model = NewsArticle
    form_class = ManualArticleForm
    template_name = 'news/manual_article_form.html'
    success_url = reverse_lazy('pending_articles')

    def form_valid(self, form):
        messages.success(self.request, 'Article added successfully! It is now pending review.')
        return super().form_valid(form)


# ============= Public News Page =============

class PublicNewsListView(ListView):
    """Public-facing news page showing published articles"""
    model = NewsArticle
    template_name = 'news/public_news.html'
    context_object_name = 'articles'
    paginate_by = 10

    def get_queryset(self):
        queryset = NewsArticle.objects.filter(status='published').order_by('-published_at')

        # Optional filtering by country
        country = self.request.GET.get('country')
        if country:
            queryset = queryset.filter(country__icontains=country)

        # Optional search
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(summary__icontains=search) |
                Q(keywords_matched__icontains=search)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['countries'] = NewsArticle.objects.filter(
            status='published'
        ).values_list('country', flat=True).distinct()
        return context


class PublicNewsDetailView(DetailView):
    """Detailed view of a published article"""
    model = NewsArticle
    template_name = 'news/public_news_detail.html'
    context_object_name = 'article'

    def get_queryset(self):
        return NewsArticle.objects.filter(status='published')
