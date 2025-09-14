import { Injectable } from '@angular/core';
import { EncryptionHelper } from './encrypt-helper' // Adjust the path as needed

@Injectable({
  providedIn: 'root'
})
export class EncryptionHandleService {
  private helper: EncryptionHelper = new EncryptionHelper();

  encrypt(plainText: string, encryptionKey: string): string {
    return this.helper.encryptString(plainText, encryptionKey);
  }

  decrypt(plainText: string, encryptionKey: string): string {
    return this.helper.decryptString(plainText, encryptionKey);
  }


}