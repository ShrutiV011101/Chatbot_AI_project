import { Injectable } from '@angular/core';
import { environment as env } from '../../environments/environment';
import { HttpClient, HttpHeaders } from '@angular/common/http';

@Injectable({
  providedIn: 'root'
})
export class ApiService {

  constructor(private http: HttpClient) { 

  }

  loginAPI(formData:any){
    let headers = new HttpHeaders({
      'Content-Type': 'application/json',
    });
    return this.http.post(
      env.ApiServer + '/api/auth/token',
      formData,
      { headers: headers }
    );
  }

  // region(){
  //   let headers = new HttpHeaders({
  //     'Content-Type': 'application/json',
  //   });
  //   return this.http.post(
  //     env.LoginApiServer + '/api/regions',
  //     { headers: headers }
  //   );
  // }

}
