from django.views.generic import FormView, TemplateView
from django.urls import reverse_lazy
from django.core.mail import send_mail
from django.conf import settings

from .forms import ContactForm
from .models import ContactMessage


class ContactView(FormView):
    template_name = 'contact/contact.html'
    form_class    = ContactForm
    success_url   = reverse_lazy('contact_success')

    def get_initial(self):
        """Pré-remplit les champs si l'utilisateur est connecté."""
        initial = super().get_initial()
        user = self.request.user
        if user.is_authenticated:
            initial['first_name'] = user.first_name
            initial['last_name']  = user.last_name
            initial['email']      = user.email
            
        reason_label = self.request.GET.get('reason')
        if reason_label:
            from .models import ContactReason
            # On cherche de manière insensible à la casse
            reason = ContactReason.objects.filter(label__iexact=reason_label).first()
            if not reason:
                # Création automatique du motif pour éviter les erreurs
                reason = ContactReason.objects.create(label=reason_label, order=10, is_active=True)
            initial['reason'] = reason.id
            
        return initial

    def form_valid(self, form):
        user = self.request.user if self.request.user.is_authenticated else None
        msg  = form.save(commit=False)
        msg.user = user
        msg.save()

        # Notification email (console en dev, SMTP en prod)
        subject = f"[Hajime Learning] Contact : {msg.reason or 'Sans motif'}"
        body = (
            f"De : {msg.first_name} {msg.last_name} <{msg.email}>\n"
            f"Motif : {msg.reason or '-'}\n\n"
            f"{msg.message}"
        )
        send_mail(
            subject,
            body,
            settings.DEFAULT_FROM_EMAIL,
            [settings.CONTACT_EMAIL],
            fail_silently=True,
        )
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['is_prefilled'] = self.request.user.is_authenticated
        return ctx


class ContactSuccessView(TemplateView):
    template_name = 'contact/success.html'
