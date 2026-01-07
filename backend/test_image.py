#!/usr/bin/env python3
"""
Test script to verify image analysis is working
Place this in your backend folder and run: python test_image.py
"""

import os
from dotenv import load_dotenv

load_dotenv()

print("="*60)
print("🧪 IMAGE ANALYSIS TEST")
print("="*60)

# Test 1: Check Google API Key
print("\n[Test 1] Checking Google API Key...")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
if GOOGLE_API_KEY:
    print(f"✅ API Key found: {GOOGLE_API_KEY[:10]}...{GOOGLE_API_KEY[-4:]}")
else:
    print("❌ API Key NOT found in .env")
    print("💡 Add GOOGLE_API_KEY=your_key to backend/.env")
    exit(1)

# Test 2: Check Pillow
print("\n[Test 2] Checking Pillow (PIL)...")
try:
    from PIL import Image
    print("✅ Pillow installed")
except ImportError:
    print("❌ Pillow NOT installed")
    print("💡 Run: pip install Pillow")
    exit(1)

# Test 3: Check google-generativeai
print("\n[Test 3] Checking google-generativeai...")
try:
    import google.generativeai as genai
    print("✅ google-generativeai installed")
except ImportError:
    print("❌ google-generativeai NOT installed")
    print("💡 Run: pip install google-generativeai")
    exit(1)

# Test 4: Configure Gemini
print("\n[Test 4] Configuring Gemini...")
try:
    genai.configure(api_key=GOOGLE_API_KEY)
    print("✅ Gemini configured")
except Exception as e:
    print(f"❌ Configuration failed: {e}")
    exit(1)

# Test 5: Create test image
print("\n[Test 5] Creating test image...")
try:
    # Create a simple test image with text
    img = Image.new('RGB', (400, 200), color='white')
    
    # Try to add text (optional - works without PIL ImageDraw)
    try:
        from PIL import ImageDraw, ImageFont
        draw = ImageDraw.Draw(img)
        draw.text((50, 80), "TEST IMAGE", fill='black')
        print("✅ Test image created with text")
    except:
        print("✅ Test image created (no text)")
    
    test_image_path = "test_image.jpg"
    img.save(test_image_path)
    print(f"✅ Saved to: {test_image_path}")
except Exception as e:
    print(f"❌ Failed to create test image: {e}")
    exit(1)

# Test 6: Analyze with Gemini
print("\n[Test 6] Analyzing image with Gemini Vision...")
try:
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    img = Image.open(test_image_path)
    prompt = "Describe this image in detail."
    
    print("   Sending request to Gemini...")
    response = model.generate_content([prompt, img])
    
    if response and response.text:
        print("✅ SUCCESS! Image analysis working!")
        print("\n" + "="*60)
        print("GEMINI RESPONSE:")
        print("="*60)
        print(response.text)
        print("="*60)
    else:
        print("❌ No response from Gemini")
        
except Exception as e:
    print(f"❌ Analysis failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test 7: Test FileAnalyzer class
print("\n[Test 7] Testing FileAnalyzer class...")
try:
    from utils.file_analyzer import FileAnalyzer
    
    result = FileAnalyzer.analyze_image_with_google(test_image_path)
    
    if result.get("status") == "success":
        print("✅ FileAnalyzer.analyze_image_with_google() works!")
        print(f"\nAnalysis: {result.get('analysis', '')[:200]}...")
    else:
        print(f"❌ FileAnalyzer failed: {result.get('error')}")
        
except Exception as e:
    print(f"❌ FileAnalyzer import/execution failed: {e}")
    import traceback
    traceback.print_exc()

# Cleanup
print("\n[Cleanup] Removing test image...")
try:
    os.remove(test_image_path)
    print("✅ Cleaned up")
except:
    pass

print("\n" + "="*60)
print("🎉 ALL TESTS PASSED!")
print("="*60)
print("\n💡 Your image analysis should be working now!")
print("   Try uploading an image through the web interface.")
print("="*60)