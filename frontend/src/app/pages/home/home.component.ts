import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { InterestSelectorComponent } from '../../components/interest-selector/interest-selector.component';
import { RecommendedEventsComponent } from '../../components/recommended-events/recommended-events.component';
import { RecommendationService } from '../../services/recommendation.service';
import { MatIconModule } from '@angular/material/icon';
import { AuthService } from '../../services/auth.service';
@Component({
  selector: 'app-home',
  standalone: true,
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.scss'],
  imports: [
    CommonModule,
    RouterModule,
    FormsModule,
    InterestSelectorComponent,
    RecommendedEventsComponent,
    MatIconModule
  ]
})
export class HomeComponent implements OnInit, OnDestroy {
  allEvents: any[] = [];
  carouselEvents: any[] = [];
  filteredEvents: any[] = [];

  currentSlideIndex = 0;
  carouselOffset = 0;
  slideWidth = 0;
  autoSlideInterval: any;
  popEventId: number | null = null;
  userName: string | null = null;
  allDatesSelected = true;
  selectedDate: string = 'all';
  availableDates: { day: string; month: string; fullDate: string; dayOfWeek: string }[] = [];
  currentOffset: number = 0;
  daysToShow: number = 14;

  constructor(
    private router: Router,
    private http: HttpClient,
    private recommendationService: RecommendationService,
    private authService: AuthService
  ) {}

  ngOnInit(): void {
    this.generateDates();
    this.fetchEvents();
    this.loadLikesFromStorage();

    
    setTimeout(() => {
      const container = document.querySelector('.carousel-container') as HTMLElement;
      this.slideWidth = container?.offsetWidth || 0;
      this.updateCarouselPosition(); // обязательно!
    }, 100);

    this.startAutoSlide();
  }

  generateDates(): void {
    const today = new Date();
    const daysOfWeek = ['Вс', 'Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб'];
    const monthNames = ['янв.', 'февр.', 'мар.', 'апр.', 'мая', 'июня', 'июля', 'авг.', 'сент.', 'окт.', 'нояб.', 'дек.'];

    this.availableDates = [];

    for (let i = 0; i < 42; i++) {
      const date = new Date(today);
      date.setDate(today.getDate() + i);

      const day = date.getDate().toString().padStart(2, '0');
      const month = monthNames[date.getMonth()];
      const dayOfWeek = daysOfWeek[date.getDay()];

      this.availableDates.push({
        day,
        month,
        fullDate: `${day}.${date.getMonth() + 1}.${date.getFullYear()}`,
        dayOfWeek
      });
    }
  }

  getDisplayedDates(): any[] {
    return this.availableDates.slice(this.currentOffset, this.currentOffset + this.daysToShow);
  }

  prevWeek(): void {
    if (this.currentOffset > 0) {
      this.currentOffset -= this.daysToShow;
    }
  }

  nextWeek(): void {
    if (this.currentOffset + this.daysToShow < this.availableDates.length) {
      this.currentOffset += this.daysToShow;
    }
  }

  fetchEvents(): void {
    this.http.get<any[]>('http://localhost:8000/events/').subscribe({
      next: (events) => {
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
  
        this.allEvents = events.map(event => ({
          ...event,
          date: new Date(event.date).toLocaleDateString('ru-RU'),
          image: imageMap[event.name] || '/images/placeholder.jpg'
        }));
  
        this.carouselEvents = this.allEvents.slice(0, 4);
        this.filteredEvents = [...this.allEvents];
      },
      error: (err) => {
        console.error('❌ Ошибка загрузки событий:', err?.message || err?.statusText || err);
      }
    });
  }
  
  
  
  

  selectDate(date: string): void {
    this.selectedDate = date;
    this.allDatesSelected = date === 'all';

    this.filteredEvents = date === 'all'
      ? [...this.allEvents]
      : this.allEvents.filter(event => {
          const eventDate = new Date(event.date.split('.').reverse().join('-'));
          const selectedDateObj = new Date(date.split('.').reverse().join('-'));
          return (
            eventDate.getDate() === selectedDateObj.getDate() &&
            eventDate.getMonth() === selectedDateObj.getMonth() &&
            eventDate.getFullYear() === selectedDateObj.getFullYear()
          );
        });
  }

  goToEventPage(event: any): void {
    this.recommendationService.recordClick(event.id).subscribe();
    this.router.navigate(['/event', event.id]);
  }

  nextSlide(): void {
    this.currentSlideIndex = (this.currentSlideIndex + 1) % this.carouselEvents.length;
    this.updateCarouselPosition();
  }

  prevSlide(): void {
    this.currentSlideIndex = (this.currentSlideIndex - 1 + this.carouselEvents.length) % this.carouselEvents.length;
    this.updateCarouselPosition();
  }

  goToSlide(index: number): void {
    this.currentSlideIndex = index;
    this.updateCarouselPosition();
  }

  updateCarouselPosition(): void {
    this.carouselOffset = -this.currentSlideIndex * this.slideWidth;
  }

  filterEvents(category: string): void {
    this.filteredEvents = category === 'all'
      ? [...this.allEvents]
      : this.allEvents.filter(event => event.category === category);
  }

  startAutoSlide(): void {
    this.autoSlideInterval = setInterval(() => {
      this.nextSlide();
    }, 3000);
  }

  stopAutoSlide(): void {
    clearInterval(this.autoSlideInterval);
  }

  ngOnDestroy(): void {
    this.stopAutoSlide();
  }
  likedEvents: Set<number> = new Set();

  toggleLike(eventId: number): void {
    if (this.likedEvents.has(eventId)) {
      this.likedEvents.delete(eventId);
    } else {
      this.likedEvents.add(eventId);
  
      // Анимация взрыва
      this.popEventId = eventId;
      setTimeout(() => {
        this.popEventId = null;
      }, 400); // должно совпадать с длиной animation
    }
  
    this.saveLikesToStorage();
  }
  
  
  saveLikesToStorage(): void {
    localStorage.setItem('likedEvents', JSON.stringify(Array.from(this.likedEvents)));
  }
  
  loadLikesFromStorage(): void {
    const stored = localStorage.getItem('likedEvents');
    if (stored) {
      this.likedEvents = new Set(JSON.parse(stored));
    }
  }
  

  

}
