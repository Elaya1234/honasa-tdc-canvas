const http = require('http');
const fs = require('fs');

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
  console.log('🧪 HONASA DISCUSSION INTELLIGENCE — INTEGRATION SUITE');
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
    // 1. Root HTML Check
    console.log('[TEST GROUP 1] Web Application UI & Dual-Option Portal');
    const rootRes = await request({ hostname: 'localhost', port: 8510, path: '/', method: 'GET' });
    assert(rootRes.text.includes('Elaya Narayanan'), 'Master App Brand: "Elaya Narayanan"');
    assert(rootRes.text.includes('Discussion Intelligence'), 'Master App Title: "Discussion Intelligence"');
    assert(rootRes.text.includes('id="portal-modal"'), 'Option 1 & 2 Welcome Portal Modal present');
    assert(rootRes.text.includes('1. Customer AudioCRM & KYC'), 'Option 1: Customer AudioCRM & KYC tab');
    assert(rootRes.text.includes('2. In-Person Meeting Intelligence'), 'Option 2: In-Person Meeting Intelligence tab');
    assert(rootRes.text.includes('id="meeting-waveform"'), 'Waveform Visualizer canvas present');
    assert(rootRes.text.includes('id="meeting-modal"'), 'Meeting Minutes Modal present');

    // 2. AudioCRM Dataset & Persistence
    console.log('\n[TEST GROUP 2] Option 1: AudioCRM Dataset Persistence & Excel Export');
    const datasetRes = await request({ hostname: 'localhost', port: 8510, path: '/api/dataset', method: 'GET' });
    const dsJson = datasetRes.json();
    assert(dsJson.success === true, 'Dataset API returned success');
    assert(dsJson.dataset.totalRows === 100, `Total Rows preserved = 100 (got ${dsJson.dataset.totalRows})`);
    assert(dsJson.dataset.fileName.includes('KYC SOUTH'), `Active dataset matches user file (${dsJson.dataset.fileName})`);

    // Manual Save API
    const saveRes = await request({
      hostname: 'localhost',
      port: 8510,
      path: '/api/dataset/save',
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });
    const saveJson = saveRes.json();
    assert(saveJson.success === true, 'Dataset manual save endpoint works');

    // Excel Export
    const excelRes = await request({ hostname: 'localhost', port: 8510, path: '/api/export/excel', method: 'GET' });
    assert(excelRes.statusCode === 200, 'Excel Export returns HTTP 200');
    assert(excelRes.headers['content-type'].includes('spreadsheetml'), 'Excel Content-Type is valid');
    assert(excelRes.data.length > 50000, `Excel size is healthy (${excelRes.data.length} bytes)`);

    // CSV Export
    const csvRes = await request({ hostname: 'localhost', port: 8510, path: '/api/export/csv', method: 'GET' });
    assert(csvRes.statusCode === 200, 'CSV Export returns HTTP 200');
    assert(csvRes.headers['content-type'].includes('text/csv'), 'CSV Content-Type is valid');
    assert(csvRes.data.length > 10000, `CSV size is healthy (${csvRes.data.length} bytes)`);

    // 3. Option 2: In-Person Meeting Discussion Intelligence
    console.log('\n[TEST GROUP 3] Option 2: In-Person Meeting Discussion Engine');
    
    // List meetings
    const listRes = await request({ hostname: 'localhost', port: 8510, path: '/api/meetings', method: 'GET' });
    const listJson = listRes.json();
    assert(listJson.success === true, 'GET /api/meetings returns success');
    assert(Array.isArray(listJson.meetings) && listJson.meetings.length >= 1, `Seed meeting present (count: ${listJson.meetings.length})`);

    // Create new meeting session
    const newMeetingPayload = {
      title: 'HONASA Derma Co Q4 Strategy & Sunscreen Line Expansion',
      category: 'Commercial & Quick Commerce',
      attendees: ['Varun Alagh (CEO)', 'Ghazal Alagh (CIO)', 'R&D Head Dr. Ananya', 'Zomato/Blinkit Category Head']
    };
    const createRes = await request({
      hostname: 'localhost',
      port: 8510,
      path: '/api/meetings',
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    }, JSON.stringify(newMeetingPayload));
    const createJson = createRes.json();
    assert(createJson.success === true && createJson.meeting.id, `Created new discussion session: ${createJson.meeting?.id}`);
    const meetingId = createJson.meeting.id;

    // Simulate 1st 10-minute segment
    console.log('  -> Simulating Segment 1 (0:00 - 10:00)...');
    const seg1Res = await request({
      hostname: 'localhost',
      port: 8510,
      path: `/api/meetings/${meetingId}/simulate-segment`,
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    }, JSON.stringify({ note: 'Initial discussion on sunscreen quick commerce turnaround' }));
    const seg1Json = seg1Res.json();
    assert(seg1Json.success === true, 'Segment 1 processed successfully');
    assert(seg1Json.segment.index === 1, 'Segment 1 index verified');
    assert(seg1Json.meeting.masterTranscript.length > 100, 'Master transcript contains segment 1 text');

    // Simulate 2nd 10-minute segment (Seamless Rolling Chunk)
    console.log('  -> Simulating Segment 2 (10:00 - 20:00)...');
    const seg2Res = await request({
      hostname: 'localhost',
      port: 8510,
      path: `/api/meetings/${meetingId}/simulate-segment`,
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    }, JSON.stringify({ note: 'Reviewing dermatological clinical trial results' }));
    const seg2Json = seg2Res.json();
    assert(seg2Json.success === true, 'Segment 2 processed successfully');
    assert(seg2Json.segment.index === 2, 'Segment 2 index verified');
    assert(seg2Json.meeting.segments.length === 2, 'Total segments recorded = 2');
    assert(seg2Json.meeting.masterTranscript.includes('Segment 1') && seg2Json.meeting.masterTranscript.includes('Segment 2'), 'Master transcript unified both segments seamlessly');

    // Finalize meeting
    console.log('  -> Finalizing meeting minutes...');
    const finRes = await request({
      hostname: 'localhost',
      port: 8510,
      path: `/api/meetings/${meetingId}/finalize`,
      method: 'POST'
    });
    const finJson = finRes.json();
    assert(finJson.success === true, 'Meeting finalized successfully');
    assert(finJson.meeting.status === 'completed', 'Meeting status marked as "completed"');
    assert(finJson.meeting.summary.length > 50, 'Executive summary synthesized');
    assert(finJson.meeting.decisions.length >= 1, `Strategic decisions logged: ${finJson.meeting.decisions.length}`);
    assert(finJson.meeting.actionItems.length >= 1, `Action items matrix populated: ${finJson.meeting.actionItems.length}`);

    // Export Markdown (.md)
    console.log('\n[TEST GROUP 4] Meeting Export Options (Markdown, Plain Text, Print)');
    const mdRes = await request({
      hostname: 'localhost',
      port: 8510,
      path: `/api/meetings/${meetingId}/export/md`,
      method: 'GET'
    });
    assert(mdRes.statusCode === 200, 'Markdown export returns HTTP 200');
    assert(mdRes.headers['content-type'].includes('markdown'), 'Markdown Content-Type header valid');
    assert(mdRes.text.includes('# HONASA Derma Co Q4 Strategy'), 'Markdown contains H1 title');
    assert(mdRes.text.includes('Executive Summary'), 'Markdown contains Executive Summary');
    assert(mdRes.text.includes('Action Items & Ownership'), 'Markdown contains Action Items');
    assert(mdRes.text.includes('Verbatim Master Transcript'), 'Markdown contains unified transcript');

    // Export Plain Text (.txt)
    const txtRes = await request({
      hostname: 'localhost',
      port: 8510,
      path: `/api/meetings/${meetingId}/export/txt`,
      method: 'GET'
    });
    assert(txtRes.statusCode === 200, 'Plain Text export returns HTTP 200');
    assert(txtRes.text.includes('DISCUSSION INTELLIGENCE'), 'Text export contains title header');

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
