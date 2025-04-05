import { Component, OnInit } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { AuthService } from '../../services/auth.service';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router'; // Добавлено для навигации
import { MatIconModule } from '@angular/material/icon';

@Component({
  selector: 'app-profile',
  standalone: true,
  imports: [CommonModule, MatIconModule],
  templateUrl: './profile.component.html',
  styleUrls: ['./profile.component.scss']
})
export class ProfileComponent implements OnInit {
  user: any;
  tickets: any[] = [];
  likedEvents: any[] = [];
  reservedEvents: any[] = [];  // Массив для забронированных событий

  constructor(
    private authService: AuthService,
    private http: HttpClient,
    private router: Router  // Для навигации на страницу события
  ) {}

  ngOnInit() {
    // Получаем профиль пользователя через AuthService
    this.authService.getProfile().subscribe({
      next: (data) => {
        this.user = data;
        this.getUserTickets();
        this.loadLikedEvents();
        this.getReservedEvents();  // Загружаем забронированные события
      },
      error: (error) => {
        console.error("Ошибка загрузки профиля", error);
      }
    });
  }

  // Логика выхода пользователя
  logout() {
    this.authService.logout();
  }

  // Получение билетов пользователя
  getUserTickets() {
    if (!this.user || !this.user.id) return;

    const accessToken = localStorage.getItem('access_token');
    const headers = new HttpHeaders().set('Authorization', `Bearer ${accessToken}`);

    // Запрос на получение билетов пользователя
    this.http.get<any[]>(`http://127.0.0.1:8000/tickets/${this.user.id}`, { headers }).subscribe({
      next: (data) => {
        this.tickets = data;
      },
      error: (error) => {
        console.error('Ошибка при получении билетов:', error);
      }
    });
  }

  // Получение забронированных событий пользователя
  getReservedEvents() {
    if (!this.user || !this.user.id) return;
  
    const accessToken = localStorage.getItem('access_token');
    const headers = new HttpHeaders().set('Authorization', `Bearer ${accessToken}`);
  
    this.http.get<any[]>(`http://127.0.0.1:8000/reservations/${this.user.id}`, { headers }).subscribe({
      next: (data) => {
        this.reservedEvents = data;
      },
      error: (error) => {
        console.error('Ошибка при получении забронированных событий:', error);
      }
    });
  }
  

  // Получение лайкнутых событий
  loadLikedEvents() {
    const likedIds = new Set<number>(JSON.parse(localStorage.getItem('likedEvents') || '[]'));

    this.http.get<any[]>('http://127.0.0.1:8000/events/').subscribe({
      next: (allEvents) => {
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

        this.likedEvents = allEvents
          .filter(event => likedIds.has(event.id))
          .map(event => ({
            ...event,
            date: new Date(event.date).toLocaleDateString('ru-RU'),
            image: imageMap[event.name] || '/images/placeholder.jpg'
          }));
      },
      error: (err) => {
        console.error('Ошибка загрузки ивентов для лайков:', err);
      }
    });
  }

  // Переход к странице события
  goToEvent(eventId: number): void {
    this.router.navigate(['/event', eventId]);
  }

  // Удаление события из избранных
  removeFromFavorites(eventId: number): void {
    const liked = new Set<number>(JSON.parse(localStorage.getItem('likedEvents') || '[]'));
    liked.delete(eventId);
    localStorage.setItem('likedEvents', JSON.stringify(Array.from(liked)));
  
    // Обновляем список на экране
    this.likedEvents = this.likedEvents.filter(event => event.id !== eventId);
  }

  // Добавление события в избранные или удаление
  toggleLike(eventId: number): void {
    const liked = new Set<number>(JSON.parse(localStorage.getItem('likedEvents') || '[]'));
  
    if (liked.has(eventId)) {
      liked.delete(eventId);
      // Убираем из UI
      this.likedEvents = this.likedEvents.filter(e => e.id !== eventId);
    } else {
      liked.add(eventId);
      // Можно сделать обновление заново из API, если нужно
    }
  
    localStorage.setItem('likedEvents', JSON.stringify(Array.from(liked)));
  }
  getImageForEvent(eventName: string): string {
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
    return imageMap[eventName] || '/images/placeholder.jpg';
  }
  
}
