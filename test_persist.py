"""Test base64 image persistence"""
import sys, io, os
sys.stdout.reconfigure(encoding='utf-8')
os.chdir(r'D:\Quant_Projects\Quant_Projects\buffet-demo')

from app import app, get_dish_library, SmartMatcher

client = app.test_client()

# Test: upload reference image via admin route
with open(r'D:\Quant_Projects\Quant_Projects\buffet-demo\static\composites\.gitkeep', 'rb') as f:
    pass  # need a real image

# Create a test image
from PIL import Image
test_img = io.BytesIO()
Image.new('RGB', (300, 200), color=(255, 200, 100)).save(test_img, format='JPEG')
test_img.seek(0)

print('=== Upload reference image ===')
resp = client.post('/admin/library/guobaorou/upload_ref',
    data={'reference_image': (test_img, 'test_guobaorou.jpg')},
    content_type='multipart/form-data',
    follow_redirects=True)
print(f'Status: {resp.status_code}')
if resp.status_code != 200:
    print(resp.data.decode('utf-8', errors='ignore')[:500])
else:
    # Check dish library
    lib = get_dish_library()
    dish = lib.get_dish('guobaorou')
    refs = dish.get('reference_images', [])
    print(f'Reference images count: {len(refs)}')
    if refs:
        uri_preview = refs[0][:80]
        print(f'First ref starts with: {uri_preview}...')
        print('✅ Base64 image stored in JSON!')

# Test: reload library (simulate page refresh/redeploy)
print('\n=== Simulate page refresh ===')
lib2 = get_dish_library()
dish2 = lib2.get_dish('guobaorou')
refs2 = dish2.get('reference_images', [])
print(f'After reload - reference images count: {len(refs2)}')
if len(refs2) > 0:
    print('✅ Images persist after reload!')
else:
    print('❌ Images lost!')

# Test: SmartMatcher can use base64 images
print('\n=== Test SmartMatcher with base64 refs ===')
sm = SmartMatcher(lib)
print(f'Profiles computed: {len(sm.profiles)}')
if sm.profiles:
    print('✅ SmartMatcher works with base64 reference images')
else:
    print('⚠️ SmartMatcher has no profiles (might need more than 1 image)')

# Test: get_reference_images returns file paths
paths = lib.get_reference_images('guobaorou')
print(f'\nFile paths available: {len(paths)}')
if paths:
    print(f'First path: {paths[0]}')
    print(f'File exists: {os.path.exists(paths[0])}')
