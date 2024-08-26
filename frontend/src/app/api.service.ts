import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { catchError, tap } from 'rxjs/operators';
import { EventType, ObjectType, PatternID } from './dtos/utils';
import { NotFoundError } from 'rxjs';
import { SearchPlans } from './dtos/search_plans';

@Injectable({
  providedIn: 'root'
})
export class ApiService {

  private backendUrl = 'http://localhost:5000/';
  httpOptions = {
    headers: new HttpHeaders({
      'Content-Type': 'application/json',
    })
  };

  constructor(
    private http: HttpClient
  ) { }

  postOCEL(formData: FormData) {
    return this.http.post<any>(this.backendUrl + 'upload-ocel', formData)
  }

  confirmEventTypes(session_key: string, selected_event_types: EventType[]) {
    const headers = new HttpHeaders({
      'Content-Type': 'application/json'
    });
    const body = JSON.stringify(selected_event_types);
    return this.http.post<any>(this.backendUrl + 'set-event-types?session-key=' + session_key, body, { headers })
  }

  loadTables(session_key: string) {
    return this.http.get<any>(this.backendUrl + '/load-tables?session-key=' + session_key)
  }

  loadSearchPlans(session_key: string, max_attr_labels: number) {
    return this.http.get<any>(this.backendUrl + '/search-plans?session-key=' + session_key 
      + '&max-attr-labels=' + max_attr_labels)
  }

  getPrefixesLookup(session_key: string){
    return this.http.get<any>(this.backendUrl + '/variable-prefixes-lookup?session-key=' + session_key)
  }

  registerCustomPattern(session_key: string, editedEventType: string, customPatternDescription: string) {
    const headers = new HttpHeaders({
      'Content-Type': 'application/json'
    });
    let body_content = {
      "event_type": editedEventType,
      "pattern_id": customPatternDescription
    }
    const body = JSON.stringify(body_content);
    return this.http.post<any>(this.backendUrl + 'register-custom-pattern?session-key=' + session_key, body, { headers })
  }
  
  startSearchRules(session_key: string, target_pattern_description: string, max_rule_ante_length: number, min_rule_ante_support: number, complementary_mode: boolean, merge_mode: boolean,
    search_plans: SearchPlans | undefined
  ) {
    const headers = new HttpHeaders({
      'Content-Type': 'application/json'
    });
    let body_content = {
      "selected-patterns": search_plans
    }
    const body = JSON.stringify(body_content);
    return this.http.post<any>(this.backendUrl + '/search-rules?session-key=' + session_key +
      '&complementary-mode=' + complementary_mode +
      '&merge-mode=' + merge_mode + 
      '&target-pattern-description=' + target_pattern_description +
      '&max-rule-ante-length=' + max_rule_ante_length +
      '&min-rule-ante-support=' + min_rule_ante_support,
    body, {headers})
  }

  getFilteredModel(session_key:string, event_type: EventType, object_types: ObjectType[]) {
    const headers = new HttpHeaders({
      'Content-Type': 'application/json'
    });
    let body_content = {
      "event-type": event_type,
      "object-types": object_types,
    }
    const body = JSON.stringify(body_content);
    return this.http.post<any>(this.backendUrl + 'get-model?session-key=' + session_key, body, { headers })
  }

  downloadRules(session_key: string) {
    return this.http.get(
      this.backendUrl + '/download-rules?session-key=' + session_key, {
      responseType: 'arraybuffer'
    });
  }


}
