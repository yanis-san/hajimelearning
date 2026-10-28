/**
 * Composant Alpine `autoplayVideo` : lecture automatique de la vidéo (x-ref="video")
 * quand elle entre dans le viewport, pause quand elle en sort, bascule muet/son.
 *
 * Usage : x-data="autoplayVideo" x-init="observe()"
 */
document.addEventListener('alpine:init', () => {
  Alpine.data('autoplayVideo', () => ({
    isMuted: true,

    observe() {
      if (!('IntersectionObserver' in window)) return;
      const observer = new IntersectionObserver(
        ([entry]) => {
          if (entry.isIntersecting) {
            this.$refs.video.play().catch(() => {});
          } else {
            this.$refs.video.pause();
          }
        },
        { threshold: 0.2 },
      );
      observer.observe(this.$el);
    },

    toggleMute() {
      this.isMuted = !this.isMuted;
      this.$refs.video.muted = this.isMuted;
    },
  }));
});
