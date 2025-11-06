import os
import shutil
import json
import yaml
from pathlib import Path
import glob
from datetime import datetime

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
            try:
                metadata = yaml.safe_load(yaml_content)
            except yaml.YAMLError:
                metadata = {}
        else:
            metadata = {}
            md_content = content
    else:
        metadata = {}
        md_content = content
    
    return metadata, md_content

def create_html_page(student_data, course_code, target_dir):
    """Create HTML page for student using simple profiles/username.html structure"""
    username = student_data['username']
    
    # Create profiles directory if it doesn't exist
    profiles_dir = target_dir / 'profiles'
    profiles_dir.mkdir(exist_ok=True)
    
    # Create the HTML file directly in profiles folder
    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="{student_data['name']} - Student Portfolio">
    <title>{student_data['name']} - Portfolio</title>
    
    <!-- Favicon -->
    <link rel="icon" type="image/png" href="../assets/img/favicon.png">
    
    <!-- Tailwind CSS -->
    <script src="https://cdn.tailwindcss.com"></script>
    
    <!-- Custom Styles -->
    <link rel="stylesheet" href="../assets/css/style.css">
    
    <!-- Font Awesome -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    
    <script>
        tailwind.config = {{
            theme: {{
                extend: {{
                    colors: {{
                        primary: '#3B82F6',
                        secondary: '#8B5CF6',
                        accent: '#10B981'
                    }}
                }}
            }}
        }}
    </script>
</head>
<body class="bg-gray-50 font-sans">
    <!-- Loading Screen -->
    <div id="loading-screen" class="fixed inset-0 bg-white z-50 flex items-center justify-center">
        <div class="text-center">
            <div class="animate-spin rounded-full h-16 w-16 border-b-2 border-primary mx-auto mb-4"></div>
            <p class="text-gray-600">Loading profile...</p>
        </div>
    </div>

    <!-- Navigation -->
    <nav class="bg-white shadow-lg fixed w-full top-0 z-40">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between h-16">
                <div class="flex items-center">
                    <a href="../index.html" class="flex items-center space-x-2">
                        <i class="fas fa-graduation-cap text-primary text-2xl"></i>
                        <span class="font-bold text-xl text-gray-900">Regis University</span>
                    </a>
                </div>
                <div class="hidden md:flex items-center space-x-8">
                    <a href="../index.html" class="text-gray-700 hover:text-primary transition duration-300">
                        <i class="fas fa-home mr-1"></i>Home
                    </a>
                    <a href="../student-guide.html" class="text-gray-700 hover:text-primary transition duration-300">
                        <i class="fas fa-book mr-1"></i>Student Guide
                    </a>
                    <a href="../instructor-guide.html" class="text-gray-700 hover:text-primary transition duration-300">
                        <i class="fas fa-chalkboard-teacher mr-1"></i>Instructor Guide
                    </a>
                </div>
                <div class="md:hidden flex items-center">
                    <button id="mobile-menu-button" class="text-gray-700 hover:text-primary focus:outline-none">
                        <i class="fas fa-bars text-xl"></i>
                    </button>
                </div>
            </div>
        </div>
        <!-- Mobile Menu -->
        <div id="mobile-menu" class="md:hidden hidden bg-white border-t">
            <div class="px-2 pt-2 pb-3 space-y-1">
                <a href="../index.html" class="block px-3 py-2 text-gray-700 hover:text-primary">
                    <i class="fas fa-home mr-2"></i>Home
                </a>
                <a href="../student-guide.html" class="block px-3 py-2 text-gray-700 hover:text-primary">
                    <i class="fas fa-book mr-2"></i>Student Guide
                </a>
                <a href="../instructor-guide.html" class="block px-3 py-2 text-gray-700 hover:text-primary">
                    <i class="fas fa-chalkboard-teacher mr-2"></i>Instructor Guide
                </a>
            </div>
        </div>
    </nav>

    <!-- Main Content -->
    <div id="main-content" style="display: none;">
        <!-- Content will be populated by JavaScript -->
    </div>

    <!-- Footer -->
    <footer class="bg-gray-900 text-white py-8 mt-16">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="text-center">
                <div class="flex items-center justify-center space-x-2 mb-4">
                    <i class="fas fa-graduation-cap text-2xl"></i>
                    <span class="text-xl font-bold">Regis University</span>
                </div>
                <p class="text-gray-300 mb-2">3333 Regis Blvd, Denver, CO 80221</p>
                <p class="text-gray-300 mb-4">Phone: (800) 388-2366</p>
                <div class="border-t border-gray-700 pt-4">
                    <p class="text-gray-400 text-sm">© 2025 Regis University. All rights reserved.</p>
                </div>
            </div>
        </div>
    </footer>

    <!-- JavaScript -->
    <script src="../assets/js/main.js"></script>
    <script src="../assets/js/markdown-parser.js"></script>
    <script>
        // Profile configuration
        const PROFILE_CONFIG = {{
            username: '{username}',
            course: '{course_code}',
            profilePath: 'https://raw.githubusercontent.com/iamgmujtaba/regis_std/main/data/{course_code}/{username}/profile.md'
        }};

        // Load and render the profile
        document.addEventListener('DOMContentLoaded', async function() {{
            try {{
                // Fetch the markdown profile
                const response = await fetch(PROFILE_CONFIG.profilePath);
                if (!response.ok) {{
                    throw new Error('Profile not found');
                }}
                
                const markdownContent = await response.text();
                
                // Parse and render the markdown
                const parser = new MarkdownParser();
                const htmlContent = parser.generateHTML(markdownContent, PROFILE_CONFIG);
                
                // Update the main content
                document.getElementById('main-content').innerHTML = htmlContent;
                document.getElementById('main-content').style.display = 'block';
                
                // Hide loading screen
                document.getElementById('loading-screen').style.display = 'none';
                
                // Initialize mobile menu
                const mobileMenuButton = document.getElementById('mobile-menu-button');
                const mobileMenu = document.getElementById('mobile-menu');
                
                if (mobileMenuButton && mobileMenu) {{
                    mobileMenuButton.addEventListener('click', function() {{
                        mobileMenu.classList.toggle('hidden');
                    }});
                }}
                
            }} catch (error) {{
                console.error('Error loading profile:', error);
                document.getElementById('loading-screen').innerHTML = `
                    <div class="text-center">
                        <i class="fas fa-exclamation-triangle text-red-500 text-4xl mb-4"></i>
                        <h2 class="text-xl font-bold text-gray-900 mb-2">Profile Not Found</h2>
                        <p class="text-gray-600 mb-4">Unable to load the student profile.</p>
                        <a href="../index.html" class="inline-flex items-center px-4 py-2 bg-primary text-white rounded-lg hover:bg-blue-800 transition duration-300">
                            <i class="fas fa-home mr-2"></i>
                            Return Home
                        </a>
                    </div>
                `;
            }}
        }});
    </script>
</body>
</html>'''
    
    # Write the HTML file directly in profiles folder
    html_file = profiles_dir / f'{username}.html'
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    # Return simple path
    return f'profiles/{username}.html'

def sync_student_data():
    """Sync student data to main portfolio repository"""
    
    # Paths
    source_dir = Path('data')
    target_dir = Path('main-portfolio')
    
    if not source_dir.exists():
        print("❌ Source data directory not found")
        return
        
    if not target_dir.exists():
        print("❌ Main portfolio directory not found")
        return
    
    print(f"📁 Processing data from: {source_dir}")
    print(f"📁 Syncing to: {target_dir}")
    
    # Ensure target directories exist
    (target_dir / 'data').mkdir(exist_ok=True)
    (target_dir / 'profiles').mkdir(exist_ok=True)
    
    # Find all course directories
    for course_dir in source_dir.glob('*/'):
        if not course_dir.is_dir():
            continue
            
        course_code = course_dir.name
        print(f"🔄 Processing course: {course_code}")
        
        course_students = []
        
        # Process each student in the course
        for student_dir in course_dir.glob('*/'):
            if not student_dir.is_dir():
                continue
                
            username = student_dir.name
            profile_path = student_dir / 'profile.md'
            
            print(f"  👤 Processing student: {username}")
            
            if profile_path.exists():
                metadata, content = parse_markdown_profile(profile_path)
                
                # Create student data entry
                student_data = {
                    'username': username,
                    'name': f"{metadata.get('firstName', '')} {metadata.get('lastName', '')}".strip() or username,
                    'email': metadata.get('email', ''),
                    'course': course_code,
                    'semester': metadata.get('semester', 'Spring 2025'),
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
                        print(f"    📸 Found avatar: avatar.{ext}")
                        break
                
                # Find project files
                for pdf_file in student_dir.glob('*.pdf'):
                    student_data['files'].append({
                        'name': pdf_file.name,
                        'path': f'regis_std/data/{course_code}/{username}/{pdf_file.name}',
                        'type': 'pdf'
                    })
                    print(f"    📄 Found PDF: {pdf_file.name}")
                
                # Find image files
                for img_file in student_dir.glob('*.{jpg,jpeg,png}'):
                    if img_file.name.startswith('avatar'):
                        continue
                    student_data['files'].append({
                        'name': img_file.name,
                        'path': f'regis_std/data/{course_code}/{username}/{img_file.name}',
                        'type': 'image'
                    })
                    print(f"    🖼️  Found image: {img_file.name}")
                
                # Create HTML page for this student
                html_path = create_html_page(student_data, course_code, target_dir)
                student_data['profilePage'] = html_path
                print(f"    🌐 Created HTML page: {html_path}")
                
                course_students.append(student_data)
                print(f"    ✅ Processed {student_data['name']} ({username})")
            else:
                print(f"    ⚠️  No profile.md found for {username}")
        
        # Create separate JSON file for this semester/course
        semester_json_path = target_dir / 'data' / f'students_{course_code}.json'
        
        semester_data = {
            'course': {
                'code': course_code.upper(),
                'name': f'Data Science Practicum - {course_code.upper()}',
                'semester': 'Spring 2025',
                'year': '2025',
                'description': f'Student portfolios for {course_code.upper()} - Data Science Practicum course at Regis University.'
            },
            'university': {
                'name': 'Regis University',
                'phone': '(800) 388-2366',
                'address': '3333 Regis Blvd, Denver, CO 80221',
                'website': 'https://www.regis.edu'
            },
            'students': course_students,
            'spotlight': [],  # Can be populated later
            'statistics': {
                'totalStudents': len(course_students),
                'totalProjects': len(course_students) * 2,  # Assuming 2 projects per student
                'lastUpdated': datetime.now().isoformat()
            },
            'metadata': {
                'dataSource': 'regis_std repository',
                'syncedAt': datetime.now().isoformat(),
                'version': '1.0'
            }
        }
        
        # Write semester-specific JSON file
        with open(semester_json_path, 'w', encoding='utf-8') as f:
            json.dump(semester_data, f, indent=2, ensure_ascii=False)
        
        print(f"📊 Created {course_code} data file with {len(course_students)} students")
        print(f"📁 Saved: {semester_json_path}")
        
        # Update main students.json to reference the new semester
        main_students_json = target_dir / 'data' / 'students.json'
        if main_students_json.exists():
            with open(main_students_json, 'r', encoding='utf-8') as f:
                main_data = json.load(f)
        else:
            main_data = {
                'university': {
                    'name': 'Regis University',
                    'phone': '(800) 388-2366',
                    'address': '3333 Regis Blvd, Denver, CO 80221',
                    'website': 'https://www.regis.edu'
                },
                'currentSemester': 'spring-2025',
                'semesters': {},
                'spotlightProjects': []
            }
        
        # Add/update semester reference in main file
        semester_key = course_code.replace('_', '-')
        main_data['semesters'][semester_key] = {
            'name': f'Spring 2025 - {course_code.upper()}',
            'course': course_code.upper(),
            'students': course_students,
            'dataFile': f'data/students_{course_code}.json',
            'htmlPath': 'profiles/',
            'spotlight': []
        }
        
        # Update current semester if this is the most recent
        main_data['currentSemester'] = semester_key
        
        # Write updated main students.json
        with open(main_students_json, 'w', encoding='utf-8') as f:
            json.dump(main_data, f, indent=2, ensure_ascii=False)
        
        print(f"📊 Updated main students.json with {course_code} reference")

    print(f"✅ Sync completed successfully!")

if __name__ == "__main__":
    print("🔄 Starting enhanced sync process...")
    sync_student_data()
    print("✅ Enhanced sync completed!")