#!/usr/bin/env python3
"""
Test script to verify graceful error handling when backend is unavailable.
This script simulates frontend behavior when the backend is not running.
"""

import requests
import json
from typing import Dict, Any

def test_memory_api_error_handling():
    """
    Test that the memory API handles errors gracefully when backend is unavailable.
    """
    print("Testing memory API error handling...")
    
    # Test GET /api/memory when backend is unavailable
    try:
        response = requests.get('http://localhost:3001/api/memory', timeout=5)
        data = response.json()
        
        print(f"GET /api/memory response: {data}")
        
        # Check if response follows expected error format
        if 'success' in data and not data['success']:
            print("✅ GET request handled gracefully - returned default values")
            print(f"   Summary: '{data.get('summary', 'N/A')}'")
            print(f"   Message Count: {data.get('messageCount', 'N/A')}")
            print(f"   Error: {data.get('error', 'N/A')}")
        else:
            print("❌ GET request did not handle error gracefully")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ GET request failed with network error: {e}")
    
    print()
    
    # Test POST /api/memory (clear action) when backend is unavailable
    try:
        response = requests.post(
            'http://localhost:3001/api/memory',
            json={'action': 'clear'},
            timeout=5
        )
        data = response.json()
        
        print(f"POST /api/memory response: {data}")
        
        # Check if response follows expected error format
        if 'success' in data and not data['success']:
            print("✅ POST request handled gracefully - returned error info")
            print(f"   Error: {data.get('error', 'N/A')}")
        else:
            print("❌ POST request did not handle error gracefully")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ POST request failed with network error: {e}")

def test_chat_api_error_handling():
    """
    Test that the chat API handles errors gracefully when backend is unavailable.
    """
    print("\nTesting chat API error handling...")
    
    try:
        response = requests.post(
            'http://localhost:3001/api/chat',
            json={'message': 'Hello, test message'},
            timeout=5
        )
        
        print(f"Chat API status: {response.status_code}")
        
        if response.status_code >= 400:
            print("✅ Chat API returned appropriate error status")
        else:
            print("❌ Chat API did not return error status when backend unavailable")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Chat API request failed with network error: {e}")

def main():
    print("Error Handling Test Suite")
    print("=" * 50)
    print("This test verifies that the frontend handles backend unavailability gracefully.")
    print("Make sure the frontend is running on http://localhost:3001")
    print("Make sure the backend is NOT running on http://localhost:5001")
    print()
    
    test_memory_api_error_handling()
    test_chat_api_error_handling()
    
    print("\n" + "=" * 50)
    print("Test completed. Check the results above.")
    print("\nExpected behavior:")
    print("- Memory API should return default values with success=false")
    print("- No exceptions should be thrown")
    print("- Frontend should continue to work despite backend unavailability")

if __name__ == '__main__':
    main()