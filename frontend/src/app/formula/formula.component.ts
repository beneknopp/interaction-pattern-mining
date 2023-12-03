import { Component, ElementRef, Input, OnChanges, SimpleChanges } from '@angular/core';

declare var MathJax: any;

@Component({
  selector: 'app-formula',
  templateUrl: './formula.component.html',
  styleUrl: './formula.component.css'
})
export class FormulaComponent {
  @Input() expression: string = '';
  @Input() fontSize: number = 10;

  mathContent: string = '';

  constructor(private el: ElementRef) { }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes["expression"]) {
      this.updateMathContent();
    }
  }

  ngAfterViewInit(): void {
    this.updateMathContent();
  }

  private updateMathContent() {
    this.mathContent = this.expression;
    if (MathJax) {
      MathJax.typesetClear();
      MathJax.typesetPromise([this.el.nativeElement]).catch((err: any) => console.error(err));
    }
  }
}