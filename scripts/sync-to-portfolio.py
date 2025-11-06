import os
import shutil
import json
import yaml
from pathlib import Path
import glob
from datetime import datetime
import re

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

def find_student_files(student_dir, course_code, username):
    """Find all student files (images, PDFs) and generate URLs"""
    files = {
        'avatar_url': None,
        'images': [],
        'pdfs': []
    }
    
    # base_url = f"https://raw.githubusercontent.com/iamgmujtaba/regis_std/main/data/{course_code}/{username}"
    # base_url = f"https://github.com/iamgmujtaba/regis_std/blob/main/data/{course_code}/{username}"
    base_url = f"https://raw.githubusercontent.com/iamgmujtaba/regis_std/main/data/{course_code}/{username}"

    # Find avatar (priority: webp > jpg > png)
    for ext in ['webp', 'jpg', 'jpeg', 'png']:
        avatar_path = student_dir / f'avatar.{ext}'
        if avatar_path.exists():
            files['avatar_url'] = f"{base_url}/avatar.{ext}"
            print(f"    📸 Found avatar: avatar.{ext} -> {files['avatar_url']}")
            break
    
    # Find all images
    for img_file in student_dir.glob('*.{jpg,jpeg,png,webp}'):
        if not img_file.name.startswith('avatar'):
            img_url = f"{base_url}/{img_file.name}"
            files['images'].append({
                'name': img_file.name,
                'url': img_url,
                'type': 'image'
            })
            print(f"    🖼️  Found image: {img_file.name}")
    
    # Find all PDFs
    for pdf_file in student_dir.glob('*.pdf'):
        pdf_url = f"{base_url}/{pdf_file.name}"
        files['pdfs'].append({
            'name': pdf_file.name,
            'url': pdf_url,
            'type': 'pdf'
        })
        print(f"    📄 Found PDF: {pdf_file.name}")
    
    return files

def parse_markdown_sections(content):
    """Parse markdown content into sections exactly as students write them"""
    sections = {
        'about': '', 
        'skills': [], 
        'practicum1': {}, 
        'practicum2': {}, 
        'contact': {}
    }
    
    lines = content.split('\n')
    current_section = None
    current_content = []
    
    for line in lines:
        line = line.strip()
        
        if line.startswith('## '):
            # Save previous section
            if current_section:
                sections[current_section] = '\n'.join(current_content).strip()
            
            # Start new section
            section_name = line[3:].strip().lower()
            current_content = []
            
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
                current_section = None
        else:
            if current_section and line:
                current_content.append(line)
    
    # Save last section
    if current_section:
        sections[current_section] = '\n'.join(current_content).strip()
    
    # Parse skills into structured format
    if sections['skills']:
        sections['skills'] = parse_skills_section(sections['skills'])
    
    # Parse project sections
    if sections['practicum1']:
        sections['practicum1'] = parse_project_section(sections['practicum1'])
    
    if sections['practicum2']:
        sections['practicum2'] = parse_project_section(sections['practicum2'])
    
    # Parse contact section
    if sections['contact']:
        sections['contact'] = parse_contact_section(sections['contact'])
    
    return sections

def parse_skills_section(skills_text):
    """Parse skills section into categories"""
    skills = {}
    current_category = None
    
    for line in skills_text.split('\n'):
        line = line.strip()
        if line.startswith('**') and line.endswith(':**'):
            current_category = line[2:-3].strip()
            skills[current_category] = []
        elif line.startswith('- ') and current_category:
            skill = line[2:].strip()
            skills[current_category].append(skill)
    
    return skills

def parse_project_section(project_text):
    """Parse project section into structured data"""
    project = {
        'title': '',
        'tags': [],
        'abstract': '',
        'achievements': [],
        'github': '#',
        'report': '#',
        'slides': '#',
        'demo': '#'
    }
    
    current_field = None
    
    for line in project_text.split('\n'):
        line = line.strip()
        
        if line.startswith('**Title:**'):
            project['title'] = line[10:].strip()
        elif line.startswith('**Tags:**'):
            tags = line[9:].strip()
            project['tags'] = [tag.strip() for tag in tags.split(',') if tag.strip()]
        elif line.startswith('**Abstract:**'):
            project['abstract'] = line[13:].strip()
            current_field = 'abstract'
        elif line.startswith('**Key Achievements:**'):
            current_field = 'achievements'
        elif line.startswith('**Links:**'):
            current_field = 'links'
        elif line.startswith('- '):
            if current_field == 'achievements':
                project['achievements'].append(line[2:].strip())
            elif current_field == 'links':
                link_text = line[2:].strip()
                if '[GitHub Repository]' in link_text:
                    match = re.search(r'\[GitHub Repository\]\((.*?)\)', link_text)
                    if match:
                        project['github'] = match.group(1)
                elif '[Project Report]' in link_text:
                    match = re.search(r'\[Project Report\]\((.*?)\)', link_text)
                    if match:
                        project['report'] = match.group(1)
                elif '[Presentation Slides]' in link_text:
                    match = re.search(r'\[Presentation Slides\]\((.*?)\)', link_text)
                    if match:
                        project['slides'] = match.group(1)
                elif '[Live Demo]' in link_text or '[Demo]' in link_text:
                    match = re.search(r'\[.*?Demo.*?\]\((.*?)\)', link_text)
                    if match:
                        project['demo'] = match.group(1)
        elif current_field == 'abstract' and line and not line.startswith('**'):
            project['abstract'] += ' ' + line
    
    return project

def parse_contact_section(contact_text):
    """Parse contact section"""
    contact = {
        'email': '',
        'linkedin': '#',
        'github': '#',
        'portfolio': '#'
    }
    
    for line in contact_text.split('\n'):
        line = line.strip()
        if line.startswith('**Email:**'):
            contact['email'] = line[10:].strip()
        elif line.startswith('**LinkedIn:**'):
            match = re.search(r'\[.*?\]\((.*?)\)', line)
            if match:
                contact['linkedin'] = match.group(1)
        elif line.startswith('**GitHub:**'):
            match = re.search(r'\[.*?\]\((.*?)\)', line)
            if match:
                contact['github'] = match.group(1)
        elif line.startswith('**Portfolio:**'):
            match = re.search(r'\[.*?\]\((.*?)\)', line)
            if match:
                contact['portfolio'] = match.group(1)
    
    return contact

def generate_project_html(project_data, title, gradient_color, student_files, course_code, username):
    """Generate project HTML with proper PDF links"""
    if not project_data or not project_data.get('title'):
        # Default project template
        return f'''
        <div class="bg-white rounded-lg shadow-lg overflow-hidden mb-8 border border-gray-200 hover:shadow-xl transition duration-300">
            <div class="bg-gradient-to-r from-{gradient_color} to-blue-600 px-6 py-4">
                <h3 class="text-2xl font-bold text-white flex items-center">
                    <i class="fas fa-project-diagram mr-3"></i>
                    {title} Project
                </h3>
            </div>
            <div class="p-6">
                <h4 class="text-xl font-bold text-gray-900 mb-3">
                    [Edit your profile.md to add {title.lower()} project details]
                </h4>
                
                <div class="mb-4">
                    <span class="inline-block bg-blue-100 text-blue-800 text-xs font-semibold px-3 py-1 rounded-full mr-2">
                        <i class="fas fa-tag mr-1"></i> Add Tags
                    </span>
                </div>

                <p class="text-gray-700 mb-4 leading-relaxed">
                    <strong>Abstract:</strong> Please edit your profile.md file to add your project abstract and details.
                </p>

                <div class="flex flex-wrap gap-3 mt-6">
                    <a href="#" class="inline-flex items-center px-4 py-2 bg-gray-300 text-gray-600 rounded-lg cursor-not-allowed">
                        <i class="fab fa-github mr-2"></i> View Code
                    </a>
                    <a href="#" class="inline-flex items-center px-4 py-2 bg-gray-300 text-gray-600 rounded-lg cursor-not-allowed">
                        <i class="fas fa-file-pdf mr-2"></i> Read Report
                    </a>
                    <a href="#" class="inline-flex items-center px-4 py-2 bg-gray-300 text-gray-600 rounded-lg cursor-not-allowed">
                        <i class="fas fa-presentation mr-2"></i> View Slides
                    </a>
                </div>
            </div>
        </div>'''
    
    # Generate tags HTML
    tags_html = ''
    for tag in project_data.get('tags', []):
        color = 'blue' if 'Python' in tag else 'green' if 'Data' in tag else 'purple'
        tags_html += f'''
        <span class="inline-block bg-{color}-100 text-{color}-800 text-xs font-semibold px-3 py-1 rounded-full mr-2">
            <i class="fas fa-tag mr-1"></i> {tag}
        </span>'''
    
    # Generate achievements HTML
    achievements_html = ''
    for achievement in project_data.get('achievements', []):
        achievements_html += f'<li>{achievement}</li>'
    
    # Auto-detect PDF files if not specified in markdown
    report_url = project_data.get('report', '#')
    slides_url = project_data.get('slides', '#')
    
    # Try to find project-specific PDFs
    project_num = '1' if 'practicum i' in title.lower() else '2'
    base_url = f"https://raw.githubusercontent.com/iamgmujtaba/regis_std/main/data/{course_code}/{username}"
    
    # Look for common report naming patterns
    if report_url == '#':
        report_patterns = [
            f'practicum{project_num}_report.pdf',
            f'project{project_num}_report.pdf',
            f'practicum_{project_num}_report.pdf',
            'report.pdf'
        ]
        for pattern in report_patterns:
            for pdf in student_files['pdfs']:
                if pattern in pdf['name'].lower():
                    report_url = pdf['url']
                    break
            if report_url != '#':
                break
    
    # Look for common slides naming patterns
    if slides_url == '#':
        slides_patterns = [
            f'practicum{project_num}_slides.pdf',
            f'practicum{project_num}_presentation.pdf',
            f'project{project_num}_slides.pdf',
            'slides.pdf',
            'presentation.pdf'
        ]
        for pattern in slides_patterns:
            for pdf in student_files['pdfs']:
                if pattern in pdf['name'].lower():
                    slides_url = pdf['url']
                    break
            if slides_url != '#':
                break
    
    # Generate button classes based on availability
    github_class = "bg-gray-900 text-white hover:bg-gray-800" if project_data.get('github', '#') != '#' else "bg-gray-300 text-gray-600 cursor-not-allowed"
    report_class = "bg-primary text-white hover:bg-blue-800" if report_url != '#' else "bg-gray-300 text-gray-600 cursor-not-allowed"
    slides_class = "bg-secondary text-white hover:bg-purple-800" if slides_url != '#' else "bg-gray-300 text-gray-600 cursor-not-allowed"
    demo_class = "bg-accent text-white hover:bg-cyan-700" if project_data.get('demo', '#') != '#' else "bg-gray-300 text-gray-600 cursor-not-allowed"
    
    return f'''
    <div class="bg-white rounded-lg shadow-lg overflow-hidden mb-8 border border-gray-200 hover:shadow-xl transition duration-300">
        <div class="bg-gradient-to-r from-{gradient_color} to-blue-600 px-6 py-4">
            <h3 class="text-2xl font-bold text-white flex items-center">
                <i class="fas fa-project-diagram mr-3"></i>
                {title} Project
            </h3>
        </div>
        <div class="p-6">
            <h4 class="text-xl font-bold text-gray-900 mb-3">
                {project_data.get('title', f'{title} Project')}
            </h4>
            
            <div class="mb-4">
                {tags_html}
            </div>

            <p class="text-gray-700 mb-4 leading-relaxed">
                <strong>Abstract:</strong> {project_data.get('abstract', 'Please add project abstract in your profile.md file.')}
            </p>

            {"<div class='border-t border-gray-200 pt-4 mt-4'><h5 class='font-semibold text-gray-900 mb-3'>Key Achievements:</h5><ul class='list-disc list-inside space-y-2 text-gray-700 mb-4'>" + achievements_html + "</ul></div>" if achievements_html else ""}

            <div class="flex flex-wrap gap-3 mt-6">
                <a href="{project_data.get('github', '#')}" 
                   {"target='_blank'" if project_data.get('github', '#') != '#' else ""}
                   class="inline-flex items-center px-4 py-2 {github_class} rounded-lg transition duration-300">
                    <i class="fab fa-github mr-2"></i> View Code
                </a>
                <a href="{report_url}" 
                   {"target='_blank'" if report_url != '#' else ""}
                   class="inline-flex items-center px-4 py-2 {report_class} rounded-lg transition duration-300">
                    <i class="fas fa-file-pdf mr-2"></i> Read Report
                </a>
                <a href="{slides_url}" 
                   {"target='_blank'" if slides_url != '#' else ""}
                   class="inline-flex items-center px-4 py-2 {slides_class} rounded-lg transition duration-300">
                    <i class="fas fa-presentation mr-2"></i> View Slides
                </a>
                {"<a href='" + project_data.get('demo', '#') + "' target='_blank' class='inline-flex items-center px-4 py-2 " + demo_class + " rounded-lg transition duration-300'><i class='fas fa-external-link-alt mr-2'></i> Live Demo</a>" if project_data.get('demo', '#') != '#' else ""}
            </div>
        </div>
    </div>'''

def create_html_page(student_data, course_code, target_dir, markdown_content, metadata, student_files):
    """Create HTML page matching template.html exactly with proper file URLs"""
    username = student_data['username']
    first_name = metadata.get('firstName', 'Student')
    last_name = metadata.get('lastName', 'Name')
    email = metadata.get('email', 'student@regis.edu')
    
    # Parse markdown sections
    sections = parse_markdown_sections(markdown_content)
    
    # Create profiles directory
    profiles_dir = target_dir / 'profiles'
    profiles_dir.mkdir(exist_ok=True)
    
    # Generate skills HTML
    skills_html = generate_skills_html(sections['skills'])
    
    # Generate project HTML with file links
    practicum1_html = generate_project_html(sections['practicum1'], 'Practicum I', 'primary', student_files, course_code, username)
    practicum2_html = generate_project_html(sections['practicum2'], 'Practicum II', 'secondary', student_files, course_code, username)
    
    # Generate contact HTML
    contact_html = generate_contact_html(sections['contact'], email)
    
    # Use the found avatar URL or fallback
    avatar_url = student_files['avatar_url'] or f"https://via.placeholder.com/200x200/1e40af/ffffff?text={first_name[0]}{last_name[0]}"
    
    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="{first_name} {last_name} - Student Portfolio">
    <title>{first_name} {last_name} - Portfolio</title>
    
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
                        primary: '#1e40af',
                        secondary: '#7c3aed',
                        accent: '#06b6d4',
                    }}
                }}
            }}
        }}
    </script>
</head>
<body class="bg-gray-50">
    <!-- Navigation Bar -->
    <nav class="bg-white shadow-lg sticky top-0 z-50">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between items-center h-16">
                <div class="flex items-center">
                    <i class="fas fa-user-graduate text-primary text-2xl mr-3"></i>
                    <span class="font-bold text-xl text-gray-800">My Portfolio</span>
                </div>
                <div class="hidden md:flex space-x-6">
                    <a href="../index.html" class="text-gray-700 hover:text-primary transition duration-300">
                        <i class="fas fa-home mr-1"></i> Home
                    </a>
                    <a href="#about" class="text-gray-700 hover:text-primary transition duration-300">About</a>
                    <a href="#projects" class="text-gray-700 hover:text-primary transition duration-300">Projects</a>
                    <a href="#contact" class="text-gray-700 hover:text-primary transition duration-300">Contact</a>
                </div>
                <div class="md:hidden">
                    <button id="mobile-menu-button" class="text-gray-700 hover:text-primary">
                        <i class="fas fa-bars text-2xl"></i>
                    </button>
                </div>
            </div>
        </div>
        <!-- Mobile Menu -->
        <div id="mobile-menu" class="hidden md:hidden bg-white border-t">
            <div class="px-2 pt-2 pb-3 space-y-1">
                <a href="../index.html" class="block px-3 py-2 text-gray-700 hover:bg-gray-100 rounded">
                    <i class="fas fa-home mr-1"></i> Home
                </a>
                <a href="#about" class="block px-3 py-2 text-gray-700 hover:bg-gray-100 rounded">About</a>
                <a href="#projects" class="block px-3 py-2 text-gray-700 hover:bg-gray-100 rounded">Projects</a>
                <a href="#contact" class="block px-3 py-2 text-gray-700 hover:bg-gray-100 rounded">Contact</a>
            </div>
        </div>
    </nav>

    <!-- Hero/Profile Section -->
    <section class="bg-gradient-to-r from-primary to-secondary py-16">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex flex-col md:flex-row items-center justify-center gap-8">
                <!-- Profile Photo -->
                <div class="flex-shrink-0">
                    <div class="w-48 h-48 rounded-full overflow-hidden border-4 border-white shadow-2xl bg-white">
                        <img src="{avatar_url}" 
                             alt="{first_name} {last_name}" 
                             class="w-full h-full object-cover"
                             onerror="this.src='https://via.placeholder.com/200x200/1e40af/ffffff?text={first_name[0]}{last_name[0]}'">
                    </div>
                </div>
                
                <!-- Profile Info -->
                <div class="text-center md:text-left text-white">
                    <h1 class="text-4xl md:text-5xl font-bold mb-2">{first_name} {last_name}</h1>
                    <p class="text-xl text-blue-100 mb-4">Data Science Student | Practicum Student</p>
                    
                    <!-- Social Links -->
                    <div class="flex justify-center md:justify-start space-x-4 mb-4">
                        <a href="{sections['contact'].get('github', '#')}" 
                           target="_blank"
                           class="w-10 h-10 bg-white text-primary rounded-full flex items-center justify-center hover:bg-blue-50 transition duration-300">
                            <i class="fab fa-github text-xl"></i>
                        </a>
                        <a href="{sections['contact'].get('linkedin', '#')}" 
                           target="_blank"
                           class="w-10 h-10 bg-white text-primary rounded-full flex items-center justify-center hover:bg-blue-50 transition duration-300">
                            <i class="fab fa-linkedin text-xl"></i>
                        </a>
                        <a href="mailto:{email}" 
                           class="w-10 h-10 bg-white text-primary rounded-full flex items-center justify-center hover:bg-blue-50 transition duration-300">
                            <i class="fas fa-envelope text-xl"></i>
                        </a>
                        <a href="#" 
                           target="_blank"
                           class="w-10 h-10 bg-white text-primary rounded-full flex items-center justify-center hover:bg-blue-50 transition duration-300">
                            <i class="fas fa-file-pdf text-xl"></i>
                        </a>
                    </div>
                    
                    <!-- Quick Links -->
                    <div class="flex flex-wrap justify-center md:justify-start gap-3">
                        <a href="#" 
                           target="_blank"
                           class="bg-white text-primary px-4 py-2 rounded-lg font-semibold hover:bg-blue-50 transition duration-300 inline-flex items-center">
                            <i class="fas fa-download mr-2"></i> Download CV
                        </a>
                        <a href="#contact" 
                           class="bg-transparent border-2 border-white text-white px-4 py-2 rounded-lg font-semibold hover:bg-white hover:text-primary transition duration-300 inline-flex items-center">
                            <i class="fas fa-paper-plane mr-2"></i> Contact Me
                        </a>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- About Section -->
    <section id="about" class="py-16 bg-white">
        <div class="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
            <h2 class="text-3xl font-bold text-gray-900 mb-4 text-center">About Me</h2>
            <div class="w-20 h-1 bg-primary mx-auto mb-8"></div>
            
            <div class="prose prose-lg max-w-none text-gray-700">
                {format_about_text(sections['about'])}
            </div>

            <!-- Skills Section -->
            <div class="mt-12">
                <h3 class="text-2xl font-bold text-gray-900 mb-6 text-center">Technical Skills</h3>
                {skills_html}
            </div>
        </div>
    </section>

    <!-- Projects Section -->
    <section id="projects" class="py-16 bg-gray-50">
        <div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
            <h2 class="text-3xl font-bold text-gray-900 mb-4 text-center">Practicum Projects</h2>
            <div class="w-20 h-1 bg-primary mx-auto mb-12"></div>

            {practicum1_html}
            {practicum2_html}
        </div>
    </section>

    <!-- Contact Section -->
    <section id="contact" class="py-16 bg-white">
        <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
            <h2 class="text-3xl font-bold text-gray-900 mb-4 text-center">Get In Touch</h2>
            <div class="w-20 h-1 bg-primary mx-auto mb-12"></div>
            {contact_html}
        </div>
    </section>

    <!-- Footer -->
    <footer class="bg-gray-900 text-white py-8">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
            <p class="mb-2">&copy; 2025 {first_name} {last_name}. All rights reserved.</p>
            <p class="text-gray-400 text-sm">Practicum Portfolio | Powered by GitHub Pages</p>
            <div class="mt-4">
                <a href="../index.html" class="text-gray-400 hover:text-white transition mx-2">
                    <i class="fas fa-home mr-1"></i> Back to Main Page
                </a>
            </div>
        </div>
    </footer>

    <!-- Mobile Menu Script -->
    <script>
        document.getElementById('mobile-menu-button').addEventListener('click', function() {{
            const menu = document.getElementById('mobile-menu');
            menu.classList.toggle('hidden');
        }});

        // Smooth scrolling for anchor links
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {{
            anchor.addEventListener('click', function (e) {{
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {{
                    target.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
                    // Close mobile menu if open
                    document.getElementById('mobile-menu').classList.add('hidden');
                }}
            }});
        }});
    </script>
</body>
</html>'''
    
    # Write the HTML file
    html_file = profiles_dir / f'{username}.html'
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"    🌐 Created HTML page: profiles/{username}.html")
    print(f"    📸 Avatar URL: {avatar_url}")
    print(f"    📄 Found {len(student_files['pdfs'])} PDFs, {len(student_files['images'])} images")
    
    return f'profiles/{username}.html'

def format_about_text(about_text):
    """Format about text as HTML paragraphs"""
    if not about_text:
        return '''<p class="text-lg leading-relaxed mb-4">
            I am a dedicated Data Science student at Regis University, currently completing my practicum 
            experience. Please edit your profile.md file to add information about yourself.
        </p>'''
    
    paragraphs = about_text.split('\n\n')
    html = ''
    for paragraph in paragraphs:
        if paragraph.strip():
            html += f'<p class="text-lg leading-relaxed mb-4">{paragraph.strip()}</p>\n'
    
    return html

def generate_skills_html(skills_dict):
    """Generate skills HTML from parsed skills"""
    if not skills_dict:
        return '''<div class="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div class="bg-gradient-to-br from-blue-50 to-blue-100 p-4 rounded-lg text-center border border-blue-200">
                <i class="fas fa-code text-primary text-3xl mb-2"></i>
                <p class="font-semibold">Programming</p>
                <p class="text-sm text-gray-600">Python, R, SQL</p>
            </div>
            <div class="bg-gradient-to-br from-green-50 to-green-100 p-4 rounded-lg text-center border border-green-200">
                <i class="fas fa-laptop-code text-green-600 text-3xl mb-2"></i>
                <p class="font-semibold">Data Analysis</p>
                <p class="text-sm text-gray-600">Pandas, NumPy</p>
            </div>
            <div class="bg-gradient-to-br from-purple-50 to-purple-100 p-4 rounded-lg text-center border border-purple-200">
                <i class="fas fa-chart-bar text-purple-600 text-3xl mb-2"></i>
                <p class="font-semibold">Visualization</p>
                <p class="text-sm text-gray-600">Matplotlib, Seaborn</p>
            </div>
            <div class="bg-gradient-to-br from-orange-50 to-orange-100 p-4 rounded-lg text-center border border-orange-200">
                <i class="fas fa-brain text-orange-600 text-3xl mb-2"></i>
                <p class="font-semibold">Machine Learning</p>
                <p class="text-sm text-gray-600">Scikit-learn</p>
            </div>
        </div>'''
    
    # Map skill categories to icons and colors
    skill_icons = {
        'Programming Languages': ('fas fa-code', 'blue'),
        'Tools & Frameworks': ('fas fa-tools', 'green'),
        'Databases': ('fas fa-database', 'purple'),
        'Machine Learning': ('fas fa-brain', 'orange'),
        'Web Development': ('fas fa-laptop-code', 'indigo'),
        'Data Science': ('fas fa-chart-bar', 'red')
    }
    
    html = '<div class="grid grid-cols-2 md:grid-cols-4 gap-4">'
    
    for category, skills_list in skills_dict.items():
        icon, color = skill_icons.get(category, ('fas fa-star', 'gray'))
        skills_text = ', '.join(skills_list[:3])  # Show first 3 skills
        
        html += f'''
        <div class="bg-gradient-to-br from-{color}-50 to-{color}-100 p-4 rounded-lg text-center border border-{color}-200">
            <i class="{icon} text-{color}-600 text-3xl mb-2"></i>
            <p class="font-semibold">{category}</p>
            <p class="text-sm text-gray-600">{skills_text}</p>
        </div>'''
    
    html += '</div>'
    return html

def generate_contact_html(contact_data, email):
    """Generate contact HTML from parsed contact data"""
    return f'''
    <div class="grid md:grid-cols-2 gap-8">
        <!-- Contact Info -->
        <div>
            <h3 class="text-xl font-semibold mb-4">Contact Information</h3>
            <div class="space-y-4">
                <div class="flex items-start">
                    <div class="flex-shrink-0">
                        <div class="w-10 h-10 bg-primary rounded-lg flex items-center justify-center">
                            <i class="fas fa-envelope text-white"></i>
                        </div>
                    </div>
                    <div class="ml-4">
                        <p class="font-semibold">Email</p>
                        <a href="mailto:{email}" class="text-primary hover:underline">
                            {email}
                        </a>
                    </div>
                </div>

                <div class="flex items-start">
                    <div class="flex-shrink-0">
                        <div class="w-10 h-10 bg-secondary rounded-lg flex items-center justify-center">
                            <i class="fab fa-linkedin text-white"></i>
                        </div>
                    </div>
                    <div class="ml-4">
                        <p class="font-semibold">LinkedIn</p>
                        <a href="{contact_data.get('linkedin', '#')}" 
                           target="_blank"
                           class="text-primary hover:underline">
                            {"LinkedIn Profile" if contact_data.get('linkedin', '#') != '#' else "Add LinkedIn in profile.md"}
                        </a>
                    </div>
                </div>

                <div class="flex items-start">
                    <div class="flex-shrink-0">
                        <div class="w-10 h-10 bg-gray-900 rounded-lg flex items-center justify-center">
                            <i class="fab fa-github text-white"></i>
                        </div>
                    </div>
                    <div class="ml-4">
                        <p class="font-semibold">GitHub</p>
                        <a href="{contact_data.get('github', '#')}" 
                           target="_blank"
                           class="text-primary hover:underline">
                            {"GitHub Profile" if contact_data.get('github', '#') != '#' else "Add GitHub in profile.md"}
                        </a>
                    </div>
                </div>

                <div class="flex items-start">
                    <div class="flex-shrink-0">
                        <div class="w-10 h-10 bg-accent rounded-lg flex items-center justify-center">
                            <i class="fas fa-globe text-white"></i>
                        </div>
                    </div>
                    <div class="ml-4">
                        <p class="font-semibold">Portfolio</p>
                        <a href="{contact_data.get('portfolio', '#')}" 
                           target="_blank"
                           class="text-primary hover:underline">
                            {"Personal Website" if contact_data.get('portfolio', '#') != '#' else "Add portfolio in profile.md"}
                        </a>
                    </div>
                </div>
            </div>
        </div>

        <!-- Quick Message Card -->
        <div class="bg-gradient-to-br from-blue-50 to-purple-50 p-6 rounded-lg border border-blue-200">
            <h3 class="text-xl font-semibold mb-4">Send a Message</h3>
            <p class="text-gray-700 mb-4">
                Feel free to reach out for collaboration opportunities, questions about my projects, 
                or just to connect!
            </p>
            <a href="mailto:{email}?subject=Hello%20from%20your%20portfolio" 
               class="block w-full bg-primary text-white text-center py-3 rounded-lg font-semibold hover:bg-blue-800 transition duration-300">
                <i class="fas fa-paper-plane mr-2"></i> Send Email
            </a>
            
            <div class="mt-6 pt-6 border-t border-blue-200">
                <p class="text-sm text-gray-600 text-center mb-3">Connect on social media:</p>
                <div class="flex justify-center space-x-4">
                    <a href="{contact_data.get('github', '#')}" 
                       target="_blank"
                       class="w-10 h-10 bg-gray-900 text-white rounded-full flex items-center justify-center hover:bg-gray-800 transition">
                        <i class="fab fa-github"></i>
                    </a>
                    <a href="{contact_data.get('linkedin', '#')}" 
                       target="_blank"
                       class="w-10 h-10 bg-blue-700 text-white rounded-full flex items-center justify-center hover:bg-blue-800 transition">
                        <i class="fab fa-linkedin"></i>
                    </a>
                    <a href="mailto:{email}" 
                       class="w-10 h-10 bg-red-600 text-white rounded-full flex items-center justify-center hover:bg-red-700 transition">
                        <i class="fas fa-envelope"></i>
                    </a>
                </div>
            </div>
        </div>
    </div>'''

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
                
                # Find all student files (images, PDFs)
                student_files = find_student_files(student_dir, course_code, username)
                
                # Create student data entry
                student_data = {
                    'username': username,
                    'name': f"{metadata.get('firstName', '')} {metadata.get('lastName', '')}".strip() or username,
                    'email': metadata.get('email', ''),
                    'course': course_code,
                    'semester': metadata.get('semester', 'Spring 2025'),
                    'profilePath': f'regis_std/data/{course_code}/{username}/profile.md',
                    'avatarPath': student_files['avatar_url'],  # Direct URL
                    'projects': [],
                    'files': student_files['pdfs'] + student_files['images']
                }
                
                # Create HTML page for this student with all file links
                html_path = create_html_page(student_data, course_code, target_dir, content, metadata, student_files)
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