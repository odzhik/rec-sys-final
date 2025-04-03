import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, of } from 'rxjs';
import { catchError, tap } from 'rxjs/operators';
import { AuthService } from './auth.service';

@Injectable({
  providedIn: 'root'
})
export class RecommendationService {
  private apiUrl = '/api/recommendation'; // Proxy to recommendation service

  constructor(
    private http: HttpClient,
    private authService: AuthService
  ) {}

  /**
   * Record a click on an event
   */
  recordClick(eventId: number): Observable<any> {
    const userId = this.getCurrentUserId();
    return this.http.post(`${this.apiUrl}/click`, {
      user_id: userId,
      event_id: eventId
    }).pipe(
      catchError(error => {
        console.error('Error recording click:', error);
        return of({ status: 'error' }); // Return a safe observable
      })
    );
  }

  /**
   * Record a view with duration
   */
  recordView(eventId: number, viewDuration: number): Observable<any> {
    const userId = this.getCurrentUserId();
    return this.http.post(`${this.apiUrl}/view`, {
      user_id: userId,
      event_id: eventId,
      view_duration: viewDuration
    }).pipe(
      catchError(error => {
        console.error('Error recording view:', error);
        return of({ status: 'error' }); // Return a safe observable
      })
    );
  }

  /**
   * Get recommended events for the current user
   */
  getRecommendations(limit: number = 5): Observable<any[]> {
    const userId = this.getCurrentUserId();
    let url = `${this.apiUrl}/recommendations?limit=${limit}`;
    
    if (userId) {
      url += `&user_id=${userId}`;
    }
    
    return this.http.get<any[]>(url).pipe(
      catchError(error => {
        console.error('Error fetching recommendations:', error);
        return of([]); // Return empty array as fallback
      })
    );
  }

  /**
   * Get the current user ID if logged in
   */
  private getCurrentUserId(): number | null {
    // Try to get user from auth service
    if (this.authService.isAuthenticated()) {
      const userData = this.authService.getUserData();
      return userData?.id || null;
    }
    return null;
  }
} 