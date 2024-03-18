import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { catchError, tap } from 'rxjs/operators';
import { EventType, ObjectType } from './dtos/utils';

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

  loadSearchPlans(session_key: string) {
    return this.http.get<any>(this.backendUrl + '/search-plans?session-key=' + session_key)
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

  startSearch(session_key: string, min_support:number, complementary_mode: boolean, merge_mode: boolean) {
    return this.http.get<any>(this.backendUrl + '/search?session-key=' + session_key +
      '&complementary-mode=' + complementary_mode +
      '&merge-mode=' + merge_mode + 
      '&min-support=' + min_support)
  }

  getFilteredModel(session_key:string, split_pattern_ids: string[], event_type: EventType, object_types: ObjectType[]) {
    const headers = new HttpHeaders({
      'Content-Type': 'application/json'
    });
    let body_content = {
      "event-type": event_type,
      "object-types": object_types,
      "split-pattern-ids": split_pattern_ids
    }
    const body = JSON.stringify(body_content);
    return this.http.post<any>(this.backendUrl + 'get-model?session-key=' + session_key, body, { headers })
  }

}
