from django.views.generic import TemplateView
from library.models import Library, Book, Genre, Member, Loan

class ShowLibraryView(TemplateView):
    template_name = "library/show_library.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["libraries"] = Library.objects.all()
        context["books"] = Book.objects.all().select_related("genre", "library")
        context["genres"] = Genre.objects.all()
        context["members"] = Member.objects.all().select_related("user", "library")
        context["loans"] = Loan.objects.all().select_related("book", "member", "user")
        return context
