import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ModelEdgeComponent } from './model-edge.component';

describe('ModelEdgeComponent', () => {
  let component: ModelEdgeComponent;
  let fixture: ComponentFixture<ModelEdgeComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ModelEdgeComponent]
    })
    .compileComponents();
    
    fixture = TestBed.createComponent(ModelEdgeComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
