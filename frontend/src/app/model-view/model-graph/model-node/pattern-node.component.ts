import { Component, Input } from "@angular/core";

@Component({
    selector: 'app-pattern-node',
    templateUrl: './pattern-node.component.html',
    styleUrl: './pattern-node.component.css'
  })
  export class PatternNodeComponent {
    @Input() support: number = 0;
    @Input() showSupport: boolean = true;
    @Input() patternTeXs : string[] = [];
    @Input() fontSize: number = 10;

    ngOnInit() {
    }
  }