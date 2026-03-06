import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService, Requirement } from '../../services/api.service';

@Component({
  selector: 'app-hiring-client',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './hiring-client.component.html',
  styleUrl: './hiring-client.component.css'
})
export class HiringClientComponent implements OnInit {
  requirements: Requirement[] = [];
  selectedRequirement: Requirement | null = null;
  isCreatingNew: boolean = false;

  // Tab control for the detail view
  hcActiveTab: 'details' | 'vendor' = 'details';
  shortlistedVendors: any[] = [];
  isLoadingVendors = false;

  newRequirement: Requirement = {
    name: '',
    description: '',
    workers_required: 1,
    start_date: ''
  };

  isSubmitting = false;
  successMessage = '';
  errorMessage = '';

  constructor(private apiService: ApiService) { }

  ngOnInit() {
    this.loadRequirements();
  }

  get hcId(): number {
    return parseInt(localStorage.getItem('userId') || '1', 10);
  }

  loadRequirements() {
    this.apiService.getRequirements(this.hcId).subscribe({
      next: (reqs) => { this.requirements = reqs; },
      error: (err) => { console.error('Failed to load requirements', err); }
    });
  }

  selectRequirement(req: Requirement) {
    this.selectedRequirement = req;
    this.isCreatingNew = false;
    this.hcActiveTab = 'details';
    this.shortlistedVendors = [];
    this.successMessage = '';
    this.errorMessage = '';
    this.loadShortlistedVendors(req.id!);
  }

  loadShortlistedVendors(reqId: number) {
    this.isLoadingVendors = true;
    this.apiService.getShortlistedForHC(reqId).subscribe({
      next: (data) => { this.shortlistedVendors = data; this.isLoadingVendors = false; },
      error: () => { this.shortlistedVendors = []; this.isLoadingVendors = false; }
    });
  }

  startNewRequirement() {
    this.selectedRequirement = null;
    this.isCreatingNew = true;
    this.hcActiveTab = 'details';
    this.shortlistedVendors = [];
    this.successMessage = '';
    this.errorMessage = '';
    this.newRequirement = {
      name: '',
      description: '',
      workers_required: 1,
      start_date: ''
    };
  }

  onSubmit() {
    this.isSubmitting = true;
    this.successMessage = '';
    this.errorMessage = '';

    this.apiService.createRequirement(this.newRequirement, this.hcId).subscribe({
      next: (res) => {
        this.successMessage = 'Requirement published successfully!';
        this.isSubmitting = false;
        this.loadRequirements();
        this.isCreatingNew = false;
        this.selectedRequirement = res;
        this.shortlistedVendors = [];
        this.loadShortlistedVendors(res.id!);
      },
      error: (err) => {
        this.errorMessage = 'Failed to publish requirement. Please try again.';
        this.isSubmitting = false;
        console.error(err);
      }
    });
  }
}
