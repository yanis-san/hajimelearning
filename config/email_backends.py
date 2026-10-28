"""
Backend e-mail pour le développement.

Identique au ConsoleEmailBackend, mais décode le quoted-printable
pour que les URLs soient copiables directement depuis le terminal.
"""

import quopri

from django.core.mail.backends.console import EmailBackend as ConsoleBackend


class DecodedConsoleEmailBackend(ConsoleBackend):
    """Affiche les e-mails dans la console avec le body décodé (pas de =\\n)."""

    def write_message(self, message):
        self.stream.write("-" * 60)
        self.stream.write("\n")
        self.stream.write(f"Sujet : {message.subject}\n")
        self.stream.write(f"De : {message.from_email}\n")
        self.stream.write(f"À : {', '.join(message.to)}\n")
        self.stream.write("-" * 60)
        self.stream.write("\n")

        body = message.body or ""
        # Tenter de décoder le quoted-printable si nécessaire
        try:
            decoded = quopri.decodestring(body.encode("utf-8")).decode("utf-8")
        except Exception:
            decoded = body

        self.stream.write(decoded)
        self.stream.write("\n")
        self.stream.write("-" * 60)
        self.stream.write("\n\n")

    def send_messages(self, email_messages):
        if not email_messages:
            return 0
        msg_count = 0
        for message in email_messages:
            self.write_message(message)
            msg_count += 1
        return msg_count
