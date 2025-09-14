import * as CryptoJS from 'crypto-js';

export class EncryptionHelper {
  private iv: number[] = [240, 3, 45, 29, 0, 76, 173, 59];

  encryptString(plainText: string, encryptionKey: string): string {
    if (!plainText) {
      return '';
    }

    if (!encryptionKey) {
      throw new Error('Encryption Key is Required');
    }

    // Generate MD5 hash of the encryption key
    const key = CryptoJS.MD5(CryptoJS.enc.Utf8.parse(encryptionKey));

    // Convert the IV array to a word array
    const ivWordArray = CryptoJS.lib.WordArray.create(this.iv);

    // Encrypt the plain text using TripleDES with the key and IV
    const encrypted = CryptoJS.TripleDES.encrypt(
      CryptoJS.enc.Utf16.parse(plainText),
      key,
      {
        iv: ivWordArray,
        mode: CryptoJS.mode.CBC,
        padding: CryptoJS.pad.Pkcs7
      }
    );

    // Convert the encrypted data to Base64 string
    return encrypted.toString();
  }

  decryptString(encryptedText: string, encryptionKey: string): string {
    if (!encryptedText) {
      return '';
    }
  
    if (!encryptionKey) {
      throw new Error('Encryption Key is Required');
    }
  
    // Generate MD5 hash of the encryption key (same as used in encryption)
    const key = CryptoJS.MD5(CryptoJS.enc.Utf8.parse(encryptionKey));
  
    // Convert the IV array to a word array (same as used in encryption)
    const ivWordArray = CryptoJS.lib.WordArray.create(this.iv);
  
    // Decrypt the encrypted text using TripleDES with the key and IV
    const decrypted = CryptoJS.TripleDES.decrypt(
      encryptedText, // Use the encrypted string directly
      key,
      {
        iv: ivWordArray,
        mode: CryptoJS.mode.CBC,
        padding: CryptoJS.pad.Pkcs7
      }
    );
  
    // Convert the decrypted data from a WordArray to UTF16 string
    return CryptoJS.enc.Utf16.stringify(decrypted);
  }
}