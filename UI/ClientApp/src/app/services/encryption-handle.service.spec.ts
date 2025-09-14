import { TestBed } from '@angular/core/testing';

import { EncryptionHandleService } from './encryption-handle.service';

describe('EncryptionHandleService', () => {
  let service: EncryptionHandleService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(EncryptionHandleService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
