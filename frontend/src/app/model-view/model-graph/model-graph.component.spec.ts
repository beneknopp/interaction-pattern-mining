import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ModelGraphComponent } from './model-graph.component';

describe('ModelGraphComponent', () => {
  let component: ModelGraphComponent;
  let fixture: ComponentFixture<ModelGraphComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ModelGraphComponent]
    })
    .compileComponents();
    
    fixture = TestBed.createComponent(ModelGraphComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
