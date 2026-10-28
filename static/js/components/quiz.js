/**
 * Composant Alpine `quiz` : quiz chronométré à choix multiples.
 *
 * Usage : x-data="quiz('<id du <script type=application/json>>', '<url de sauvegarde>')"
 */
document.addEventListener('alpine:init', () => {
  const getCookie = (name) =>
    document.cookie
      .split('; ')
      .find((row) => row.startsWith(`${name}=`))
      ?.split('=')[1] ?? '';

  Alpine.data('quiz', (sourceId, saveUrl) => ({
    state: 'start',
    questions: JSON.parse(document.getElementById(sourceId).textContent),
    currentIdx: 0,
    score: 0,
    timeLeft: 0,
    timePercent: 100,
    timerInterval: null,
    selected: null,

    get currentQuestion() {
      return this.questions[this.currentIdx];
    },

    startQuiz() {
      this.currentIdx = 0;
      this.score = 0;
      this.loadQuestion();
    },

    loadQuestion() {
      this.selected = null;
      this.state = 'playing';
      this.timeLeft = this.currentQuestion.duration;
      this.timePercent = 100;
      clearInterval(this.timerInterval);
      this.timerInterval = setInterval(() => {
        this.timeLeft--;
        this.timePercent = (this.timeLeft / this.currentQuestion.duration) * 100;
        if (this.timeLeft <= 0) this.handleTimeUp();
      }, 1000);
    },

    handleTimeUp() {
      clearInterval(this.timerInterval);
      this.state = 'time_up';
    },

    submitAnswer(key) {
      clearInterval(this.timerInterval);
      this.selected = key;
      this.state = 'feedback';
      if (key === this.currentQuestion.correct) this.score++;
    },

    revealAnswer() {
      this.state = 'feedback';
    },

    skipQuestion() {
      this.nextStep();
    },

    nextStep() {
      if (this.currentIdx < this.questions.length - 1) {
        this.currentIdx++;
        this.loadQuestion();
      } else {
        this.finishGame();
      }
    },

    finishGame() {
      this.state = 'end';
      fetch(saveUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
        body: JSON.stringify({ score: this.score, total: this.questions.length }),
      });
    },

    resetGame() {
      this.state = 'start';
    },
  }));
});
