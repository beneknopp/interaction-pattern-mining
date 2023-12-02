import { Component, Input, OnInit } from '@angular/core';
import { EventType, ObjectType } from '../dtos/utils';

@Component({
  selector: 'app-model-view',
  templateUrl: './model-view.component.html',
  styleUrls: ['./model-view.component.css']
})
export class ModelViewComponent implements OnInit {
  
  @Input() modelMined: boolean = false;
  @Input() eventTypes: EventType[] | undefined;
  @Input() objectTypes: {[eventType: EventType] : ObjectType[] } | undefined;
  
  modeledEventType: EventType | undefined;
  filteredObjectTypes: ObjectType[] | undefined;

  constructor() { }

  ngOnInit(): void {
  }

  onChangeModelFilterDropdown() {
    throw new Error('Method not implemented.');
  }

}
