import os
import shutil
import json
import yaml
from pathlib import Path
import glob

def parse_markdown_profile(md_path):
    """Parse markdown profile and extract metadata"""
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract YAML front matter
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            yaml_content = parts[1]
            md_content = parts[2]
            metadata = yaml.safe_load(yaml_content)
        else:
            metadata = {}
            md_content = content
    else:
        metadata = {}
        md_content = content
    
    return metadata, md_content

def sync_student_data():
    """Sync student data to main portfolio repository"""
    
    # Paths
    source_dir = Path('data')
    target_dir = Path('main-portfolio')
    
    students_data = {}
    
    # Find all course directories
    for course_dir in source_dir.glob('*/'):
        if not course_dir.is_dir():
            continue
            
        course_code = course_dir.name
        students_data[course_code] = {
            'students': [],
            'semester': 'Spring 2025'  # Extract from CSV if needed
        }
        
        # Process each student in the course
        for student_dir in course_dir.glob('*/'):
            if not student_dir.is_dir():
                continue
                
            username = student_dir.name
            profile_path = student_dir / 'profile.md'
            
            if profile_path.exists():
                metadata, content = parse_markdown_profile(profile_path)
                
                # Create student data entry
                student_data = {
                    'username': username,
                    'name': f"{metadata.get('firstName', '')} {metadata.get('lastName', '')}".strip(),
                    'email': metadata.get('email', ''),
                    'course': course_code,
                    'profilePath': f'regis_std/data/{course_code}/{username}/profile.md',
                    'avatarPath': None,
                    'projects': [],
                    'files': []
                }
                
                # Find avatar
                for ext in ['jpg', 'jpeg', 'png']:
                    avatar_path = student_dir / f'avatar.{ext}'
                    if avatar_path.exists():
                        student_data['avatarPath'] = f'regis_std/data/{course_code}/{username}/avatar.{ext}'
                        break
                
                # Find project files
                for pdf_file in student_dir.glob('*.pdf'):
                    student_data['files'].append({
                        'name': pdf_file.name,
                        'path': f'regis_std/data/{course_code}/{username}/{pdf_file.name}',
                        'type': 'pdf'
                    })
                
                # Find image files
                for img_file in student_dir.glob('*.{jpg,jpeg,png}'):
                    if img_file.name.startswith('avatar'):
                        continue
                    student_data['files'].append({
                        'name': img_file.name,
                        'path': f'regis_std/data/{course_code}/{username}/{img_file.name}',
                        'type': 'image'
                    })
                
                students_data[course_code]['students'].append(student_data)
                print(f"✅ Processed {student_data['name']} ({username})")
    
    # Update main portfolio's students.json
    portfolio_data_dir = target_dir / 'data'
    portfolio_data_dir.mkdir(exist_ok=True)
    
    students_json_path = portfolio_data_dir / 'students.json'
    
    # Load existing data if it exists
    if students_json_path.exists():
        with open(students_json_path, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
    else:
        existing_data = {
            'university': {
                'name': 'Regis University',
                'phone': '(800) 388-2366',
                'address': '3333 Regis Blvd, Denver, CO 80221',
                'website': 'https://www.regis.edu'
            },
            'currentSemester': 'spring-2025',
            'semesters': {}
        }
    
    # Update semester data
    for course_code, course_data in students_data.items():
        semester_key = 'spring-2025'  # Adjust based on your naming convention
        existing_data['semesters'][semester_key] = {
            'name': 'Spring 2025',
            'course': course_code.upper(),
            'students': course_data['students'],
            'spotlight': existing_data['semesters'].get(semester_key, {}).get('spotlight', [])
        }
    
    # Write updated data
    with open(students_json_path, 'w', encoding='utf-8') as f:
        json.dump(existing_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Updated portfolio data with {sum(len(course['students']) for course in students_data.values())} students")

if __name__ == "__main__":
    sync_student_data()