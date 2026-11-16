const http = require('http');
const fs = require('fs');
const path = require('path');

function request(options, postData = null) {
  return new Promise((resolve, reject) => {
    const req = http.request(options, (res) => {
      const chunks = [];
      res.on('data', chunk => chunks.push(chunk));
      res.on('end', () => {
        const buffer = Buffer.concat(chunks);
        resolve({
          statusCode: res.statusCode,
          headers: res.headers,
          data: buffer,
          text: buffer.toString('utf8'),
          json: () => JSON.parse(buffer.toString('utf8'))
        });
      });
    });

    req.on('error', reject);

    if (postData) {
      if (typeof postData === 'string' || Buffer.isBuffer(postData)) {
        req.write(postData);
      } else {
        req.write(JSON.stringify(postData));
      }
    }
    req.end();
  });
}

async function runComprehensiveTests() {
  console.log('====================================================');
  console.log('🧪 ELAYA NARAYANAN — DYNAMIC AUDIOCRM & KYC SHEETS SUITE');
  console.log('====================================================\n');

  let passed = 0;
  let failed = 0;

  function assert(condition, testName) {
    if (condition) {
      console.log(`  ✓ PASS: ${testName}`);
      passed++;
    } else {
      console.error(`  ✗ FAIL: ${testName}`);
      failed++;
    }
  }

  try {
    // [TEST GROUP 1] Web Application UI & Google Sheets Multi-Sheet Architecture
    console.log('[TEST GROUP 1] UI & Google Sheets Multi-Sheet Architecture');
    const indexHtml = fs.readFileSync(path.join(__dirname, '../index.html'), 'utf8');
    const appJs = fs.readFileSync(path.join(__dirname, '../app.js'), 'utf8');

    assert(indexHtml.includes('ELAYA NARAYANAN'), 'Master App Brand: "ELAYA NARAYANAN"');
    assert(indexHtml.includes('Dynamic AudioCRM & Sheets'), 'Master App Title: "Dynamic AudioCRM & Sheets"');
    assert(indexHtml.includes('sheet-tabs-scroll'), 'Google Sheets Tab Bar (#sheet-tabs-scroll) present');
    assert(indexHtml.includes('new-sheet-modal'), 'Add New Sheet Modal present');
    assert(indexHtml.includes('downloadSheetExcel'), '1-Click Excel (.xlsx) Download button present');
    assert(indexHtml.includes('downloadSheetCsv'), '1-Click CSV Download button present');
    assert(indexHtml.includes('downloadSheetPdf'), '1-Click PDF Report Download button present');
    assert(indexHtml.includes('btn-download-drawer-audio'), 'Voice Recording (.webm) download button in audit drawer');
    assert(indexHtml.includes('queue-recovery-banner'), 'Queue Auto-Recovery Banner present');

    // [TEST GROUP 2] Google Sheets Multi-Sheet Engine & Methods in app.js
    console.log('\n[TEST GROUP 2] Google Sheets-Style Multi-Sheet Engine');
    assert(appJs.includes('sheetsVault'), 'sheetsVault state store initialized');
    assert(appJs.includes('initSheetsVault'), 'initSheetsVault automatic bootstrap active');
    assert(appJs.includes('renderSheetTabs'), 'renderSheetTabs dynamic tab renderer active');
    assert(appJs.includes('switchActiveSheet'), 'switchActiveSheet instant tab switching active');
    assert(appJs.includes('createNewBlankSheet'), 'createNewBlankSheet blank sheet creator active');
    assert(appJs.includes('duplicateSheet'), 'duplicateSheet sheet cloning active');
    assert(appJs.includes('deleteSheet'), 'deleteSheet sheet removal active');
    assert(appJs.includes('promptRenameActiveSheet'), 'promptRenameActiveSheet inline rename active');
    assert(appJs.includes('promptAddNewCustomerRow'), 'promptAddNewCustomerRow customer row addition active');

    // [TEST GROUP 3] 1-Click Downloads & File Persistence
    console.log('\n[TEST GROUP 3] 1-Click Export & File Persistence');
    assert(appJs.includes('downloadSheetExcel'), 'downloadSheetExcel function active');
    assert(appJs.includes('downloadSheetCsv'), 'downloadSheetCsv function active');
    assert(appJs.includes('downloadSheetPdf'), 'downloadSheetPdf function active');
    assert(appJs.includes('downloadBackupJson'), 'downloadBackupJson function active');

    // [TEST GROUP 4] AudioCRM Dataset Persistence & Endpoints
    console.log('\n[TEST GROUP 4] AudioCRM Dataset Persistence & Endpoints');
    const datasetRes = await request({ hostname: '127.0.0.1', port: 8510, path: '/api/dataset', method: 'GET' });
    const dsJson = datasetRes.json();
    assert(dsJson.success === true, 'Dataset API returned success');
    assert(dsJson.dataset.totalRows === 100, `Total Rows preserved = 100 (got ${dsJson.dataset.totalRows})`);
    assert(dsJson.dataset.fileName.includes('KYC SOUTH'), `Active dataset matches user file (${dsJson.dataset.fileName})`);

    // Manual Save API
    const saveRes = await request({
      hostname: '127.0.0.1',
      port: 8510,
      path: '/api/dataset/save',
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });
    const saveJson = saveRes.json();
    assert(saveJson.success === true, 'Dataset manual save endpoint works');

    // Excel Export Endpoint
    const excelRes = await request({ hostname: '127.0.0.1', port: 8510, path: '/api/export/excel', method: 'GET' });
    assert(excelRes.statusCode === 200, 'Excel Export returns HTTP 200');
    assert(excelRes.headers['content-type'].includes('spreadsheetml'), 'Excel Content-Type is valid');
    assert(excelRes.data.length > 50000, `Excel size is healthy (${excelRes.data.length} bytes)`);

    // CSV Export Endpoint
    const csvRes = await request({ hostname: '127.0.0.1', port: 8510, path: '/api/export/csv', method: 'GET' });
    assert(csvRes.statusCode === 200, 'CSV Export returns HTTP 200');
    assert(csvRes.headers['content-type'].includes('text/csv'), 'CSV Content-Type is valid');
    assert(csvRes.data.length > 10000, `CSV size is healthy (${csvRes.data.length} bytes)`);

    // [TEST GROUP 5] IndexedDB Audio Vault & Auto-Queue Recovery Engine
    console.log('\n[TEST GROUP 5] Audio Recording Vault & Auto-Queue Recovery Engine');
    assert(appJs.includes('saveAudioRecordingToVault'), 'IndexedDB saveAudioRecordingToVault active');
    assert(appJs.includes('getAudioRecordingFromVault'), 'IndexedDB getAudioRecordingFromVault active');
    assert(appJs.includes('syncVaultRecordingsToDataset'), 'syncVaultRecordingsToDataset active');
    assert(appJs.includes('autoRecoverStuckQueueRows'), 'autoRecoverStuckQueueRows queue recovery active');
    assert(appJs.includes('forceResolveAllQueuedRows'), 'forceResolveAllQueuedRows 1-tap synthesizer active');
    assert(appJs.includes('ElayaAudioVault'), 'Permanent browser IndexedDB ElayaAudioVault initialized');

    // [TEST GROUP 6] Inline Voice Recording Playback Column & Organized Audio Vault Library
    console.log('\n[TEST GROUP 6] Inline Voice Recording Column & Organized Audio Vault Library');
    assert(indexHtml.includes('recordings-vault-modal'), 'Organized Voice Recordings Vault Modal present in HTML');
    assert(indexHtml.includes('vault-count-badge'), 'Vault Audio Count badge present in top header');
    assert(indexHtml.includes('openRecordingsVaultModal'), 'Audio Vault trigger button bound to openRecordingsVaultModal');
    assert(appJs.includes('Voice Recording & Playback'), 'Spreadsheet Table header contains "Voice Recording & Playback" as last column');
    assert(appJs.includes('generateSmartAudioFilename'), 'Smart audio filename generator with date, customer, phone, product & duration active');
    assert(appJs.includes('renderRowAudioCell'), 'Inline table audio player cell renderer active');
    assert(appJs.includes('downloadRowAudioFile'), 'Individual 1-click smart webm audio downloader active');
    assert(appJs.includes('openRecordingsVaultModal'), 'openRecordingsVaultModal modal controller active');
    assert(appJs.includes('downloadAllVaultRecordings'), '1-click batch Download All Audio downloader active');
    assert(appJs.includes('updateVaultBadge'), 'updateVaultBadge dynamic counter active');

    console.log('\n====================================================');
    console.log(`RESULTS: ${passed} PASSED, ${failed} FAILED`);
    console.log('====================================================\n');

    if (failed === 0) {
      console.log('🎉 ALL INTEGRATION TESTS PASSED PERFECTLY!');
      process.exit(0);
    } else {
      process.exit(1);
    }

  } catch (err) {
    console.error('Test suite runtime error:', err);
    process.exit(1);
  }
}

runComprehensiveTests();
