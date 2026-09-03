# apps/core/mixins.py
from django.urls import reverse_lazy

class SaveAndNextMixin:
    """
    Overrides get_success_url() on FormView / CreateView / UpdateView.
    If 'save_and_next' is submitted in POST, redirects to next_url_name.
    """
    next_url_name = None

    def get_success_url(self):
        if self.request.POST.get("save_and_next") == "true" and self.next_url_name:
            return reverse_lazy(self.next_url_name)
        return super().get_success_url()