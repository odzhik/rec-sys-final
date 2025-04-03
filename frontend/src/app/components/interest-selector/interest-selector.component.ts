import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
@Component({
  selector: 'app-interest-selector',
  standalone: true,
  templateUrl: './interest-selector.component.html',
  styleUrls: ['./interest-selector.component.scss'],
  imports: [CommonModule, FormsModule]
})
export class InterestSelectorComponent {
  interests = ['Comedy', 'Food', 'Music', 'Cinema', 'Travel', 'R&B'];
  selectedInterests: string[] = [];

  toggleInterest(interest: string) {
    if (this.selectedInterests.includes(interest)) {
      this.selectedInterests = this.selectedInterests.filter(i => i !== interest);
    } else {
      this.selectedInterests.push(interest);
    }
  }
}
