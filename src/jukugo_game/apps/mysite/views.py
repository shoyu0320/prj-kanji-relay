from django.urls import reverse_lazy

# Create your views here.
from django.views.generic import CreateView, DetailView, ListView, TemplateView

from .forms import RegisterForm
from .models import Register


class IndexView(TemplateView):
    template_name = "register/index.html"
    context_object_name = "user"


class RegisterCreateView(CreateView):
    template_name = "register/register.html"
    form_class = RegisterForm
    model = Register
    success_url = reverse_lazy("register:register_complete")
    context_object_name = "user"


class RegisterCreateCompleteView(TemplateView):
    template_name = "register/register_complete.html"
    model = Register
    context_object_name = "users"


class RegisterListView(ListView):
    template_name = "register/register_history.html"
    model = Register
    context_object_name = "users"


class RegisterDetailView(DetailView):
    template_name = "register/register_detail.html"
    model = Register
    context_object_name = "user"
