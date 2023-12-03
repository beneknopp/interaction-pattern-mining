import { Component, Input } from '@angular/core';

@Component({
  selector: 'app-model-edge',
  templateUrl: './model-edge.component.html',
  styleUrl: './model-edge.component.css'
})
export class ModelEdgeComponent {
  @Input() startX: number = 0;
  @Input() startY: number = 0;
  @Input() endX: number = 0;
  @Input() endY: number = 0;
}
