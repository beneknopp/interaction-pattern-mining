import { Component, ElementRef, Input, ViewChild } from '@angular/core';
import { ObjectTypeNodeComponent } from "./model-node/object-type-node.component";
import { PatternNodeComponent } from './model-node/pattern-node.component';

@Component({
  selector: 'app-model-graph',
  templateUrl: './model-graph.component.html',
  styleUrls: ['./model-graph.component.css']
})
export class ModelGraphComponent {

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

  getLeftNodeCenterX(index: number) {
    if (this.left) {
      const leftNode = this.left.nativeElement.children[index];
      return leftNode.offsetLeft + leftNode.offsetWidth / 2;
    }
  }

  getLeftNodeCenterY(index: number) {
    if (this.left) {
      const leftNode = this.left.nativeElement.children[index];
      return leftNode.offsetTop + leftNode.offsetHeight / 2;
    }
  }

  getRightNodeCenterX(index: number) {
    if (this.right) {
      const rightNode = this.right.nativeElement.children[index];
      return rightNode.offsetLeft + rightNode.offsetWidth / 2;
    }
  }

  getRightNodeCenterY(index: number) {
    if (this.right) {
      const rightNode = this.right.nativeElement.children[index];;
      return rightNode.offsetTop + rightNode.offsetHeight / 2;
    }
  }

}
