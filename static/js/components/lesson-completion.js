/**
 * Composant Alpine `lessonCompletion` : joue le son de complétion du cours (s'il existe)
 * avant d'envoyer le formulaire « Marquer comme terminée ».
 *
 * Usage : x-data="lessonCompletion('<url du son ou vide>')"
 */
document.addEventListener('alpine:init', () => {
  Alpine.data('lessonCompletion', (soundUrl) => ({
    playAndSubmit(event) {
      if (!soundUrl) return;
      event.preventDefault();
      const audio = new Audio(soundUrl);
      audio.volume = 0.5;
      audio.play().catch(() => {});
      setTimeout(() => event.target.closest('form').submit(), 600);
    },
  }));
});
