import { Component, Input } from '@angular/core';

@Component({
  selector: 'app-object-type-node',
  templateUrl: './object-type-node.component.html',
  styleUrl: './object-type-node.component.css'
})
export class ObjectTypeNodeComponent {
  @Input() objectType: string = '';
}
