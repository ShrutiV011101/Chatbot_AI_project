import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { ChatWidgetComponent } from './chat-widget/chat-widget.component';
import { WidgetComponent } from './widget/widget.component';

const routes: Routes = [
  {
    path:'chat-widget',
    component:ChatWidgetComponent
  },
  {
    path:'',
    component:WidgetComponent
  }
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
