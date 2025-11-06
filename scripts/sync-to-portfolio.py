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

def create_html_page(student_data, course_code, target_dir, markdown_content, metadata):
    """Create HTML page for student with embedded content"""
    username = student_data['username']
    
    # Create profiles directory if it doesn't exist
    profiles_dir = target_dir / 'profiles'
    profiles_dir.mkdir(exist_ok=True)
    
    # Parse the markdown content using the existing parser logic
    # Extract sections from markdown
    sections = parse_markdown_sections(markdown_content)
    
    # Create the HTML file with embedded content
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
    <main class="pt-16">
        <!-- Hero Section -->
        <section class="bg-gradient-to-br from-primary to-secondary text-white py-20">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="text-center">
                    <div class="mb-8">
                        <div class="w-32 h-32 mx-auto bg-white/10 rounded-full flex items-center justify-center backdrop-blur-sm">
                            <i class="fas fa-user text-6xl text-white/80"></i>
                        </div>
                    </div>
                    <h1 class="text-4xl md:text-5xl font-bold mb-4">{metadata.get('firstName', '')} {metadata.get('lastName', '')}</h1>
                    <p class="text-xl text-blue-100 mb-6">Data Science Student at Regis University</p>
                    <div class="flex flex-wrap justify-center gap-4">
                        <a href="mailto:{metadata.get('email', '')}" class="inline-flex items-center px-6 py-3 bg-white text-primary rounded-full hover:bg-gray-100 transition duration-300">
                            <i class="fas fa-envelope mr-2"></i>
                            Contact Me
                        </a>
                        <a href="#about" class="inline-flex items-center px-6 py-3 border-2 border-white text-white rounded-full hover:bg-white hover:text-primary transition duration-300">
                            <i class="fas fa-user mr-2"></i>
                            Learn More
                        </a>
                    </div>
                </div>
            </div>
        </section>

        <!-- About Section -->
        <section id="about" class="py-16 bg-white">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="text-center mb-12">
                    <h2 class="text-3xl font-bold text-gray-900 mb-4">About Me</h2>
                    <div class="w-20 h-1 bg-primary mx-auto"></div>
                </div>
                <div class="max-w-4xl mx-auto">
                    <div class="prose prose-lg mx-auto text-gray-600">
                        {sections.get('about', '<p>Edit your profile.md file to add information about yourself, your background, and your interests in data science.</p>')}
                    </div>
                </div>
            </div>
        </section>

        <!-- Skills Section -->
        <section class="py-16 bg-gray-50">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="text-center mb-12">
                    <h2 class="text-3xl font-bold text-gray-900 mb-4">Skills</h2>
                    <div class="w-20 h-1 bg-primary mx-auto"></div>
                </div>
                <div class="max-w-4xl mx-auto">
                    {sections.get('skills', generate_default_skills())}
                </div>
            </div>
        </section>

        <!-- Projects Section -->
        <section class="py-16 bg-white">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="text-center mb-12">
                    <h2 class="text-3xl font-bold text-gray-900 mb-4">Projects</h2>
                    <div class="w-20 h-1 bg-primary mx-auto"></div>
                </div>
                <div class="grid md:grid-cols-2 gap-8 max-w-6xl mx-auto">
                    {sections.get('practicum1', generate_default_project('Practicum I'))}
                    {sections.get('practicum2', generate_default_project('Practicum II'))}
                </div>
            </div>
        </section>

        <!-- Contact Section -->
        <section class="py-16 bg-gradient-to-br from-gray-900 to-gray-800 text-white">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="text-center mb-12">
                    <h2 class="text-3xl font-bold mb-4">Get In Touch</h2>
                    <div class="w-20 h-1 bg-primary mx-auto"></div>
                </div>
                <div class="max-w-4xl mx-auto">
                    {sections.get('contact', generate_default_contact(metadata))}
                </div>
            </div>
        </section>
    </main>

    <!-- Footer -->
    <footer class="bg-gray-900 text-white py-8">
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
    <script>
        // Mobile menu functionality
        document.addEventListener('DOMContentLoaded', function() {{
            const mobileMenuButton = document.getElementById('mobile-menu-button');
            const mobileMenu = document.getElementById('mobile-menu');
            
            if (mobileMenuButton && mobileMenu) {{
                mobileMenuButton.addEventListener('click', function() {{
                    mobileMenu.classList.toggle('hidden');
                }});
            }}
            
            // Smooth scrolling for anchor links
            document.querySelectorAll('a[href^="#"]').forEach(anchor => {{
                anchor.addEventListener('click', function (e) {{
                    e.preventDefault();
                    const target = document.querySelector(this.getAttribute('href'));
                    if (target) {{
                        target.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
                    }}
                }});
            }});
        }});
    </script>
</body>
</html>'''
    
    # Write the HTML file directly in profiles folder
    html_file = profiles_dir / f'{username}.html'
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"    🌐 Created HTML page: profiles/{username}.html")
    
    return f'profiles/{username}.html'

def parse_markdown_sections(content):
    """Parse markdown content into sections"""
    sections = {}
    
    # Simple section parsing
    lines = content.split('\n')
    current_section = None
    current_content = []
    
    for line in lines:
        if line.startswith('## '):
            # Save previous section
            if current_section:
                sections[current_section] = '\n'.join(current_content)
            
            # Start new section
            section_name = line[3:].strip().lower()
            if 'about' in section_name:
                current_section = 'about'
            elif 'skill' in section_name:
                current_section = 'skills'
            elif 'practicum i' in section_name:
                current_section = 'practicum1'
            elif 'practicum ii' in section_name:
                current_section = 'practicum2'
            elif 'contact' in section_name:
                current_section = 'contact'
            else:
                current_section = section_name.replace(' ', '_')
            
            current_content = []
        else:
            if current_section:
                current_content.append(line)
    
    # Save last section
    if current_section:
        sections[current_section] = '\n'.join(current_content)
    
    return sections

def generate_default_skills():
    """Generate default skills HTML"""
    return '''
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div class="bg-gradient-to-br from-blue-50 to-blue-100 p-4 rounded-lg text-center border border-blue-200">
            <i class="fas fa-code text-primary text-3xl mb-2"></i>
            <p class="font-semibold">Programming</p>
            <p class="text-sm text-gray-600">Python, R, SQL</p>
        </div>
        <div class="bg-gradient-to-br from-green-50 to-green-100 p-4 rounded-lg text-center border border-green-200">
            <i class="fas fa-chart-bar text-green-600 text-3xl mb-2"></i>
            <p class="font-semibold">Analytics</p>
            <p class="text-sm text-gray-600">Data Analysis</p>
        </div>
        <div class="bg-gradient-to-br from-purple-50 to-purple-100 p-4 rounded-lg text-center border border-purple-200">
            <i class="fas fa-brain text-purple-600 text-3xl mb-2"></i>
            <p class="font-semibold">Machine Learning</p>
            <p class="text-sm text-gray-600">Scikit-learn</p>
        </div>
        <div class="bg-gradient-to-br from-red-50 to-red-100 p-4 rounded-lg text-center border border-red-200">
            <i class="fas fa-chart-line text-red-600 text-3xl mb-2"></i>
            <p class="font-semibold">Visualization</p>
            <p class="text-sm text-gray-600">Matplotlib, Seaborn</p>
        </div>
    </div>
    '''

def generate_default_project(title):
    """Generate default project HTML"""
    return f'''
    <div class="bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden">
        <div class="bg-gradient-to-r from-primary to-secondary h-2"></div>
        <div class="p-6">
            <h3 class="text-xl font-bold text-gray-900 mb-3">{title} Project</h3>
            <p class="text-gray-600 mb-4">Edit your profile.md file to add information about your {title.lower()} project.</p>
            <div class="flex flex-wrap gap-2 mb-4">
                <span class="bg-blue-100 text-blue-800 px-2 py-1 rounded-full text-sm">Python</span>
                <span class="bg-green-100 text-green-800 px-2 py-1 rounded-full text-sm">Data Science</span>
            </div>
            <div class="flex flex-wrap gap-2">
                <a href="#" class="inline-flex items-center px-3 py-2 bg-gray-100 text-gray-700 rounded-lg text-sm">
                    <i class="fab fa-github mr-2"></i>GitHub
                </a>
                <a href="#" class="inline-flex items-center px-3 py-2 bg-gray-100 text-gray-700 rounded-lg text-sm">
                    <i class="fas fa-file-pdf mr-2"></i>Report
                </a>
            </div>
        </div>
    </div>
    '''

def generate_default_contact(metadata):
    """Generate default contact HTML"""
    email = metadata.get('email', '')
    return f'''
    <div class="grid md:grid-cols-3 gap-6 text-center">
        <div class="bg-white/10 backdrop-blur-sm rounded-lg p-6">
            <i class="fas fa-envelope text-3xl text-primary mb-4"></i>
            <h3 class="font-semibold mb-2">Email</h3>
            <a href="mailto:{email}" class="text-gray-300 hover:text-white">{email}</a>
        </div>
        <div class="bg-white/10 backdrop-blur-sm rounded-lg p-6">
            <i class="fab fa-linkedin text-3xl text-primary mb-4"></i>
            <h3 class="font-semibold mb-2">LinkedIn</h3>
            <a href="#" class="text-gray-300 hover:text-white">Connect with me</a>
        </div>
        <div class="bg-white/10 backdrop-blur-sm rounded-lg p-6">
            <i class="fab fa-github text-3xl text-primary mb-4"></i>
            <h3 class="font-semibold mb-2">GitHub</h3>
            <a href="#" class="text-gray-300 hover:text-white">View my code</a>
        </div>
    </div>
    '''

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
                
                # Create HTML page for this student with embedded content
                html_path = create_html_page(student_data, course_code, target_dir, content, metadata)
                student_data['profilePage'] = html_path
                
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
            'spotlight': [],
            'statistics': {
                'totalStudents': len(course_students),
                'totalProjects': len(course_students) * 2,
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

    print(f"✅ Sync completed successfully!")

if __name__ == "__main__":
    print("🔄 Starting enhanced sync process...")
    sync_student_data()
    print("✅ Enhanced sync completed!")