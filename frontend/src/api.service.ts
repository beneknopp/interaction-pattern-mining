import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { catchError, tap } from 'rxjs/operators';
import { EventType } from './dtos/utils';

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
    return this.http.post<any>(this.backendUrl + 'set-event-types?sessionKey=' + session_key, body, { headers })
  }

  loadTables(session_key: string) {
    return this.http.get<any>(this.backendUrl + '/load-tables?sessionKey=' + session_key)
  }

  loadSearchPlans(session_key: string) {
    return this.http.get<any>(this.backendUrl + '/search-plans?sessionKey=' + session_key)
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
    return this.http.post<any>(this.backendUrl + 'register-custom-pattern?sessionKey=' + session_key, body, { headers })
  }

  startSearch(session_key: string, complementary_mode: boolean, merge_mode: boolean) {
    return this.http.get<any>(this.backendUrl + '/search?sessionKey=' + session_key +
      '&complementaryMode=' + complementary_mode +
      '&mergeMode=' + merge_mode)
  }

}
