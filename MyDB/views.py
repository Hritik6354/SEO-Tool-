from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.template import loader
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth import login,logout,authenticate
from .models  import signup,add,crawl,Profile,CrawlResult
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.sessions.models import Session
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from .helpers import send_forget_password_mail
from django.contrib.auth import get_user_model
#from weasyprint import HTML
from django.template.loader import get_template
from django.http import FileResponse
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from io import BytesIO
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.template.loader import render_to_string

import matplotlib
matplotlib.use('Agg')  # Use Agg backend for non-GUI environments (e.g., servers)
import matplotlib.pyplot as plt
import io
import base64

# Create your views here.

def all_user(request):
    return HttpResponse('Welcome')

def members(request):
    template = loader.get_template('home.html')
    return HttpResponse(template.render())

def navbar(request):
    return render(request, 'navbar.html')


def home(request):
    return render(request, 'login.html')

def seohome(request):
    return render(request, 'seohome.html')

def sign(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        umobile = request.POST.get('umobile')
        uemail = request.POST.get('uemail')
        password = request.POST.get('password')
        #user = signup.objects.filter(username=username)
        if signup.objects.filter(username=username).exists():
            messages.info(request, "Username already taken!")
            return redirect('/register/')
        user = signup.objects.create(
            username=username,
            umobile=umobile,
            uemail=uemail,
            password=password)          
        user.save()
        messages.info(request, "Account created Successfully!")
        return redirect('/login')
    return render(request, 'register.html')


def logout(request):
    logout(request)
    return redirect('/login')

@csrf_protect
def logn(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        # Authenticate the user
        try:
            user = signup.objects.get(username=username, password=password)
        except signup.DoesNotExist:
            messages.error(request, "Invalid Username or Password")
            return redirect('/login')

        # Store user details in session
        request.session['user_id'] = user.id  # Store user ID in session
        request.session['username'] = user.username  # Store username

        messages.success(request, f"Welcome {user.username}!")
        return redirect('index')
    return render(request, 'login.html')

@login_required    
def index(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('/login')

    username = request.session.get('username', 'Guest')
    return render(request, 'home.html', {'username': username})


def addproject(request):
    projects = add.objects.all().values()
    template = loader.get_template('addproject.html')
    return HttpResponse(template.render({'projects':projects}, request))


@login_required
def addrecord(request):
    if request.method == "POST":
        url = request.POST.get('url')
        title = request.POST.get('title')

        # ✅ Get the user from the session
        username = request.session.get('username')  # Fetch username from session
        try:
            user = signup.objects.get(username=username)  # Fetch user object
        except signup.DoesNotExist:
            messages.error(request, "User not found. Please log in again.")
            return redirect('/login')

        # ✅ Create the project with the correct user
        projects = add.objects.create(
            user=user,  # Assign the correct user instance
            url=url,
            title=title
        )
        projects.save()

        return redirect('/index/dashboard/')
    else:
        return redirect('/index/addproject/')

def edit_project(request, project_id):
    project = get_object_or_404(add, id=project_id)

    if request.method == "POST":
        project.url = request.POST.get('url')
        project.title = request.POST.get('title')
        project.save()
        messages.success(request, "Project updated successfully!")
        return redirect('/dashboard/')

    return render(request, 'editproject.html', {'project': project})

def delete_project(request, project_id):
    project = get_object_or_404(add, id=project_id)

    project.delete()
    messages.success(request, "Project deleted successfully!")
    
    return redirect('/dashboard/')

@login_required
def projdetail(request, project_id):
    user_id = request.session.get('user_id')
    user_projects = add.objects.filter(user_id=user_id).prefetch_related('crawl_results')
    
    # Prepare data for the first project (or average if multiple)
    if user_projects.exists():
        latest_crawls = [p.crawl_results.order_by('-crawl_time').first() for p in user_projects]
        latest_crawl = latest_crawls[0] if latest_crawls[0] else None
    else:
        latest_crawl = None

    # Calculate SEO metrics (example logic based on crawled data)
    if latest_crawl:
        # Example scoring (customize based on your needs)
        meta_info_score = min(100, max(0, 80 + (10 if latest_crawl.meta_description else -20)))  # Adjust for meta presence
        page_quality_score = min(100, max(0, 50 + (latest_crawl.word_count // 100)))  # Based on word count
        page_structure_score = min(100, max(0, 90 + (5 if latest_crawl.h1_tags else -10)))  # Based on H1 tags
        link_structure_score = min(100, max(0, 90 + (latest_crawl.internal_links // 10)))  # Based on internal links
        #server_score = min(100, max(0, 90 + (latest_crawl.status_code == 200) * 10))  # Based on status code
        external_factors_score = min(100, max(0, 100 - (latest_crawl.broken_links * 5)))  # Penalize broken links

        # Overall SEO score (average of categories)
        seo_score = (meta_info_score + page_quality_score + page_structure_score + 
                     link_structure_score + external_factors_score) // 6

        # Bar chart data
        categories = ['Meta Information', 'Page Quality', 'Page Structure', 'Link Structure', 'External Factors']
        scores = [meta_info_score, page_quality_score, page_structure_score, 
                  link_structure_score, external_factors_score]

        # Generate bar chart
        plt.figure(figsize=(10, 4))
        plt.bar(categories, scores, color='#1E90FF')
        plt.title('Overview of the SEO Check')
        plt.xlabel('Categories')
        plt.ylabel('Score (%)')
        plt.xticks(rotation=45)
        plt.ylim(0, 100)
        for i, v in enumerate(scores):
            plt.text(i, v + 1, str(v) + '%', ha='center', va='bottom')

        buf_bar = io.BytesIO()
        plt.savefig(buf_bar, format='png', bbox_inches='tight')
        plt.close()
        bar_graph_data = base64.b64encode(buf_bar.getvalue()).decode('utf-8')
        buf_bar.close()

        # Generate pie chart
        plt.figure(figsize=(4, 4))
        plt.pie([seo_score, 100 - seo_score], labels=['SEO Score', ''], colors=['#FFA500', 'lightgrey'], startangle=90, autopct='%1.0f%%')
        plt.title('SEO Score')

        buf_pie = io.BytesIO()
        plt.savefig(buf_pie, format='png', bbox_inches='tight')
        plt.close()
        pie_graph_data = base64.b64encode(buf_pie.getvalue()).decode('utf-8')
        buf_pie.close()

        project = get_object_or_404(add, id=project_id)
        latest_crawl = project.crawl_results.order_by('-crawl_time').first()
        context = {
            'project': project,
            'latest_crawl': latest_crawl,
            'user_projects': user_projects,
            'bar_graph_data': bar_graph_data,
            'pie_graph_data': pie_graph_data,
            'seo_score': seo_score,
        }
    else:
        context = {
            'project': project,
            'latest_crawl': latest_crawl,
            'user_projects': user_projects,
            'bar_graph_data': None,
            'pie_graph_data': None,
            'seo_score': 0,
        }
    
    #crawling = get_object_or_404(project=project).first()
    #user_id = request.session.get('user_id')
    
    return render(request, 'projdetail.html', context)

    
    
@login_required
def graph(request):
    user_projects = add.objects.filter(user=request.user).prefetch_related('crawl_results')
    
    # Prepare data for graph
    project_titles = []
    internal_links_data = []
    external_links_data = []
    page_speed_data = []

    for project in user_projects:
        latest_crawl = project.crawl_results.order_by('-crawl_time').first()
        if latest_crawl:
            project_titles.append(project.title[:15])  # Truncate for readability
            internal_links_data.append(latest_crawl.internal_links)
            external_links_data.append(latest_crawl.external_links)
            page_speed_data.append(latest_crawl.page_speed)

    # Create graph
    plt.figure(figsize=(10, 6))
    plt.plot(project_titles, internal_links_data, label='Internal Links', marker='o')
    plt.plot(project_titles, external_links_data, label='External Links', marker='o')
    plt.plot(project_titles, page_speed_data, label='Page Speed', marker='o')
    plt.title('Crawled Data Overview')
    plt.xlabel('Projects')
    plt.ylabel('Values')
    plt.legend()
    plt.xticks(rotation=45)
    plt.grid(True)

    # Save plot to a buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    graph_data = base64.b64encode(buf.getvalue()).decode('utf-8')
    buf.close()

    context = {
        'user_projects': user_projects,
        'graph_data': graph_data,
    }
    return render(request, 'dashboard.html', context)



@login_required
def dashboard(request):
    user_id = request.session.get('user_id')
    user_projects = add.objects.filter(user_id=user_id).prefetch_related('crawl_results')
    
    # Prepare data for the first project (or average if multiple)
    if user_projects.exists():
        latest_crawls = [p.crawl_results.order_by('-crawl_time').first() for p in user_projects]
        latest_crawl = latest_crawls[0] if latest_crawls[0] else None
    else:
        latest_crawl = None

    # Calculate SEO metrics (example logic based on crawled data)
    if latest_crawl:
        # Example scoring (customize based on your needs)
        meta_info_score = min(100, max(0, 80 + (10 if latest_crawl.meta_description else -20)))  # Adjust for meta presence
        page_quality_score = min(100, max(0, 50 + (latest_crawl.word_count // 100)))  # Based on word count
        page_structure_score = min(100, max(0, 90 + (5 if latest_crawl.h1_tags else -10)))  # Based on H1 tags
        link_structure_score = min(100, max(0, 90 + (latest_crawl.internal_links // 10)))  # Based on internal links
        #server_score = min(100, max(0, 90 + (latest_crawl.status_code == 200) * 10))  # Based on status code
        external_factors_score = min(100, max(0, 100 - (latest_crawl.broken_links * 5)))  # Penalize broken links

        # Overall SEO score (average of categories)
        seo_score = (meta_info_score + page_quality_score + page_structure_score + 
                     link_structure_score + external_factors_score) // 6

        # Bar chart data
        categories = ['Meta Information', 'Page Quality', 'Page Structure', 'Link Structure', 'External Factors']
        scores = [meta_info_score, page_quality_score, page_structure_score, 
                  link_structure_score, external_factors_score]

        # Generate bar chart
        plt.figure(figsize=(10, 4))
        plt.bar(categories, scores, color='#1E90FF')
        plt.title('Overview of the SEO Check')
        plt.xlabel('Categories')
        plt.ylabel('Score (%)')
        plt.xticks(rotation=45)
        plt.ylim(0, 100)
        for i, v in enumerate(scores):
            plt.text(i, v + 1, str(v) + '%', ha='center', va='bottom')

        buf_bar = io.BytesIO()
        plt.savefig(buf_bar, format='png', bbox_inches='tight')
        plt.close()
        bar_graph_data = base64.b64encode(buf_bar.getvalue()).decode('utf-8')
        buf_bar.close()

        # Generate pie chart
        plt.figure(figsize=(4, 4))
        plt.pie([seo_score, 100 - seo_score], labels=['SEO Score', ''], colors=['#FFA500', 'lightgrey'], startangle=90, autopct='%1.0f%%')
        plt.title('SEO Score')

        buf_pie = io.BytesIO()
        plt.savefig(buf_pie, format='png', bbox_inches='tight')
        plt.close()
        pie_graph_data = base64.b64encode(buf_pie.getvalue()).decode('utf-8')
        buf_pie.close()


        projects = add.objects.filter(user_id=user_id) 

        context = {
            'projects': projects,
            'user_projects': user_projects,
            'bar_graph_data': bar_graph_data,
            'pie_graph_data': pie_graph_data,
            'seo_score': seo_score,
        }
    else:
        context = {
            'projects': projects,
            'user_projects': user_projects,
            'bar_graph_data': None,
            'pie_graph_data': None,
            'seo_score': 0,
        }
    if not user_id:
        return redirect('/login')

   # user = get_object_or_404(signup, user_id=user_id)
    # Show projects belonging to the logged-in user
    
    return render(request, 'dashboard.html', context)

def analyze_keywords(text):
    """Calculate keyword frequency."""
    words = text.lower().split()
    keyword_counts = {word: words.count(word) for word in set(words)}
    return dict(sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:10])  # Top 10 words

@login_required
def handlecrawling(request):
    if request.method == "POST":
        url = request.POST.get("url")
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            # Extract SEO Data
            title = soup.title.string if soup.title else "No Title"
            meta_desc = soup.find("meta", attrs={"name": "description"})
            description = meta_desc["content"] if meta_desc else "No Meta Description"

            # Extract Headings (H1)
            h1_tags = [h1.get_text() for h1 in soup.find_all("h1")]

            # Extract Links
            internal_links = set()
            external_links = set()
            broken_links = []

            for link in soup.find_all("a", href=True):
                href = link["href"]
                absolute_url = urljoin(url, href)
                parsed_url = urlparse(absolute_url)

                if parsed_url.netloc == urlparse(url).netloc:
                    internal_links.add(absolute_url)
                else:
                    external_links.add(absolute_url)

                # Check broken links
                try:
                    link_response = requests.head(absolute_url, timeout=3)
                    if link_response.status_code >= 400:
                        broken_links.append(absolute_url)
                except requests.RequestException:
                    broken_links.append(absolute_url)

            # Analyze Keyword Density
            keyword_density = analyze_keywords(soup.get_text())

            # Fetch Page Speed
           # page_speed = fetch_page_speed(url)

            # Save to Database
            crawled_data, created = crawl.objects.get_or_create(
                url=url,
                defaults={
                    "title": title,
                    "meta_description": description,
                    "h1_tags": h1_tags,
                    "internal_links": list(internal_links),
                    "external_links": list(external_links),
                    "keyword_density": keyword_density,
                    #"page_speed": page_speed,
                    "broken_links": broken_links,
                }
            )

            return render(request, "result.html", {"data": crawled_data})

        except requests.exceptions.RequestException as e:
            return render(request, "crawling.html", {"error": str(e)})

    return render(request, "crawling.html")

@login_required
def analytics(request):
    id = request.session.get('user_id')
    data = crawl.objects.filter(id=id)
    context = {
        "data": data
    }
    return render(request, "analytics.html", context )

@login_required
def start_crawl(request, project_id):
    project = get_object_or_404(add, id=project_id)
    url = project.url
    
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        #Extract details
        title = soup.title.string if soup.title else ''
        meta_desc_tag = soup.find("meta", attrs={"name": "description"})
        meta_description = meta_desc_tag["content"] if meta_desc_tag and "content" in meta_desc_tag.attrs else ''
        
        h1_tags = [h1.get_text(strip=True)for h1 in soup.find_all('h1')]
        h1_text = "\n".join(h1_tags) if h1_tags else ''
        
        domain = urlparse(url).netloc
        internal = 0
        external = 0
        broken = 0
        
        for link in soup.find_all("a", href=True):
            href = link['href']
            if href.startswith('#') or href.startswith('mailto:'):
                continue
            if domain in href or href.startswith('/'):
                internal += 1
            else:
                external += 1
            try:
                check = requests.head(href if href.startswith('http') else f"{url.rstrip('/')}/{href.lstrip('/')}", timeout=3)
                if check.status_code >= 400:
                    broken += 1
            except requests.RequestException:
                broken += 1
            
            # Additional metrics
            file_size = len(response.content) // 1024  # Convert to KB
            word_count = len(soup.get_text().split())
            media_files = len(soup.find_all(['img', 'video', 'audio']))  # Count media elements
            page_speed = 0.5  # Placeholder value (0-1 scale); integrate with PageSpeed Insights API for real data
            
            # SEO suggestions
            suggested_keywords = ', '.join(['web', 'crawl', 'seo', title.split()[0] if title else 'site'])  # Simple keyword suggestion
            seo_suggestions = []
            if len(title) > 60:
                seo_suggestions.append("Title is too long. Consider shortening it to under 60 characters.")
            if not meta_description:
                seo_suggestions.append("No meta description found. Add one for better SEO.")
            seo_suggestions = '\n'.join(seo_suggestions) if seo_suggestions else "No suggestions."    
                
                #Save to DB
            CrawlResult.objects.create(
                project=project,
                page_title=title,
                meta_description=meta_description,
                h1_tags=h1_text,
                internal_links=internal,
                external_links=external,
                broken_links=broken,
                file_size=file_size,
                word_count=word_count,
                media_files=media_files,
                page_speed=page_speed,
                suggested_keywords=suggested_keywords,
                seo_suggestions=seo_suggestions,
            )
            return redirect('projdetail', project_id=project.id)
         
    except Exception as e:
        return render(request, 'project/dashboard.html', {
            'project': project,
            'error': str(e),
        })

@login_required
def analysis_results(request):
    user_id = request.session.get('user_id')
    projects = add.objects.filter(user_id=user_id).prefetch_related('crawl_results')
    project_data = []
    for project in projects:
        latest_crawl = project.crawl_results.order_by('-crawl_time').first()
        project_data.append({
            'id': project.id,
            'title': project.title,
            'url': project.url,
            'last_scan': latest_crawl.crawl_time if latest_crawl else None,
            'status': latest_crawl.status_code if latest_crawl and hasattr(latest_crawl, 'status_code') else None,
        })
    return render(request, 'analysis_result.html', {'projects': project_data})



def aboutus(request):
    #user = User.objects.filter(username=request.session.get('username')).first()
    #emp = sign.objects.filter(user=user).first()
    return render(request, 'about.html')


def contect_us(request):
    #user = User.objects.filter(username=request.session.get('username')).first()
    #emp = Employee.objects.filter(user=user).first()
    return render(request, 'contact.html')


def services(request):
    return render(request, 'service.html')



def planpricing(request):
    return render(request, 'pricing.html')


@login_required
def my_account(request):
    """
    View for displaying the user's account details.
    """
    
    username = request.session.get('username', 'Guest')
    #username = request.user.username  # Extract the actual username as a string
    return render(request, 'myaccount.html', {'username': username})

#def changepassword(request):
 #   return render(request, 'changepassword.html')

#def cpassword(request, token):
 #   context = {}
    
  #  try:
   #     profile_obj = Profile.objects.filter(forget_password_token = token).first()
    #    context = {'id' : profile_obj.user.id}
     #   
      #  if request.method == 'POST':
       #     new_password = request.POST.get('new_password')
        #    confirm_password = request.POST.get('reconfirm_password')
         #   id = request.POST.get('id')
          #  
           # if id is None:
            
            #    messages.success(request, 'No id found')
             #   return redirect(f'/cpassword/{token}/')
            #
            #if new_password != confirm_password:
             #   messages.success(request, 'both should be equal.')
              #  return redirect(f'/cpassword/{token}/')
            
            #User = get_user_model()  # This will automatically fetch the correct user model
            #user_obj = User.objects.get(id=id)
            #user_obj.set_password(new_password)
            #user_obj.save()
            #return redirect(f'/login/')
    
    #except Exception as e:
       # print(e)
    #return render(request, 'password.html', context)

#import uuid
#def forgetpassword(request):
 #   if request.method == "POST":
  #      username = request.POST.get('username')
   #     
    #    user_obj = signup.objects.filter(username=username).first()
     #   if not user_obj:
      #      messages.success(request, "Not user found with this username.")
       #     return redirect('forgetpassword')
        
        
        
        #profile_obj, created = Profile.objects.get_or_create(user = user_obj)
        
        #token = str(uuid.uuid4())
        #profile_obj.forget_password_token = token
        #profile_obj.save()
        
        #send_forget_password_mail(user_obj.uemail, token)
        #messages.success(request, 'An Email is sent.')
        #return redirect('forgetpassword')
    
    
   # return render(request, 'forgotpassword.html')
            

   
   
@login_required
def generate_project_report(request):
    # Create a file-like buffer to receive PDF data
    buffer = BytesIO()
    
    # Create the PDF object, using the buffer as its "file"
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    
    # Get the logged-in user's projects
    user_id = request.session.get('user_id')
    projects = add.objects.filter(user_id=user_id).prefetch_related('crawl_results')
    
    # List to hold the flowable elements (content for the PDF)
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    title_style = styles['Title']
    normal_style = styles['Normal']
    
    # Add title to the PDF
    elements.append(Paragraph("Project Report", title_style))
    elements.append(Spacer(1, 12))
    
    # Add user information
    username = request.session.get('username', 'Guest')
    elements.append(Paragraph(f"Generated by: { username }", normal_style))
    elements.append(Spacer(1, 12))
    
    # Add project details in a table format
    for project in projects:
        latest_crawl = project.crawl_results.order_by('-crawl_time').first()
        data = [
            ["Project Name", f"The project name is {project.title}."],
            ["Project ID", f"The project ID is {project.id}."],
            ["URL", f"The URL for this project is {project.url}."],
            ["Last Crawl Date", f"The last crawl was performed on {latest_crawl.crawl_time.strftime('%Y-%m-%d %H:%M') if latest_crawl else 'Not available yet.'}"],
            ["Meta Description", f"The meta description is {latest_crawl.meta_description or 'not available'}"],
            ["Page Title", f"The page title is {latest_crawl.page_title or 'not available'}"],
            ["H1 Tags", f"The H1 tags are {latest_crawl.h1_tags or 'not available'}"],
            ["Internal Links", f"The number of internal links is {latest_crawl.internal_links if latest_crawl else 0}."],
            ["External Links", f"The number of external links is {latest_crawl.external_links if latest_crawl else 0}."],
            ["Broken Links", f"The number of broken links is {latest_crawl.broken_links if latest_crawl else 0}."],
            ["File Size (KB)", f"The file size is {latest_crawl.file_size if latest_crawl else 0} KB."],
            ["Word Count", f"The word count is {latest_crawl.word_count if latest_crawl else 0}."],
            ["Media Files", f"The number of media files is {latest_crawl.media_files if latest_crawl else 0}."],
            ["Page Speed (0-1)", f"The page speed score is {latest_crawl.page_speed if latest_crawl else 0.0}."],
            ["Suggested Keywords", f"The suggested keywords are {latest_crawl.suggested_keywords or 'not available'}"],
            ["SEO Suggestions", f"The SEO suggestions are {latest_crawl.seo_suggestions or 'not available'}"],
            #["Status Code", f"The status code is {latest_crawl.status_code if latest_crawl else 'Not available'}."],
        ]
        if not latest_crawl:
            data.append(["Crawl Status", "No crawl data is available for this project."])

        # Create a table for each project
        table = Table(data, colWidths=[120, 380])  # Adjusted colWidths for better fit
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('LEADING', (0, 0), (-1, -1), 12),  # Line spacing
            ('PADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 20))  # Space between projects

    # Build the PDF
    doc.build(elements)
    
    # Get the value of the buffer
    buffer.seek(0)
    
    # Create the response with the PDF
    response = FileResponse(buffer, as_attachment=True, filename='project_report.pdf')
    return response


import logging
logger = logging.getLogger(__name__)

@login_required(login_url='/login')
@csrf_protect
def change_password(request):
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        # Debug: Log received form data
        logger.debug(f"Form data: old_password={old_password}, new_password={new_password}, confirm_password={confirm_password}")

        # Validate input
        if not all([old_password, new_password, confirm_password]):
            messages.error(request, "All fields are required.")
            logger.warning("Missing form fields in change password request")
            return redirect('change_password')

        # Get user from session
        user_id = request.session.get('user_id')
        if not user_id:
            messages.error(request, "Session expired. Please log in again.")
            logger.error("No user_id in session")
            return redirect('/login')

        try:
            user = signup.objects.get(id=user_id)
        except signup.DoesNotExist:
            messages.error(request, "User not found. Please log in again.")
            logger.error(f"User with id {user_id} not found")
            return redirect('/login')

        # Verify old password
        if user.password != old_password:
            messages.error(request, "Old password is incorrect.")
            logger.warning(f"Incorrect old password for user {user.username}")
            return redirect('change_password')

        # Check if new passwords match
        if new_password != confirm_password:
            messages.error(request, "New passwords do not match.")
            logger.warning("New passwords do not match")
            return redirect('change_password')

        # Update password
        try:
            user.password = new_password
            user.save()
            logger.info(f"Password updated successfully for user {user.username}")
            messages.success(request, "Password changed successfully!")
            # Do not flush session to keep user logged in
            from django.urls import reverse
            account_url = reverse('my_account')
            logger.debug(f"Redirecting to {account_url}")
            return redirect('my_account')  # Redirect to my account page
        except Exception as e:
            logger.error(f"Error updating password for user {user.username}: {str(e)}")
            messages.error(request, "An error occurred while updating the password.")
            return redirect('change_password')

    return render(request, 'changepassword.html')

# SECURITY NOTE: Storing passwords in plain text is insecure. Consider using Django's built-in User model
# with password hashing (django.contrib.auth.models.User) for production.


# New views for forgot password
class TokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return (
            str(user.pk) + str(timestamp) + str(user.uemail)
        )

account_activation_token = TokenGenerator()

def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = signup.objects.get(uemail=email)
        except signup.DoesNotExist:
            messages.error(request, "No user found with this email address.")
            return redirect('forgot_password')
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = account_activation_token.make_token(user)
        reset_link = request.build_absolute_uri(f'/reset-password/{uid}/{token}/')
        subject = 'Password Reset Request'
        message = render_to_string('reset_password_email.html', {
            'user': user,
            'reset_link': reset_link,
        })
        send_mail(
            subject,
            message,
            'your-email@gmail.com',  # From email (set in settings)
            [user.uemail],
            fail_silently=False,
        )
        messages.success(request, "A password reset link has been sent to your email.")
        return redirect('login')
    return render(request, 'forgot_password.html')

def reset_password(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = signup.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, signup.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        if request.method == 'POST':
            password = request.POST.get('password')
            confirm_password = request.POST.get('confirm_password')
            if password != confirm_password:
                messages.error(request, "Passwords do not match.")
                return render(request, 'reset_password.html', {'uidb64': uidb64, 'token': token})
            if len(password) < 6:
                messages.error(request, "Password must be at least 6 characters long.")
                return render(request, 'reset_password.html', {'uidb64': uidb64, 'token': token})
            user.password = password  # Update password (use set_password in production)
            user.save()
            messages.success(request, "Your password has been reset successfully!")
            return redirect('login')
        return render(request, 'reset_password.html', {'uidb64': uidb64, 'token': token})
    else:
        messages.error(request, "The reset link is invalid or has expired.")
        return redirect('forgot_password')
