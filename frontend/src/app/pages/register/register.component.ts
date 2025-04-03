import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router'; // Роутер для перенаправления
import { AuthService } from '../../services/auth.service'; // Сервис авторизации

@Component({
  selector: 'app-register',
  standalone: true,
  templateUrl: './register.component.html',
  styleUrls: ['./register.component.scss'],
  imports: [CommonModule, FormsModule] // ОБЯЗАТЕЛЬНО добавляем сюда FormsModule
})
export class RegisterComponent {
  username: string = '';
  email: string = '';
  password: string = '';
  confirmPassword: string = '';
  errorMessage: string = '';
  successMessage: string = '';

  constructor(private authService: AuthService, private router: Router) {}

  register(event: Event) {
    event.preventDefault();

    if (!this.username || !this.email || !this.password || !this.confirmPassword) {
      this.errorMessage = 'Все поля обязательны!';
      return;
    }

    if (this.password !== this.confirmPassword) {
      this.errorMessage = 'Пароли не совпадают!';
      return;
    }

    this.authService.register(this.username, this.email, this.password).subscribe({
      next: () => {
        this.successMessage = 'Регистрация успешна! Перенаправление...';
        this.errorMessage = '';
        setTimeout(() => this.router.navigate(['/login']), 2000);
      },
      error: (err) => {
        this.errorMessage = err.error?.message || 'Ошибка регистрации';
        this.successMessage = '';
      }
    });
  }
}
