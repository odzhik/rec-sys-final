import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Router, RouterLink } from '@angular/router';
import { RecommendationService } from '../../services/recommendation.service';

@Component({
  selector: 'app-recommended-events',
  standalone: true,
  imports: [CommonModule, RouterModule, RouterLink],
  template: `
    <div class="recommended-container">
      <div class="recommended-events">
        <h2>Рекомендованные для вас</h2>
        <div class="events-grid" *ngIf="recommendedEvents.length > 0">
          <div class="event-card" *ngFor="let event of recommendedEvents" [routerLink]="['/event', event.id]" (click)="onEventClick(event)">
            <div class="event-image">
              <img [src]="event.image || '/images/placeholder.jpg'" [alt]="event.name">
            </div>
            <div class="event-details">
              <h3>{{ event.name }}</h3>
              <p class="event-date">{{ event.date }}</p>
              <p class="event-location">{{ event.location }}</p>
              <p class="event-price">{{ event.price === 'Free' ? 'Бесплатно' : event.price + ' ₸' }}</p>
            </div>
          </div>
        </div>
        <div class="loading" *ngIf="loading">
          <p>Загрузка рекомендаций...</p>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .recommended-container {
      width: 100%;
      display: flex;
      justify-content: center;
      padding: 0 1rem;
    }

    .recommended-events {
      margin: 2rem 0;
      width: 100%;
      max-width: 1200px;
      text-align: center;
    }

    h2 {
      font-size: 1.5rem;
      margin-bottom: 1.5rem;
      color: #333;
      text-align: center;
      font-weight: bold;
    }

    .events-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
      gap: 1.5rem;
      justify-content: center;
    }

    .event-card {
      border-radius: 8px;
      overflow: hidden;
      box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
      transition: transform 0.3s ease, box-shadow 0.3s ease;
      cursor: pointer;
      background-color: #fff;
      margin: 0 auto;
      max-width: 280px;
      width: 100%;
    }

    .event-card:hover {
      transform: translateY(-5px);
      box-shadow: 0 10px 20px rgba(0, 0, 0, 0.15);
    }

    .event-image {
      height: 150px;
      overflow: hidden;
    }

    .event-image img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }

    .event-details {
      padding: 1rem;
      text-align: left;
    }

    .event-details h3 {
      margin: 0 0 0.5rem;
      font-size: 1.1rem;
    }

    .event-date, .event-location, .event-price {
      margin: 0.25rem 0;
      font-size: 0.9rem;
      color: #666;
    }

    .event-price {
      font-weight: bold;
      color: #2c3e50;
    }

    .loading {
      text-align: center;
      padding: 2rem;
      color: #666;
    }

    @media (max-width: 768px) {
      .events-grid {
        grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
      }

      .event-card {
        max-width: 230px;
      }
    }
  `]
})
export class RecommendedEventsComponent implements OnInit {
  recommendedEvents: any[] = [];
  loading = true;

  constructor(
    private recommendationService: RecommendationService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.loadRecommendations();
  }

  loadRecommendations(): void {
    this.loading = true;

    const imageMap: { [key: string]: string } = {
      'Jazz Night': '/images/jazz.jpg',
      'Startup Pitch': '/images/startup.png',
      'Movie Premiere': '/images/movie.jpg',
      'Food Festival': '/images/food-fest.jpg',
      'Art Exhibition': '/images/art.jpg',
      'Stand-up Show': '/images/standup.jpg',
      'Classical Concert': '/images/classical.jpg',
      'Fitness Expo': '/images/fitness.jpeg',
      'Movie Night: Interstellar': '/images/interstellar.jpg',
      'Tech Meetup': '/images/event1.jpg'
    };

    this.recommendationService.getRecommendations(4).subscribe({
      next: (events) => {
        this.recommendedEvents = events.map(event => ({
          ...event,
          image: imageMap[event.name] || '/images/placeholder.jpg'
        }));
        this.loading = false;
      },
      error: () => {
        this.loadFallbackEvents();
        this.loading = false;
      }
    });
  }

  loadFallbackEvents(): void {
    this.recommendedEvents = [
      { id: 1, image: '/images/event1.jpg', name: 'Concert in Almaty', date: '17.03.2025', location: 'Republic Palace', price: 30 },
      { id: 2, image: '/images/event2.jpg', name: 'Movie Night', date: '18.03.2025', location: 'Esentai Mall', price: 'Free' },
      { id: 3, image: '/images/event3.jpg', name: 'Football Match', date: '19.03.2025', location: 'Central Stadium', price: 15 },
      { id: 4, image: '/images/event4.jpeg', name: 'Comedy Show', date: '20.03.2025', location: 'Theatre', price: 25 }
    ];
  }

  onEventClick(event: any): void {
    this.recommendationService.recordClick(event.id).subscribe();
  }
}

