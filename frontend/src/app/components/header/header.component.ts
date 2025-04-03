import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Router } from '@angular/router';
import { AuthService } from '../../services/auth.service';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-header',
  standalone: true,
  templateUrl: './header.component.html',
  styleUrls: ['./header.component.scss'],
  imports: [CommonModule, RouterModule]
})
export class HeaderComponent implements OnInit, OnDestroy {
  isAuthenticated: boolean = false;
  private authSubscription!: Subscription;

  constructor(private authService: AuthService, private router: Router) {}

  ngOnInit() {
    // Подписка на изменения состояния авторизации
    this.authSubscription = this.authService.authState$.subscribe((authStatus) => {
      this.isAuthenticated = authStatus;
    });
  }

  goToProfile() {
    this.router.navigate(['/profile']); // Переход в профиль
  }

  ngOnDestroy() {
    // Отписка, чтобы избежать утечек памяти
    if (this.authSubscription) {
      this.authSubscription.unsubscribe();
    }
  }
}
