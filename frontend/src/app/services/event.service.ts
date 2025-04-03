import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class EventService {
  private apiUrl = '/api/events'; // Используем относительный путь для работы с nginx proxy

  constructor(private http: HttpClient) {}

  getAllEvents(): Observable<any[]> {
    return this.http.get<any[]>(this.apiUrl);
  }

  getEventById(eventId: number): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/${eventId}`);
  }  
}
