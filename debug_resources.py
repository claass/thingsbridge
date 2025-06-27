#!/usr/bin/env python3
"""Debug script to verify MCP resources are working correctly."""

import json
import sys
from thingsbridge.server import mcp

def test_resource_registration():
    """Test that resources are properly registered."""
    print("🔍 Testing Resource Registration...")
    
    # Check if resource manager exists
    if hasattr(mcp, '_resource_manager'):
        rm = mcp._resource_manager
        print(f"✅ Resource manager found: {type(rm)}")
        
        # Get registered resources
        if hasattr(rm, '_resources'):
            resources = rm._resources
            print(f"✅ Found {len(resources)} registered resources:")
            for uri, resource in resources.items():
                print(f"   - {uri}: {resource.name}")
            return True
        else:
            print("❌ No _resources attribute in resource manager")
    else:
        print("❌ No resource manager found")
    
    return False

def test_resource_discovery():
    """Test MCP resource discovery (what clients see)."""
    print("\n🔍 Testing Resource Discovery...")
    
    try:
        # Simulate MCP resources/list call
        from fastmcp.core.types import ListResourcesRequest
        
        request = ListResourcesRequest()
        
        # This is what MCP clients call to discover resources
        if hasattr(mcp, '_list_resources'):
            response = mcp._list_resources(request)
            print(f"✅ Resource discovery works!")
            print(f"✅ Client would see {len(response.resources)} resources:")
            
            for resource in response.resources:
                print(f"   - URI: {resource.uri}")
                print(f"     Name: {resource.name}")
                print(f"     Description: {resource.description}")
                print(f"     MIME Type: {resource.mimeType}")
                print()
            return True
        else:
            print("❌ No _list_resources method found")
            
    except Exception as e:
        print(f"❌ Error during resource discovery: {e}")
    
    return False

def test_resource_reading():
    """Test actually reading the resources."""
    print("🔍 Testing Resource Reading...")
    
    test_uris = [
        "things://areas",
        "things://projects", 
        "things://today",
        "things://inbox"
    ]
    
    success_count = 0
    
    for uri in test_uris:
        try:
            print(f"\n📖 Testing {uri}...")
            
            # Simulate MCP resources/read call
            from fastmcp.core.types import ReadResourceRequest
            
            request = ReadResourceRequest(uri=uri)
            
            if hasattr(mcp, '_read_resource'):
                response = mcp._read_resource(request)
                print(f"✅ {uri} readable!")
                
                # Try to parse as JSON to verify format
                if response.contents:
                    content = response.contents[0]
                    if content.mimeType == "application/json":
                        try:
                            data = json.loads(content.text)
                            print(f"   📊 Contains {len(data)} items")
                            if data:
                                print(f"   📝 Sample: {data[0] if isinstance(data, list) else list(data.keys())[:3]}")
                        except json.JSONDecodeError:
                            print(f"   ⚠️  Content is not valid JSON")
                    else:
                        print(f"   📄 Content type: {content.mimeType}")
                        print(f"   📝 Preview: {content.text[:100]}...")
                
                success_count += 1
            else:
                print(f"❌ No _read_resource method")
                
        except Exception as e:
            print(f"❌ Error reading {uri}: {e}")
    
    print(f"\n📊 Resource Reading Results: {success_count}/{len(test_uris)} successful")
    return success_count == len(test_uris)

def main():
    """Run all resource tests."""
    print("=" * 60)
    print("🧪 MCP Resource Testing Suite")
    print("=" * 60)
    
    tests = [
        ("Resource Registration", test_resource_registration),
        ("Resource Discovery", test_resource_discovery), 
        ("Resource Reading", test_resource_reading)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'=' * 20} {test_name} {'=' * 20}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 Test Summary")
    print("=" * 60)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 All tests passed! Your MCP resources are working correctly.")
        print("💡 If LLMs aren't using them, it's due to client behavior, not your server.")
    else:
        print("\n🔧 Some tests failed. Check the errors above for debugging.")
    
    return passed == len(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)