from django.urls import reverse_lazy
from django.views.generic import FormView, TemplateView

from config import throttle
from notifications.tasks import dispatch_email

from .forms import ContactForm
from .models import ContactReason


class ContactView(FormView):
    template_name = 'contact/contact.html'
    form_class = ContactForm
    success_url = reverse_lazy('contact_success')

    def get_initial(self):
        """Pré-remplit les champs si l'utilisateur est connecté."""
        initial = super().get_initial()
        user = self.request.user
        if user.is_authenticated:
            initial['first_name'] = user.first_name
            initial['last_name'] = user.last_name
            initial['email'] = user.email

        reason_label = self.request.GET.get('reason')
        if reason_label:
            # Recherche insensible à la casse parmi les motifs existants (jamais de création via GET)
            reason = ContactReason.objects.filter(label__iexact=reason_label, is_active=True).first()
            if reason:
                initial['reason'] = reason.id

        return initial

    def form_valid(self, form):
        if not throttle.allow(self.request, 'contact', limit=5, window=3600):
            form.add_error(None, "Trop de messages envoyés. Réessayez dans une heure.")
            return self.form_invalid(form)

        user = self.request.user if self.request.user.is_authenticated else None
        msg = form.save(commit=False)
        msg.user = user
        msg.save()

        # E-mail à l'équipe (Reply-To = expéditeur) + accusé de réception à l'expéditeur
        dispatch_email('contact_message', msg.pk)
        dispatch_email('contact_receipt', msg.pk)
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['is_prefilled'] = self.request.user.is_authenticated
        return ctx


class ContactSuccessView(TemplateView):
    template_name = 'contact/success.html'
