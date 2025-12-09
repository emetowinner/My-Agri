from django import forms
from .models import CrawlJob, NewsArticle


class CrawlJobForm(forms.ModelForm):
    """Form for creating a new crawl job"""

    class Meta:
        model = CrawlJob
        fields = ['keywords', 'country']
        widgets = {
            'keywords': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter keywords (comma-separated): e.g., agriculture, farming, crops'
            }),
            'country': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Nigeria, Ghana, Kenya'
            }),
        }
        help_texts = {
            'keywords': 'Enter search keywords separated by commas',
            'country': 'Enter the country to filter news from'
        }


class ManualArticleForm(forms.ModelForm):
    """Form for manually adding a news article"""

    class Meta:
        model = NewsArticle
        fields = ['title', 'url', 'summary', 'source_name', 'country', 'keywords_matched']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Article title'
            }),
            'url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://example.com/article'
            }),
            'summary': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 8,
                'placeholder': 'Enter a 3-paragraph summary of the article...'
            }),
            'source_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., BBC News, CNN'
            }),
            'country': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Nigeria'
            }),
            'keywords_matched': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., agriculture, technology'
            }),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.is_manual = True
        instance.status = 'pending'  # Manual articles also need review
        if commit:
            instance.save()
        return instance
