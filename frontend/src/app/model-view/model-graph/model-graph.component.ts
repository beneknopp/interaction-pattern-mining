import { Component, ElementRef, Input, ViewChild } from '@angular/core';

@Component({
  selector: 'app-model-graph',
  templateUrl: './model-graph.component.html',
  styleUrls: ['./model-graph.component.css']
})
export class ModelGraphComponent {
  
  @Input() fontSize: number = 10;

  collapseContainer() {
    throw new Error('Method not implemented.');
  }
  expandContainer() {
    throw new Error('Method not implemented.');
  }

  @ViewChild('left') left: ElementRef | undefined;
  @ViewChild('right') right: ElementRef | undefined;

  @Input() leftContents: [number, string[]][] = []
  @Input() rightContents: string[] = []

}
