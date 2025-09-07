#!/usr/bin/env node

/**
 * Test script for the new API endpoints
 * Run with: node test-api-endpoints.js
 */

const BASE_URL = 'http://localhost:3000';

async function testEndpoint(method, endpoint, body = null) {
  try {
    const options = {
      method,
      headers: {
        'Content-Type': 'application/json',
      },
    };

    if (body) {
      options.body = JSON.stringify(body);
    }

    console.log(`\n🧪 Testing ${method} ${endpoint}`);
    if (body) {
      console.log('📤 Request body:', JSON.stringify(body, null, 2));
    }

    const response = await fetch(`${BASE_URL}${endpoint}`, options);
    const data = await response.json();

    console.log(`📊 Status: ${response.status}`);
    console.log('📥 Response:', JSON.stringify(data, null, 2));

    return { success: response.ok, data, status: response.status };
  } catch (error) {
    console.error(`❌ Error testing ${method} ${endpoint}:`, error.message);
    return { success: false, error: error.message };
  }
}

async function runTests() {
  console.log('🚀 Starting API endpoint tests...\n');

  // Test 1: GET /api/filters
  await testEndpoint('GET', '/api/filters');

  // Test 2: POST /api/matching with null filterId (original matching)
  await testEndpoint('POST', '/api/matching', { filterId: null });

  // Test 3: POST /api/matching with undefined filterId (original matching)
  await testEndpoint('POST', '/api/matching', { filterId: undefined });

  // Test 4: POST /api/matching with empty string filterId (original matching)
  await testEndpoint('POST', '/api/matching', { filterId: '' });

  // Test 5: POST /api/matching with a sample filterId
  await testEndpoint('POST', '/api/matching', { filterId: 'sample-filter-id' });

  // Test 6: POST /api/filters with a sample filter URL
  await testEndpoint('POST', '/api/filters', { 
    filterUrl: 'https://app.pipedrive.com/organizations?filter_id=12345' 
  });

  // Test 7: POST /api/matching with invalid filterId type
  await testEndpoint('POST', '/api/matching', { filterId: 123 });

  // Test 8: POST /api/filters with missing filterUrl
  await testEndpoint('POST', '/api/filters', {});

  console.log('\n✅ All tests completed!');
  console.log('\n📝 Note: Some tests may fail if the backend Python scripts are not properly configured or if the database is not set up.');
  console.log('   This is expected for the POST endpoints that execute Python scripts.');
}

// Run the tests
runTests().catch(console.error);
