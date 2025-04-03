import { bootstrapApplication } from '@angular/platform-browser';
import { importProvidersFrom } from '@angular/core';
import { AppComponent } from './app/app.component';
import { provideRouter } from '@angular/router';
import { provideHttpClient, withInterceptors } from '@angular/common/http'; // ✅ Подключаем HTTP-клиент
import { routes } from './app/app.routes'; // ✅ Маршруты
import { AuthInterceptor } from './app/interceptors/auth.interceptor';
import { HttpClientModule } from '@angular/common/http'; // ✅ Добавляем HttpClientModule
import { HomeComponent } from './app/pages/home/home.component';
bootstrapApplication(AppComponent, {
  providers: [
    provideRouter(routes), // ✅ Подключаем маршрутизацию
    provideHttpClient(withInterceptors([AuthInterceptor])), // ✅ Подключаем HTTP-клиент с интерцептором
    importProvidersFrom(HttpClientModule) // ✅ Импортируем HttpClientModule
  ]
}).catch(err => console.error(err));
