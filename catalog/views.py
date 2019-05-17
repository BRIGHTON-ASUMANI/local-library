import datetime
from django.views import generic
from django.shortcuts import render
from catalog.models import Book, Author, BookInstance, Genre
from django.shortcuts import get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.decorators import permission_required, login_required

from catalog.forms import RenewBookForm


def index(request):
    """View function for home page of site."""
    num_books = Book.objects.all().count()
    num_instances = BookInstance.objects.all().count()
    num_instances_available = BookInstance.objects.filter(status__exact='a').count()
    num_authors = Author.objects.count()

    num_visits = request.session.get('num_visits', 0)
    request.session['num_visits'] = num_visits + 1
    
    context = {
        'num_books': num_books,
        'num_instances': num_instances,
        'num_instances_available': num_instances_available,
        'num_authors': num_authors,
        'num_visits': num_visits,
    }

    return render(request, 'index.html', context=context)


class BookListView(LoginRequiredMixin, generic.ListView):
    model = Book
    login_url = 'accounts/login/'
    template_name = 'book_list.html'
    redirect_field_name = 'index/'

    def get_queryset(self):
        return Book.objects.filter(title__icontains='war')[:5] 

    def get_context_data(self, **kwargs):
        context = super(BookListView, self).get_context_data(**kwargs)
        context['some_data'] = 'This is just some data'
        return context

class BookDetailView(LoginRequiredMixin, generic.DetailView):
    model = Book
    paginate_by = 10

    def book_detail_view(request, primary_key):
        book = get_object_or_404(Book, pk=primary_key)
        return render(request, 'book_detail.html', context={'book': book})


class AuthorListView(LoginRequiredMixin, generic.ListView):
    model = Author  
    template_name = 'author_list.html'

    def get_queryset(self):
        return Author.objects.filter(last_name__icontains='war')[:5] 

    def get_context_data(self, **kwargs):
        context = super(AuthorListView, self).get_context_data(**kwargs)
        context['some_data'] = 'This is just some data'
        return context



class AuthorDetailView(generic.DetailView):
    model = Author
    paginate_by = 10

    def book_detail_view(request, primary_key):
        author = get_object_or_404(Author, pk=primary_key)
        return render(request, 'author_detail.html', context={'author': author})

class LoanedBooksByUserListView(LoginRequiredMixin,generic.ListView):
    """Generic class-based view listing books on loan to current user."""
    model = BookInstance
    template_name ='bookinstance_list_borrowed_user.html'
    paginate_by = 10
    
    def get_queryset(self):
        return BookInstance.objects.filter(borrower=self.request.user).filter(status__exact='o').order_by('due_back')


@permission_required('catalog.can_mark_returned')
def renew_book_librarian(request, pk):
    """View function for renewing a specific BookInstance by librarian."""
    book_instance = get_object_or_404(BookInstance, pk=pk)
    if request.method == 'POST':
        form = RenewBookForm(request.POST)
        if form.is_valid():
            book_instance.due_back = form.cleaned_data['renewal_date']
            book_instance.save()
            return HttpResponseRedirect(reverse('all-borrowed') )
    else:
        proposed_renewal_date = datetime.date.today() + datetime.timedelta(weeks=3)
        form = RenewBookForm(initial={'renewal_date': proposed_renewal_date})

    context = {
        'form': form,
        'book_instance': book_instance,
    }
    return render(request, 'book_renew_librarian.html', context)