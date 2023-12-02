import { NgModule } from '@angular/core';

import { AppComponent } from './app.component';
import { ApiService } from './api.service';

import { HttpClientModule } from '@angular/common/http';
import { ModelViewComponent } from './model-view/model-view.component'; // Import HttpClientModule
import { NgSelectModule } from '@ng-select/ng-select';
import { CommonModule } from '@angular/common';
import { BrowserModule } from '@angular/platform-browser';
import { FormsModule } from '@angular/forms';

@NgModule({
  declarations: [
    AppComponent,
    ModelViewComponent
  ],
  imports: [
    BrowserModule,
    HttpClientModule,
    FormsModule,
    CommonModule,
    NgSelectModule
  ],
  providers: [ApiService],
  bootstrap: [AppComponent]
})
export class AppModule { }
