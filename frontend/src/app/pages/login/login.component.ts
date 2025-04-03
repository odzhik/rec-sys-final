import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AuthService } from '../../services/auth.service';
import { HeaderComponent } from '../../components/header/header.component'; 
import { Router } from '@angular/router'; 
@Component({
  selector: 'app-login',
  standalone: true,
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.scss'],
  imports: [CommonModule, FormsModule],
})
export class LoginComponent {
  email: string = '';
  password: string = '';
  errorMessage: string = '';

  constructor(private authService: AuthService, private router: Router) {}

  login() {
    console.log('Введенный email:', this.email);
    console.log('Введенный пароль:', this.password);
  
    if (!this.email || !this.password) {
      this.errorMessage = '❌ Поля не могут быть пустыми!';
      return;
    }
  
    this.authService.login(this.email, this.password).subscribe(
      (response) => {
        console.log('Ответ от сервера:', response);
        this.authService.saveToken(response.access_token);
        console.log('✅ Успешный вход! Токен сохранен.');
  
        this.router.navigate(['/']);  // Переход на главную страницу
      },
      () => {
        this.errorMessage = '❌ Ошибка: Неверный email или пароль.';
      }
    );
  }
}  
