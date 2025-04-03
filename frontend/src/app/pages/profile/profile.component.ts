import { Component, OnInit } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { AuthService } from '../../services/auth.service';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-profile',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './profile.component.html',
  styleUrls: ['./profile.component.scss']
})
export class ProfileComponent implements OnInit {
  user: any;
  tickets: any[] = [];

  constructor(private authService: AuthService, private http: HttpClient) {}

  ngOnInit() {
    this.authService.getProfile().subscribe({
      next: (data) => {
        console.log("Данные профиля:", data);
        this.user = data;
        this.getUserTickets(); // Загружаем билеты после загрузки профиля
      },
      error: (error) => {
        console.error("Ошибка загрузки профиля", error);
      }
    });
  }

  logout() {
    this.authService.logout();
  }

  getUserTickets() {
    if (!this.user || !this.user.id) {
      console.warn("ID пользователя не найден!");
      return;
    }

    const accessToken = localStorage.getItem('access_token');
    const headers = new HttpHeaders().set('Authorization', `Bearer ${accessToken}`);

    const userData = { user_id: this.user.id }; // Отправляем реальный ID

    console.log("Запрос билетов для userId:", this.user.id);

  this.http.get<any[]>(`http://127.0.0.1:8000/tickets/${this.user.id}`, { headers })
    .subscribe({
      next: (data) => {
        console.log('Билеты:', data);
        this.tickets = data;
      },
      error: (error) => {
        console.error('Ошибка при получении билетов:', error);
      }
    });
  }
}

