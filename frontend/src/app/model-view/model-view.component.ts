import { Component, Input, OnInit } from '@angular/core';
import { EventType, ObjectType } from '../dtos/utils';
import { ApiService } from '../api.service';
import { ModelResponse } from '../dtos/model-response';

@Component({
  selector: 'app-model-view',
  templateUrl: './model-view.component.html',
  styleUrls: ['./model-view.component.css']
})
export class ModelViewComponent implements OnInit {

  @Input() sessionKey: string | undefined;
  @Input() modelMined: boolean = false
  @Input() eventTypes: EventType[] | undefined
  @Input() objectTypes: { [eventType: EventType]: ObjectType[] } | undefined

  modeledEventType: EventType | undefined;
  filteredObjectTypes: ObjectType[] | undefined
  cachedFilteredObjectTypes: ObjectType[] = []
  formulaFontSize: number = 10;
  modelResponse: ModelResponse | undefined;
  argument_ids: { [objectType: ObjectType]: string[] } = {};
  splitPatternIds: string[] = [];
  leftContents: [number, string[]][] = [];
  rightContents: string[] = [];

  constructor(private apiService: ApiService) { }

  ngOnInit(): void {
  }

  onChangeEventType() {
    this.filteredObjectTypes = []
  }

  onChangeObjectTypes() {
    if (!this.sessionKey) {
      return
    }
    if (!this.filteredObjectTypes || !this.modeledEventType) {
      return
    }
    if (JSON.stringify(this.cachedFilteredObjectTypes) == JSON.stringify(this.filteredObjectTypes)) {
      return
    }
    this.cachedFilteredObjectTypes = this.filteredObjectTypes
    this.apiService.getFilteredModel(this.sessionKey, this.splitPatternIds, this.modeledEventType, this.filteredObjectTypes)
      .subscribe((resp: ModelResponse) => {
        this.modelResponse = resp
        let partitions: any[] = []
        Object.entries(resp).forEach(([_, value]) => {partitions.push(value)})
        let patternNodeContents : [number, string[]][] = []
        partitions.forEach(partition => {
          patternNodeContents.push([partition.support, partition.pretty_pattern_ids])
        })
        this.leftContents = patternNodeContents
        if(this.filteredObjectTypes){
          this.rightContents = this.filteredObjectTypes
        }
      })
  }

  getEventTypes(): EventType[] {
    return this.eventTypes ? this.eventTypes : []
  }

  getEventTypeObjectTypes() {
    if (!this.objectTypes || !this.modeledEventType) {
      return []
    }
    return this.objectTypes[this.modeledEventType]
  }

}
