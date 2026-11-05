import { button, element } from '../ui/dom';
import type { Command } from '../ui/dom';
import { GameFrame, record, values } from './GameView';
import type { GameView } from './GameView';
import type { RoomArtwork } from '../ui/RoomArtwork';

export class QuizView extends GameFrame implements GameView {
  private question = element('h3');
  private answers = element('div', 'quiz-answers');
  private explanation = element('p', 'quiz-explanation');
  private nextButton = button('Weiter', () => this.action('next'));
  constructor(command: Command, art: RoomArtwork) {
    super(command);
    this.element.dataset.game = 'quiz';
    const stage = element('div', 'quiz-stage');
    stage.style.backgroundImage = `url("${art.game('quiz-stage')}")`;
    stage.append(art.image(art.game('quiz-emblem'), 'Aikos Quiz'), this.question);
    this.content.append(stage, this.answers, this.explanation, this.nextButton);
    this.answers.style.setProperty(
      '--quiz-answer',
      `url("${art.surface('button_normal.quiz_answer')}")`,
    );
  }
  update(data: Record<string, unknown>): void {
    this.score.textContent = `Frage ${Number(data.index ?? 0) + 1} von 10 · ${data.score ?? 0} richtig`;
    this.question.textContent = String(data.question ?? '');
    this.answers.replaceChildren();
    for (const raw of values(data.answers)) {
      const answer = record(raw),
        control = button(String(answer.text), () => this.action('answer', answer.id));
      control.disabled = !!data.busy || data.selected !== null;
      control.classList.toggle('correct', data.correct === answer.id);
      control.classList.toggle('chosen', data.selected === answer.id);
      this.answers.append(control);
    }
    this.explanation.textContent = String(data.explanation ?? '');
    this.nextButton.hidden = !data.revealed;
    this.nextButton.disabled = !!data.busy;
    this.nextButton.textContent = data.finished ? 'Neue Fragerunde' : 'Weiter';
  }
}
