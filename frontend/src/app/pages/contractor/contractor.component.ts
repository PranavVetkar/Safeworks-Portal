import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService, Requirement, Worker } from '../../services/api.service';

@Component({
  selector: 'app-contractor',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './contractor.component.html',
  styleUrl: './contractor.component.css'
})
export class ContractorComponent implements OnInit {
  Object = Object;
  requirements: Requirement[] = [];
  selectedRequirement: Requirement | null = null;
  workers: Worker[] = [];

  // Compatibility results map: workerId -> { match_percentage, suggested_courses }
  compatibilityResults: { [key: number]: any } = {};
  isChecking = false;

  // Submission Form
  selectedWorkers: number[] = [];
  readinessDate: string = '';
  isSubmitting = false;

  // Auto-calculated submission counts (used in template & submitApplication)
  get workersCommitted(): number {
    return this.selectedWorkers.length;
  }
  get workersReady(): number {
    return this.selectedWorkers.filter(
      id => (this.compatibilityResults[id]?.match_percentage ?? 0) > 80
    ).length;
  }
  get workersToOnboard(): number {
    return this.workersCommitted - this.workersReady;
  }

  // Course management: workerId -> Set of assigned course names
  assignedCourses: { [workerId: number]: Set<string> } = {};
  courseLoading: { [workerId: number]: boolean } = {};

  get contractorId(): number {
    return parseInt(localStorage.getItem('userId') || '5', 10);
  }

  constructor(private apiService: ApiService) { }

  ngOnInit() {
    this.apiService.getAssignedRequirements(this.contractorId).subscribe(data => {
      this.requirements = data;
    });

    this.apiService.getWorkers(this.contractorId).subscribe(data => {
      this.workers = data;
      if (this.workers.length === 0) {
        this.workers = [
          { id: 101, name: 'John Doe', contractor_id: this.contractorId, certifications: 'OSHA 30, First Aid', years_experience: 5, area_of_experience: 'Electrical' },
          { id: 102, name: 'Jane Smith', contractor_id: this.contractorId, certifications: 'Master Electrician, Safety Pro', years_experience: 8, area_of_experience: 'Scaffolding' }
        ];
      }
    });
  }

  selectRequirement(req: Requirement) {
    this.selectedRequirement = req;
    this.compatibilityResults = {};
    this.selectedWorkers = [];
    this.assignedCourses = {};
  }

  checkCompatibility() {
    if (!this.selectedRequirement?.id || this.workers.length === 0) return;

    this.isChecking = true;
    let checksCompleted = 0;

    this.workers.forEach(w => {
      this.apiService.checkWorkerCompatibility(this.selectedRequirement!.id!, w.id).subscribe({
        next: (res) => {
          this.compatibilityResults[w.id] = res;
          checksCompleted++;
          if (checksCompleted === this.workers.length) this.isChecking = false;
          // Load existing assigned courses for this worker
          this.loadWorkerCourses(w.id);
        },
        error: (err) => {
          console.error(err);
          this.compatibilityResults[w.id] = { match_percentage: Math.floor(Math.random() * 40) + 40, suggested_courses: ['Fallback Course'] };
          checksCompleted++;
          if (checksCompleted === this.workers.length) this.isChecking = false;
          this.loadWorkerCourses(w.id);
        }
      });
    });
  }

  loadWorkerCourses(workerId: number) {
    this.apiService.getWorkerCourses(workerId).subscribe({
      next: (courses) => {
        this.assignedCourses[workerId] = new Set(courses);
      },
      error: () => {
        this.assignedCourses[workerId] = new Set();
      }
    });
  }

  isCourseAssigned(workerId: number, course: string): boolean {
    return this.assignedCourses[workerId]?.has(course) ?? false;
  }

  toggleCourse(workerId: number, course: string) {
    if (this.isCourseAssigned(workerId, course)) {
      this.apiService.removeWorkerCourse(workerId, course).subscribe({
        next: () => {
          this.assignedCourses[workerId].delete(course);
        }
      });
    } else {
      this.apiService.assignWorkerCourse(workerId, course).subscribe({
        next: () => {
          if (!this.assignedCourses[workerId]) this.assignedCourses[workerId] = new Set();
          this.assignedCourses[workerId].add(course);
        }
      });
    }
  }

  toggleWorker(id: number) {
    const idx = this.selectedWorkers.indexOf(id);
    if (idx === -1) {
      this.selectedWorkers.push(id);
    } else {
      this.selectedWorkers.splice(idx, 1);
    }
  }

  submitApplication() {
    if (!this.selectedRequirement || this.selectedWorkers.length === 0) return;
    this.isSubmitting = true;

    // Auto-calculate worker counts from compatibility results
    const committed = this.selectedWorkers.length;
    const ready = this.selectedWorkers.filter(
      id => (this.compatibilityResults[id]?.match_percentage ?? 0) > 80
    ).length;
    const toOnboard = committed - ready;

    const sub = {
      requirement_id: this.selectedRequirement.id!,
      contractor_id: this.contractorId,
      worker_ids: this.selectedWorkers.join(','),
      readiness_date: this.readinessDate,
      workers_committed: committed,
      workers_ready: ready,
      workers_to_onboard: toOnboard
    };

    this.apiService.submitApplication(sub).subscribe({
      next: () => {
        alert('Application submitted successfully!');
        this.isSubmitting = false;
        this.selectedRequirement = null;
      },
      error: () => {
        alert('Error submitting application.');
        this.isSubmitting = false;
      }
    });
  }
}
