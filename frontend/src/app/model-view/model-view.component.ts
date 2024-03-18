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
  @Input() allPatterns: { [eventType: EventType]: string[] } = {};

  modeledEventType: EventType | undefined;
  filteredObjectTypes: ObjectType[] = [];
  cachedFilteredObjectTypes: ObjectType[] = []
  splitResponse: SplitResponse | undefined;
  argument_ids: { [objectType: ObjectType]: string[] } = {};
  // for each split, a tuple of support-pattern-set-pairs and object types
  partitions: [[number, string[]][], string[]][] = [];
  antecedent_formulas: string[][] = [];
  formulaFontSize: number = 14;
  splitPatterns: string[] = [];
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
    debugger
    if (!this.sessionKey) {
      return
    }
    if (!this.modeledEventType) {
      return
    }
    this.cachedFilteredObjectTypes = this.filteredObjectTypes
    this.apiService.getFilteredModel(this.sessionKey, this.splitPatterns, this.modeledEventType, this.filteredObjectTypes)
      .subscribe((resp: SplitResponse) => {
        this.splitResponse = resp
        let partitions: [[number, string[]][], string[]][] = []
        let antecedent_formulas: string[][] = []
        Object.values(resp).forEach((partitionResponse: PartitionResponse) => {
          antecedent_formulas.push(partitionResponse.pretty_antecedent_ids)

          let model_responses = partitionResponse.model_responses
          let patternNodeContents: [number, string[]][] = []
          Object.values(model_responses).forEach((model_response: ModelResponse) => {
            let support = model_response.support
            let pretty_pattern_ids = model_response.pretty_pattern_ids
            let patternNodeContent: [number, string[]] = [support, pretty_pattern_ids]
            if (this.filteredObjectTypes) {
              patternNodeContents.push(patternNodeContent)
            }
          })
          if (this.filteredObjectTypes) {
            let partition: [[number, string[]][], string[]] = [
              patternNodeContents, this.filteredObjectTypes
            ]
            partitions.push(partition)
          }
        })
        this.antecedent_formulas = antecedent_formulas
        this.partitions = partitions
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
