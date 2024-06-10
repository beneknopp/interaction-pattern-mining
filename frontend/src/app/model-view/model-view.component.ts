import { Component, Input, OnInit, OnChanges, SimpleChanges } from '@angular/core';
import { EventType, ObjectType } from '../dtos/utils';
import { ApiService } from '../api.service';
import { ModelEvaluation, ModelResponse, PartitionResponse, SplitResponse } from '../dtos/model-response';

@Component({
  selector: 'app-model-view',
  templateUrl: './model-view.component.html',
  styleUrls: ['./model-view.component.css']
})
export class ModelViewComponent implements OnInit, OnChanges {

  @Input() sessionKey: string | undefined;
  @Input() modelMined: boolean = false
  @Input() eventTypes: EventType[] | undefined
  @Input() objectTypes: { [eventType: EventType]: ObjectType[] } | undefined
  @Input() modelEvaluations: { [eventType: EventType]: ModelEvaluation } | undefined;

  modeledEventType: EventType | undefined;
  filteredObjectTypes: ObjectType[] = [];
  cachedFilteredObjectTypes: ObjectType[] = []
  antecedent_formulas: string[][] = [];
  formulaFontSize: number = 14;
  modelResponse: ModelResponse | undefined;
  partitionContents:    [number, string[]][] = [];
  validPatternsContent: [number, string[]][] = [];
  recall: number = -1;
  precision: number = -1;
  discrimination: number = -1;
  simplicity: number = -1;

  constructor(private apiService: ApiService) { }

  ngOnInit(): void {
  }

  onChangeEventType() {
    this.filteredObjectTypes = []
  }

  ngOnChanges(changes: SimpleChanges) {
    this.onChangeConfig()
  }

  onChangeConfig() {
    if (!this.sessionKey) {
      return
    }
    if (!this.modeledEventType) {
      return
    }
    this.cachedFilteredObjectTypes = this.filteredObjectTypes
    this.apiService.getFilteredModel(this.sessionKey, this.modeledEventType, this.filteredObjectTypes)
      .subscribe((resp: ModelResponse) => {
        debugger
        this.modelResponse = resp
        let partitions: PartitionResponse[] = []
        this.validPatternsContent = [[
          resp.valid_patterns.support,
          resp.valid_patterns.pretty_pattern_ids
        ]]
        Object.entries(resp.partitions).forEach(([key, value]) => {partitions.push(value)})
        let patternNodeContents: [number, string[]][] = []
        partitions.forEach(partition => {
          patternNodeContents.push([
            partition.support,
            partition.pretty_pattern_ids
          ])
        })
        this.partitionContents = patternNodeContents
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
