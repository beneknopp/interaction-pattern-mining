import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { FormsModule } from '@angular/forms';

import { AppComponent } from './app.component';
import { ApiService } from './api.service';

import { HttpClientModule } from '@angular/common/http';
import { ModelViewComponent } from './model-view/model-view.component'; // Import HttpClientModule
import { NgSelectModule } from '@ng-select/ng-select';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { FormulaComponent } from "./formula/formula.component";
import { CommonModule } from '@angular/common';
import { ObjectTypeNodeComponent } from './model-view/model-graph/model-node/object-type-node.component';
import { ModelEdgeComponent } from './model-view/model-graph/model-edge/model-edge.component';
import { PatternNodeComponent } from './model-view/model-graph/model-node/pattern-node.component';
import { ModelGraphComponent } from './model-view/model-graph/model-graph.component';


@NgModule({
    declarations: [
        AppComponent,
        FormulaComponent,
        ModelViewComponent,
        ModelGraphComponent,
        PatternNodeComponent,
        ObjectTypeNodeComponent,
        ModelEdgeComponent
    ],
    providers: [ApiService],
    bootstrap: [AppComponent],
    imports: [
        BrowserModule,
        HttpClientModule,
        FormsModule,
        NgSelectModule,
        CommonModule,
        BrowserAnimationsModule
    ]
})
export class AppModule { }
