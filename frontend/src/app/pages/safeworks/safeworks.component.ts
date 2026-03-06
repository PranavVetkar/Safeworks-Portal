import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService, Requirement } from '../../services/api.service';

@Component({
  selector: 'app-safeworks',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './safeworks.component.html',
  styleUrl: './safeworks.component.css'
})
export class SafeworksComponent implements OnInit {
  requirements: Requirement[] = [];
  selectedRequirement: Requirement | null = null;
  submissions: any[] = [];
  submissionWorkers: any[] = []; // Per-contractor worker details

  isValidating = false;
  isForwarding = false;
  activeTab = 'details'; // 'details' | 'submissions'
  activeReportTab = 'cumulative'; // 'cumulative' | contractor_id string

  // Mock Contractors for selection
  contractors = [
    { id: 5, name: 'Apex Construction' },
    { id: 6, name: 'BuildWell Inc.' },
    { id: 7, name: 'City Scaffolders' }
  ];
  selectedContractors: number[] = [];

  // Shortlisting
  shortlistedIds: Set<number> = new Set();
  isShortlisting = false;

  constructor(private apiService: ApiService) { }

  ngOnInit() {
    this.loadRequirements();
  }

  loadRequirements() {
    this.apiService.getAllRequirements().subscribe(data => {
      this.requirements = data;
      if (this.requirements.length > 0 && !this.selectedRequirement) {
        this.selectRequirement(this.requirements[0]);
      }
    });
  }

  selectRequirement(req: Requirement) {
    this.selectedRequirement = req;
    this.activeTab = 'details';
    this.activeReportTab = 'cumulative';
    this.selectedContractors = [];
    this.submissions = [];
    this.submissionWorkers = [];
    this.shortlistedIds = new Set();
    this.loadSubmissions(req.id!);
    this.loadSubmissionWorkers(req.id!);
    this.loadShortlisted(req.id!);
  }

  loadSubmissions(id: number) {
    this.apiService.getSubmissions(id).subscribe(data => {
      this.submissions = data;
    });
  }

  loadSubmissionWorkers(id: number) {
    this.apiService.getSubmissionWorkers(id).subscribe({
      next: (data) => { this.submissionWorkers = data; },
      error: () => { this.submissionWorkers = []; }
    });
  }

  loadShortlisted(id: number) {
    this.apiService.getShortlistedContractors(id).subscribe({
      next: (data) => {
        this.shortlistedIds = new Set(data.map((d: any) => d.contractor_id));
      },
      error: () => { this.shortlistedIds = new Set(); }
    });
  }

  validateRequirement() {
    if (!this.selectedRequirement?.id) return;
    this.isValidating = true;
    this.apiService.validateRequirementAi(this.selectedRequirement.id).subscribe({
      next: (req) => {
        this.selectedRequirement = req;
        const idx = this.requirements.findIndex(r => r.id === req.id);
        if (idx !== -1) this.requirements[idx] = req;
        this.isValidating = false;
      },
      error: (err) => { console.error(err); this.isValidating = false; }
    });
  }

  toggleContractorSelection(id: number) {
    const index = this.selectedContractors.indexOf(id);
    if (index === -1) this.selectedContractors.push(id);
    else this.selectedContractors.splice(index, 1);
  }

  forwardToContractors() {
    if (!this.selectedRequirement?.id || this.selectedContractors.length === 0) return;
    this.isForwarding = true;
    this.apiService.forwardRequirement(this.selectedRequirement.id, this.selectedContractors).subscribe({
      next: () => {
        alert(`Requirement forwarded to ${this.selectedContractors.length} contractors!`);
        this.isForwarding = false;
        this.selectedContractors = [];
      },
      error: () => { alert('Failed to forward requirement'); this.isForwarding = false; }
    });
  }

  toggleShortlist(contractorId: number) {
    if (!this.selectedRequirement?.id) return;
    if (this.shortlistedIds.has(contractorId)) {
      // Already shortlisted – toggling off is not supported by current backend, just skip visually
      return;
    }
    this.isShortlisting = true;
    this.apiService.shortlistContractors(this.selectedRequirement.id, [contractorId]).subscribe({
      next: () => {
        this.shortlistedIds.add(contractorId);
        this.isShortlisting = false;
      },
      error: () => { this.isShortlisting = false; }
    });
  }

  getWorkersForContractor(contractorId: number): any[] {
    const group = this.submissionWorkers.find(g => g.contractor_id === contractorId);
    return group?.workers ?? [];
  }

  setReportTab(tab: string) {
    this.activeReportTab = tab;
  }
}
