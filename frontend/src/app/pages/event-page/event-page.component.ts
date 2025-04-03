import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { EventService } from '../../services/event.service';

@Component({
  selector: 'app-event-page',
  templateUrl: './event-page.component.html',
  styleUrls: ['./event-page.component.css']
})
export class EventPageComponent implements OnInit {
  eventName: string = '';
  eventData: any;

  constructor(
    private route: ActivatedRoute,
    private eventService: EventService
  ) {}

  ngOnInit(): void {
    const eventId = this.route.snapshot.paramMap.get('id') || '';
    this.getEventDataById(eventId);
  }
  
  getEventDataById(eventId: string) {
    this.eventService.getEventById(Number(eventId)).subscribe((data: any) => {
      this.eventData = data;
    });
  }  
}
