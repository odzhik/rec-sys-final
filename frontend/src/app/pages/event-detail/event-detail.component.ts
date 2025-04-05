import { Component, OnInit, OnDestroy } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { RecommendationService } from '../../services/recommendation.service';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-event-detail',
  standalone: true,
  templateUrl: './event-detail.component.html',
  styleUrls: ['./event-detail.component.scss'],
  imports: [CommonModule]
})
export class EventDetailComponent implements OnInit, OnDestroy {
  event: any;
  userId!: number;  // Теперь берем реальный ID
  successMessage: string = '';
  errorMessage: string = '';
  loading: boolean = true;
  
  startTime: number = 0;
  eventId: number = 0;
  private apiUrl = '/api';

  constructor(
    private route: ActivatedRoute, 
    private router: Router, 
    private http: HttpClient,
    private recommendationService: RecommendationService,
    private authService: AuthService  // ✅ добавили AuthService
  ) {}

  ngOnInit(): void {
    this.userId = this.authService.getUserId();  // ✅ Получаем реальный userId

    this.eventId = Number(this.route.snapshot.paramMap.get('id'));
    
    this.http.get(`${this.apiUrl}/events/${this.eventId}`).subscribe({
      next: (response) => {
        this.event = response;
        console.log('Данные о событии:', this.event);
        this.startTime = Date.now();
        this.recordClick();
        this.loading = false;
      },
      error: (error) => {
        console.error('Ошибка загрузки события:', error);
        this.loading = false;
        if (error.status === 404) {
          this.errorMessage = `Событие не найдено.`;
        } else {
          this.errorMessage = `Ошибка при загрузке события: ${error.message || 'Неизвестная ошибка'}`;
        }
      }
    });
  }
  
  ngOnDestroy(): void {
    if (this.startTime > 0 && this.eventId > 0) {
      const viewDuration = (Date.now() - this.startTime) / 1000;
      this.recordView(viewDuration);
    }
  }
  
  recordClick(): void {
    if (this.eventId > 0) {
      this.recommendationService.recordClick(this.eventId).subscribe({
        next: () => console.log('Click recorded'),
        error: (err) => console.error('Error recording click', err)
      });
    }
  }
  
  recordView(duration: number): void {
    if (this.eventId > 0) {
      this.recommendationService.recordView(this.eventId, duration).subscribe({
        next: () => console.log(`View recorded: ${duration.toFixed(2)}s`),
        error: (err) => console.error('Error recording view', err)
      });
    }
  }

  buyTicket(): void {
    if (!this.event || this.event.available_tickets <= 0) {
      return;
    }

    const payload = {
      user_id: this.userId,  // ✅ Теперь реальный ID
      event_id: this.event.id
    };

    const headers = new HttpHeaders({
      'Content-Type': 'application/json'
    });

    this.http.post(`${this.apiUrl}/buy_ticket`, payload, { headers }).subscribe({
      next: (response: any) => {
        console.log('Билет успешно забронирован:', response);
        this.event.available_tickets = Math.max(0, this.event.available_tickets - 1);
        this.successMessage = 'Билет успешно забронирован!';
        
        setTimeout(() => {
          this.successMessage = '';
        }, 3000);
      },
      error: (error) => {
        console.error('Ошибка при покупке билета:', error);
        this.successMessage = 'Ошибка при бронировании билета. Попробуйте позже.';
      }
    });
  }

  goBack(): void {
    this.router.navigate(['/']);
  }
}
