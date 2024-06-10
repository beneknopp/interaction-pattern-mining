import { Component } from '@angular/core';
import { ApiService } from './api.service';
import { UploadResponse } from './dtos/upload-response';
import { PatternType, SearchPlans } from './dtos/search_plans';
import { EventType, ObjectType, PatternID } from './dtos/utils';
import { ModelEvaluation } from './dtos/model-response';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent {

  title = 'ox-miner'
  logUploaded = false
  sessionKey: string | undefined = undefined
  searchPlansLoaded = false;
  tablesLoaded = false;
  complementaryMode = false;
  mergeMode = false;
  searchComplete = false;
  targetPatternDescription: string = "";
  maxRuleAnteLength: number = 1;
  minRuleAnteSupport: number = 0;
  eventTypes: EventType[] = [];
  filteredEventTypes: EventType[] = [];
  selectedEventTypes: EventType[] = [];
  eventTypesConfirmed: boolean = false;
  searchPlans: SearchPlans | undefined;
  filteredSearchPlans: SearchPlans | undefined;
  editedEventType: EventType | undefined;
  editedPatternType: PatternType | undefined;
  editedObjectType: ObjectType | undefined;
  uploadResponse: UploadResponse | undefined;
  selectedPatterns: PatternID[] = [];
  customPatternDescription: PatternID = "";
  modelMined = false;
  allPatterns: { [eventType: EventType]: string[] } = {};
  modelEvaluations: { [eventType: EventType]: ModelEvaluation} = {}
  minSupport: number = 0;

  constructor(
    private apiService: ApiService
  ) { }

  onSelectionChange($event: Event) {
    console.log($event)
  }

  onFileSelected(event: any) {
    const file: File = event.target.files[0];
    if (file) {
      const formData = new FormData();
      formData.append("file", file);
      const upload$ = this.apiService.postOCEL(formData).subscribe((resp: UploadResponse) => {
        this.logUploaded = true
        this.eventTypesConfirmed = false
        this.sessionKey = resp.session_key
        this.uploadResponse = resp
        this.eventTypes = resp.event_types
        this.selectedEventTypes = resp.event_types
      });
    }
  }

  onConfirmEventTypes() {
    if (!this.sessionKey) {
      return
    }
    const upload$ = this.apiService.confirmEventTypes(this.sessionKey, this.filteredEventTypes).subscribe((resp: SearchPlans) => {
      this.searchPlans = JSON.parse(JSON.stringify(resp));
      this.filteredSearchPlans = JSON.parse(JSON.stringify(resp));
      this.eventTypesConfirmed = true
      this.selectedEventTypes = this.filteredEventTypes
      this.editedEventType = this.selectedEventTypes[0]
    })
  }

  loadSearchPlans() {
    if (!this.sessionKey) {
      return
    }
    this.apiService.loadSearchPlans(this.sessionKey).subscribe((resp: SearchPlans) => {
      this.searchPlans = JSON.parse(JSON.stringify(resp))
      this.filteredSearchPlans = JSON.parse(JSON.stringify(resp))
      this.searchPlansLoaded = true
    })
  }

  isObjectTypeSelectionDisabled(): boolean {
    return !this.eventTypesConfirmed || !(this.editedPatternType == PatternType.Interaction)
  }

  getEditedObjectTypeOptions(): ObjectType[] {
    if (!this.uploadResponse || !this.editedEventType || !(this.editedPatternType == PatternType.Interaction)) {
      return []
    }
    return this.uploadResponse.event_type_object_types[this.editedEventType]
  }

  onChangePatternEditDropdown() {
    let event_type = this.editedEventType
    let pattern_type = this.editedPatternType
    let object_type = this.editedObjectType
    if (!this.filteredSearchPlans || !event_type || !pattern_type) {
      return
    }
    if (pattern_type == PatternType.Interaction) {
      if (!object_type) {
        return
      }
      this.selectedPatterns = this.filteredSearchPlans.patterns[event_type][PatternType.Interaction][object_type]
      return
    }
    this.selectedPatterns = this.filteredSearchPlans.patterns[event_type][pattern_type]
  }

  getPatternOptions() {
    let event_type = this.editedEventType
    let pattern_type = this.editedPatternType
    if (!this.searchPlans || !event_type || !pattern_type) {
      return []
    }
    if (pattern_type == PatternType.Interaction) {
      let object_type = this.editedObjectType
      if (!object_type) {
        return []
      }
      return this.searchPlans.patterns[event_type][pattern_type][object_type]
    }
    return this.searchPlans.patterns[event_type][pattern_type]
  }

  onChangeSelectedPatterns() {
    let event_type = this.editedEventType
    let pattern_type = this.editedPatternType
    if (!this.filteredSearchPlans || !event_type || !pattern_type) {
      return
    }
    if (pattern_type == PatternType.Interaction) {
      let object_type = this.editedObjectType
      if (!object_type) {
        return
      }
      this.filteredSearchPlans.patterns[event_type][pattern_type][object_type] = this.selectedPatterns
      return
    }
    this.filteredSearchPlans.patterns[event_type][pattern_type] = this.selectedPatterns
  }

  onConfirmCustomPattern() {
    let event_type = this.editedEventType
    if (!event_type || !this.sessionKey || !this.searchPlans) {
      return
    }
    let pattern_id = this.customPatternDescription
    this.apiService.registerCustomPattern(this.sessionKey, event_type, pattern_id)
      .subscribe((resp: any) => {
        console.log(resp)
        if (resp["resp"]) {
          let search_plans = this.searchPlans
          let filtered_search_plans = this.filteredSearchPlans
          if (filtered_search_plans && search_plans && event_type) {
            let custom_patterns_filtered = filtered_search_plans.patterns[event_type][PatternType.Custom]
            let customer_patterns = search_plans.patterns[event_type][PatternType.Custom]
            if (!custom_patterns_filtered.includes(pattern_id)) {
              custom_patterns_filtered.push(pattern_id)
            }
            if (!customer_patterns.includes(pattern_id)) {
              customer_patterns.push(pattern_id)
            }
            this.editedPatternType = PatternType.Custom
            this.onChangePatternEditDropdown()
            this.onChangeSelectedPatterns()
          }
        }
      })
  }

  loadTables() {
    if (!this.sessionKey) {
      return
    }
    this.apiService.loadTables(this.sessionKey).subscribe((resp: any) => {
      console.log(resp)
      this.tablesLoaded = true
    })
  }

  startSearchModel() {
    if (!this.sessionKey) {
      return
    }
    this.modelMined = false
    this.apiService.startSearchModel(this.sessionKey, this.minSupport, this.complementaryMode, this.mergeMode,
      this.filteredSearchPlans
    ).subscribe(
      (resp: {model_evaluations: {[eventType: EventType]: ModelEvaluation},
      all_patterns: {[eventType: EventType]: string[]}} ) => {
      this.modelEvaluations = resp.model_evaluations
      this.allPatterns = resp.all_patterns
      this.modelMined = true
    })
  }

  startSearchRules() {
    if (!this.sessionKey) {
      return
    }
    this.modelMined = false
    this.apiService.startSearchRules(
      this.sessionKey, 
      this.targetPatternDescription,
      this.maxRuleAnteLength,
      this.minRuleAnteSupport,
      this.complementaryMode, 
      this.mergeMode,
      this.filteredSearchPlans
    ).subscribe(
      (resp: {model_evaluations: {[eventType: EventType]: ModelEvaluation},
      all_patterns: {[eventType: EventType]: string[]}} ) => {
      this.modelEvaluations = resp.model_evaluations
      this.allPatterns = resp.all_patterns
      this.modelMined = true
    })
  }

}

