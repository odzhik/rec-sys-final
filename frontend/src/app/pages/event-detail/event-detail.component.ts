import { Component, OnInit, OnDestroy } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { RecommendationService } from '../../services/recommendation.service';
import { environment } from '../../../environments/environment';

@Component({
  selector: 'app-event-detail',
  standalone: true,
  templateUrl: './event-detail.component.html',
  styleUrls: ['./event-detail.component.scss'],
  imports: [CommonModule]
})
export class EventDetailComponent implements OnInit, OnDestroy {
  event: any;
  userId: number = 12; // Заглушка
  successMessage: string = '';
  errorMessage: string = '';
  loading: boolean = true;
  
  // For view tracking
  startTime: number = 0;
  eventId: number = 0;
  private apiUrl = '/api'; // Use proxy path

  constructor(
    private route: ActivatedRoute, 
    private router: Router, 
    private http: HttpClient,
    private recommendationService: RecommendationService
  ) {}

  ngOnInit(): void {
    this.eventId = Number(this.route.snapshot.paramMap.get('id'));
    
    // Получаем данные о событии с сервера (используем API прокси)
    this.http.get(`${this.apiUrl}/events/${this.eventId}`).subscribe({
      next: (response) => {
        this.event = response;
        console.log('Данные о событии:', this.event);
        
        // Start tracking view time
        this.startTime = Date.now();
        
        // Record event click
        this.recordClick();
        this.loading = false;
      },
      error: (error) => {
        console.error('Ошибка загрузки события:', error);
        this.loading = false;
        if (error.status === 404) {
          this.errorMessage = `Событие не найдено. Возможно, это демонстрационное событие, которое отсутствует в базе данных.`;
        } else {
          this.errorMessage = `Ошибка при загрузке события: ${error.message || 'Неизвестная ошибка'}`;
        }
      }
    });
  }
  
  ngOnDestroy(): void {
    // Calculate view duration in seconds
    if (this.startTime > 0 && this.eventId > 0) {
      const viewDuration = (Date.now() - this.startTime) / 1000; // Convert to seconds
      this.recordView(viewDuration);
    }
  }
  
  // Record click for recommendation system
  recordClick(): void {
    if (this.eventId > 0) {
      this.recommendationService.recordClick(this.eventId).subscribe({
        next: () => console.log('Click recorded'),
        error: (err) => console.error('Error recording click', err)
      });
    }
  }
  
  // Record view for recommendation system
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
      user_id: this.userId,
      event_id: this.event.id
    };

    // Формируем HTTP заголовки для запроса
    const headers = new HttpHeaders({
      'Content-Type': 'application/json'
    });

    // Используем прокси API вместо хардкода
    this.http.post(`${this.apiUrl}/buy_ticket`, payload, { headers }).subscribe({
      next: (response: any) => {
        console.log('Билет успешно куплен:', response);
        
        // Уменьшаем количество доступных билетов локально
        this.event.available_tickets = Math.max(0, this.event.available_tickets - 1);
        
        // Показываем сообщение об успехе
        this.successMessage = 'Билет успешно куплен!';
        
        // Скрываем сообщение через 3 секунды
        setTimeout(() => {
          this.successMessage = '';
        }, 3000);
      },
      error: (error) => {
        console.error('Ошибка при покупке билета:', error);
        this.successMessage = 'Ошибка при покупке билета. Попробуйте позже.';
      }
    });
  }

  goBack(): void {
    this.router.navigate(['/']);
  }
}
