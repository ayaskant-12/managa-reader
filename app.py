# app.py (main application file)
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
import os
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:ayaskant@localhost/manga_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configure upload settings
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'covers'), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'pages'), exist_ok=True)

db = SQLAlchemy(app)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_file(file, subfolder):
    if file and allowed_file(file.filename):
        # Generate unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = secure_filename(file.filename)
        filename = f"{timestamp}_{filename}"
        
        # Save file
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], subfolder)
        os.makedirs(upload_path, exist_ok=True)
        file_path = os.path.join(upload_path, filename)
        file.save(file_path)
        
        return f"/static/uploads/{subfolder}/{filename}"
    return None

# Database Models
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), default='user')
    
    # Add relationships for future features
    bookmarks = db.relationship('Bookmark', backref='user', lazy=True, cascade="all, delete-orphan")
    reading_history = db.relationship('ReadingHistory', backref='user', lazy=True, cascade="all, delete-orphan")
    comments = db.relationship('Comment', backref='user', lazy=True, cascade="all, delete-orphan")
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Manga Models
class Manga(db.Model):
    __tablename__ = 'manga'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    genres = db.Column(db.String(200))
    cover_url = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    chapters = db.relationship('Chapter', backref='manga', lazy=True, cascade="all, delete-orphan")
    bookmarks = db.relationship('Bookmark', backref='manga', lazy=True, cascade="all, delete-orphan")
    reading_history = db.relationship('ReadingHistory', backref='manga', lazy=True, cascade="all, delete-orphan")

class Chapter(db.Model):
    __tablename__ = 'chapters'
    id = db.Column(db.Integer, primary_key=True)
    manga_id = db.Column(db.Integer, db.ForeignKey('manga.id'), nullable=False)
    chapter_number = db.Column(db.Float, nullable=False)
    title = db.Column(db.String(200))
    release_date = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    pages = db.relationship('Page', backref='chapter', lazy=True, cascade="all, delete-orphan")
    bookmarks = db.relationship('Bookmark', backref='chapter', lazy=True, cascade="all, delete-orphan")
    reading_history = db.relationship('ReadingHistory', backref='chapter', lazy=True, cascade="all, delete-orphan")
    comments = db.relationship('Comment', backref='chapter', lazy=True, cascade="all, delete-orphan")

class Page(db.Model):
    __tablename__ = 'pages'
    id = db.Column(db.Integer, primary_key=True)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapters.id'), nullable=False)
    page_number = db.Column(db.Integer, nullable=False)
    image_url = db.Column(db.String(500), nullable=False)

# Comment Model
class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapters.id'), nullable=False)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

# Enhanced Bookmark Model
class Bookmark(db.Model):
    __tablename__ = 'bookmarks'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    manga_id = db.Column(db.Integer, db.ForeignKey('manga.id'), nullable=False)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapters.id'), nullable=True)
    page_number = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    note = db.Column(db.Text)

# Enhanced ReadingHistory Model
class ReadingHistory(db.Model):
    __tablename__ = 'reading_history'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapters.id'), nullable=False)
    manga_id = db.Column(db.Integer, db.ForeignKey('manga.id'), nullable=False)
    page_number = db.Column(db.Integer, default=1)
    read_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    read_duration = db.Column(db.Integer, default=0)

# Authentication Decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'admin':
            flash('Admin privileges required.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def index():
    # Get some featured manga for the homepage
    featured_manga = Manga.query.order_by(db.func.random()).limit(6).all()
    return render_template('index.html', featured_manga=featured_manga)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return redirect(url_for('register'))
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists!', 'danger')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered!', 'danger')
            return redirect(url_for('register'))
        
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password!', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    user = User.query.get(session['user_id'])
    bookmarks = Bookmark.query.filter_by(user_id=user.id).join(Manga).order_by(Bookmark.created_at.desc()).all()
    
    # Get recent reading history
    recent_history = ReadingHistory.query.filter_by(user_id=user.id).join(Chapter).join(Manga)\
        .order_by(ReadingHistory.read_at.desc()).limit(5).all()
    
    # Get total unique manga read
    total_manga_read = db.session.query(db.func.count(db.distinct(ReadingHistory.manga_id)))\
        .filter(ReadingHistory.user_id == user.id).scalar()
    
    return render_template('dashboard.html', user=user, bookmarks=bookmarks, 
                         recent_history=recent_history, total_manga_read=total_manga_read)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user = User.query.get(session['user_id'])
    
    if request.method == 'POST':
        user.email = request.form['email']
        
        if request.form['new_password']:
            if request.form['new_password'] == request.form['confirm_password']:
                user.set_password(request.form['new_password'])
            else:
                flash('New passwords do not match!', 'danger')
                return redirect(url_for('profile'))
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))
    
    return render_template('profile.html', user=user)

# Manga Library Routes
@app.route('/manga')
def manga_list():
    page = request.args.get('page', 1, type=int)
    genre_filter = request.args.get('genre', '')
    search_query = request.args.get('q', '')
    
    # Build query based on filters
    query = Manga.query
    
    if genre_filter:
        query = query.filter(Manga.genres.ilike(f'%{genre_filter}%'))
    
    if search_query:
        query = query.filter(
            db.or_(
                Manga.title.ilike(f'%{search_query}%'),
                Manga.author.ilike(f'%{search_query}%'),
                Manga.description.ilike(f'%{search_query}%')
            )
        )
    
    manga = query.order_by(Manga.title).paginate(page=page, per_page=12, error_out=False)
    
    # Get unique genres for filter dropdown
    all_manga = Manga.query.all()
    genres = set()
    for m in all_manga:
        if m.genres:
            for genre in m.genres.split(','):
                genres.add(genre.strip())
    
    return render_template('manga_list.html', manga=manga, genres=sorted(genres), 
                          genre_filter=genre_filter, search_query=search_query)

@app.route('/manga/<int:manga_id>')
def manga_detail(manga_id):
    manga = Manga.query.get_or_404(manga_id)
    chapters = Chapter.query.filter_by(manga_id=manga_id).order_by(Chapter.chapter_number).all()
    
    # Check if user has bookmarked this manga
    is_bookmarked = False
    if 'user_id' in session:
        bookmark = Bookmark.query.filter_by(user_id=session['user_id'], manga_id=manga_id).first()
        is_bookmarked = bookmark is not None
    
    return render_template('manga_detail.html', manga=manga, chapters=chapters, is_bookmarked=is_bookmarked)

@app.route('/manga/<int:manga_id>/chapter/<float:chapter_number>')
@login_required
def read_chapter(manga_id, chapter_number):
    manga = Manga.query.get_or_404(manga_id)
    chapter = Chapter.query.filter_by(manga_id=manga_id, chapter_number=chapter_number).first_or_404()
    pages = Page.query.filter_by(chapter_id=chapter.id).order_by(Page.page_number).all()
    
    # Get next and previous chapters for navigation
    prev_chapter = Chapter.query.filter(
        Chapter.manga_id == manga_id,
        Chapter.chapter_number < chapter_number
    ).order_by(Chapter.chapter_number.desc()).first()
    
    next_chapter = Chapter.query.filter(
        Chapter.manga_id == manga_id,
        Chapter.chapter_number > chapter_number
    ).order_by(Chapter.chapter_number.asc()).first()
    
    # Check for existing reading history
    existing_history = ReadingHistory.query.filter_by(
        user_id=session['user_id'], 
        chapter_id=chapter.id
    ).first()
    
    if existing_history:
        # Update existing history
        existing_history.read_at = db.func.current_timestamp()
    else:
        # Create new reading history
        history = ReadingHistory(
            user_id=session['user_id'],
            chapter_id=chapter.id,
            manga_id=manga_id,
            read_at=db.func.current_timestamp()
        )
        db.session.add(history)
    
    db.session.commit()
    
    # Get last read page from bookmark if exists
    last_page = 1
    bookmark = Bookmark.query.filter_by(
        user_id=session['user_id'],
        manga_id=manga_id,
        chapter_id=chapter.id
    ).first()
    
    if bookmark and bookmark.page_number:
        last_page = bookmark.page_number
    
    return render_template('chapter_reader.html', 
                         manga=manga, 
                         chapter=chapter, 
                         pages=pages,
                         prev_chapter=prev_chapter,
                         next_chapter=next_chapter,
                         last_page=last_page)

# Reading History Routes
@app.route('/history')
@login_required
def reading_history():
    page = request.args.get('page', 1, type=int)
    
    history = ReadingHistory.query.filter_by(user_id=session['user_id'])\
        .join(Chapter).join(Manga)\
        .order_by(ReadingHistory.read_at.desc())\
        .paginate(page=page, per_page=20, error_out=False)
    
    return render_template('reading_history.html', history=history)

@app.route('/history/clear', methods=['POST'])
@login_required
def clear_reading_history():
    # Delete all reading history for the user
    ReadingHistory.query.filter_by(user_id=session['user_id']).delete()
    db.session.commit()
    
    flash('Reading history cleared!', 'success')
    return redirect(url_for('reading_history'))

# Bookmark Routes
@app.route('/bookmarks')
@login_required
def bookmarks():
    page = request.args.get('page', 1, type=int)
    
    bookmarks = Bookmark.query.filter_by(user_id=session['user_id'])\
        .join(Manga)\
        .order_by(Bookmark.created_at.desc())\
        .paginate(page=page, per_page=20, error_out=False)
    
    return render_template('bookmarks.html', bookmarks=bookmarks)

@app.route('/manga/<int:manga_id>/bookmark', methods=['POST'])
@login_required
def toggle_bookmark(manga_id):
    manga = Manga.query.get_or_404(manga_id)
    
    # Check if bookmark already exists
    bookmark = Bookmark.query.filter_by(
        user_id=session['user_id'], 
        manga_id=manga_id
    ).first()
    
    if bookmark:
        db.session.delete(bookmark)
        db.session.commit()
        flash('Bookmark removed!', 'info')
    else:
        new_bookmark = Bookmark(
            user_id=session['user_id'],
            manga_id=manga_id
        )
        db.session.add(new_bookmark)
        db.session.commit()
        flash('Manga bookmarked!', 'success')
    
    return redirect(url_for('manga_detail', manga_id=manga_id))

@app.route('/bookmark/<int:bookmark_id>/delete', methods=['POST'])
@login_required
def delete_bookmark(bookmark_id):
    bookmark = Bookmark.query.get_or_404(bookmark_id)
    
    # Verify ownership
    if bookmark.user_id != session['user_id']:
        flash('You are not authorized to delete this bookmark!', 'danger')
        return redirect(url_for('bookmarks'))
    
    db.session.delete(bookmark)
    db.session.commit()
    
    flash('Bookmark deleted!', 'success')
    return redirect(url_for('bookmarks'))

@app.route('/bookmark/page', methods=['POST'])
@login_required
def bookmark_page():
    manga_id = request.form.get('manga_id')
    chapter_id = request.form.get('chapter_id')
    page_number = request.form.get('page_number')
    note = request.form.get('note', '')
    
    manga = Manga.query.get_or_404(manga_id)
    chapter = Chapter.query.get_or_404(chapter_id)
    
    # Check if bookmark already exists
    bookmark = Bookmark.query.filter_by(
        user_id=session['user_id'],
        manga_id=manga_id,
        chapter_id=chapter_id
    ).first()
    
    if bookmark:
        # Update existing bookmark
        bookmark.page_number = page_number
        bookmark.note = note
        bookmark.created_at = db.func.current_timestamp()
    else:
        # Create new bookmark
        bookmark = Bookmark(
            user_id=session['user_id'],
            manga_id=manga_id,
            chapter_id=chapter_id,
            page_number=page_number,
            note=note
        )
        db.session.add(bookmark)
    
    db.session.commit()
    
    flash('Page bookmarked!', 'success')
    return redirect(url_for('read_chapter', manga_id=manga_id, chapter_number=chapter.chapter_number))

# Dark mode toggle
@app.route('/toggle-dark-mode', methods=['POST'])
@login_required
def toggle_dark_mode():
    session['dark_mode'] = request.json.get('dark_mode', False)
    return jsonify({'success': True})

# Comment Routes
@app.route('/chapter/<int:chapter_id>/comment', methods=['POST'])
@login_required
def add_comment(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)
    manga = Manga.query.get_or_404(chapter.manga_id)
    
    text = request.form.get('text', '').strip()
    
    if not text:
        flash('Comment cannot be empty!', 'danger')
        return redirect(url_for('read_chapter', manga_id=manga.id, chapter_number=chapter.chapter_number))
    
    if len(text) > 1000:
        flash('Comment is too long! Maximum 1000 characters allowed.', 'danger')
        return redirect(url_for('read_chapter', manga_id=manga.id, chapter_number=chapter.chapter_number))
    
    new_comment = Comment(
        user_id=session['user_id'],
        chapter_id=chapter_id,
        text=text
    )
    
    db.session.add(new_comment)
    db.session.commit()
    
    flash('Comment added successfully!', 'success')
    return redirect(url_for('read_chapter', manga_id=manga.id, chapter_number=chapter.chapter_number))

@app.route('/comment/<int:comment_id>/delete', methods=['POST'])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    chapter = Chapter.query.get_or_404(comment.chapter_id)
    manga = Manga.query.get_or_404(chapter.manga_id)
    
    # Check if user owns the comment or is an admin
    if comment.user_id != session['user_id'] and session.get('role') != 'admin':
        flash('You are not authorized to delete this comment!', 'danger')
        return redirect(url_for('read_chapter', manga_id=manga.id, chapter_number=chapter.chapter_number))
    
    db.session.delete(comment)
    db.session.commit()
    
    flash('Comment deleted successfully!', 'success')
    return redirect(url_for('read_chapter', manga_id=manga.id, chapter_number=chapter.chapter_number))

@app.route('/comment/<int:comment_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    chapter = Chapter.query.get_or_404(comment.chapter_id)
    manga = Manga.query.get_or_404(chapter.manga_id)
    
    # Check if user owns the comment
    if comment.user_id != session['user_id']:
        flash('You are not authorized to edit this comment!', 'danger')
        return redirect(url_for('read_chapter', manga_id=manga.id, chapter_number=chapter.chapter_number))
    
    if request.method == 'POST':
        text = request.form.get('text', '').strip()
        
        if not text:
            flash('Comment cannot be empty!', 'danger')
            return redirect(url_for('edit_comment', comment_id=comment_id))
        
        if len(text) > 1000:
            flash('Comment is too long! Maximum 1000 characters allowed.', 'danger')
            return redirect(url_for('edit_comment', comment_id=comment_id))
        
        comment.text = text
        db.session.commit()
        
        flash('Comment updated successfully!', 'success')
        return redirect(url_for('read_chapter', manga_id=manga.id, chapter_number=chapter.chapter_number))
    
    return render_template('edit_comment.html', comment=comment, manga=manga, chapter=chapter)

# Admin Dashboard
@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    # Get statistics for the dashboard
    total_manga = Manga.query.count()
    total_users = User.query.count()
    total_chapters = Chapter.query.count()
    recent_users = User.query.order_by(User.id.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html', 
                         total_manga=total_manga,
                         total_users=total_users,
                         total_chapters=total_chapters,
                         recent_users=recent_users)

# Admin Manga Management
@app.route('/admin/manga')
@login_required
@admin_required
def admin_manga_list():
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('q', '')
    
    query = Manga.query
    
    if search_query:
        query = query.filter(
            db.or_(
                Manga.title.ilike(f'%{search_query}%'),
                Manga.author.ilike(f'%{search_query}%')
            )
        )
    
    manga_list = query.order_by(Manga.title).paginate(page=page, per_page=10, error_out=False)
    
    return render_template('admin/manga_list.html', manga_list=manga_list, search_query=search_query)

@app.route('/admin/manga/add', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_add_manga():
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        description = request.form['description']
        genres = request.form['genres']
        
        # Handle cover upload
        cover_url = '/static/images/default-cover.jpg'
        if 'cover' in request.files:
            file = request.files['cover']
            if file and file.filename != '':
                uploaded_path = save_uploaded_file(file, 'covers')
                if uploaded_path:
                    cover_url = uploaded_path
        
        new_manga = Manga(
            title=title,
            author=author,
            description=description,
            genres=genres,
            cover_url=cover_url
        )
        
        db.session.add(new_manga)
        db.session.commit()
        
        flash('Manga added successfully!', 'success')
        return redirect(url_for('admin_manga_list'))
    
    return render_template('admin/add_manga.html')

@app.route('/admin/manga/<int:manga_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit_manga(manga_id):
    manga = Manga.query.get_or_404(manga_id)
    
    if request.method == 'POST':
        manga.title = request.form['title']
        manga.author = request.form['author']
        manga.description = request.form['description']
        manga.genres = request.form['genres']
        
        # Handle cover upload
        if 'cover' in request.files:
            file = request.files['cover']
            if file and file.filename != '':
                uploaded_path = save_uploaded_file(file, 'covers')
                if uploaded_path:
                    manga.cover_url = uploaded_path
        
        db.session.commit()
        flash('Manga updated successfully!', 'success')
        return redirect(url_for('admin_manga_list'))
    
    return render_template('admin/edit_manga.html', manga=manga)

@app.route('/admin/manga/<int:manga_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_manga(manga_id):
    manga = Manga.query.get_or_404(manga_id)
    
    # Delete associated chapters and pages (cascading deletes should handle this)
    db.session.delete(manga)
    db.session.commit()
    
    flash('Manga deleted successfully!', 'success')
    return redirect(url_for('admin_manga_list'))

# Admin Chapter Management
@app.route('/admin/manga/<int:manga_id>/chapters')
@login_required
@admin_required
def admin_chapter_list(manga_id):
    manga = Manga.query.get_or_404(manga_id)
    chapters = Chapter.query.filter_by(manga_id=manga_id).order_by(Chapter.chapter_number).all()
    
    return render_template('admin/chapter_list.html', manga=manga, chapters=chapters)

@app.route('/admin/manga/<int:manga_id>/chapters/add', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_add_chapter(manga_id):
    manga = Manga.query.get_or_404(manga_id)
    
    if request.method == 'POST':
        chapter_number = float(request.form['chapter_number'])
        title = request.form['title']
        
        # Check if chapter already exists
        existing_chapter = Chapter.query.filter_by(manga_id=manga_id, chapter_number=chapter_number).first()
        if existing_chapter:
            flash('Chapter already exists!', 'danger')
            return redirect(url_for('admin_add_chapter', manga_id=manga_id))
        
        new_chapter = Chapter(
            manga_id=manga_id,
            chapter_number=chapter_number,
            title=title
        )
        
        db.session.add(new_chapter)
        db.session.commit()
        
        flash('Chapter added successfully!', 'success')
        return redirect(url_for('admin_chapter_list', manga_id=manga_id))
    
    return render_template('admin/add_chapter.html', manga=manga)

@app.route('/admin/chapter/<int:chapter_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_chapter(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)
    manga_id = chapter.manga_id
    
    db.session.delete(chapter)
    db.session.commit()
    
    flash('Chapter deleted successfully!', 'success')
    return redirect(url_for('admin_chapter_list', manga_id=manga_id))

# Admin Page Management
@app.route('/admin/chapter/<int:chapter_id>/pages/upload', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_upload_pages(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)
    manga = Manga.query.get_or_404(chapter.manga_id)
    
    if request.method == 'POST':
        # Handle multiple file uploads
        files = request.files.getlist('pages')
        page_number = 1
        
        for file in files:
            if file and file.filename != '':
                uploaded_path = save_uploaded_file(file, 'pages')
                if uploaded_path:
                    new_page = Page(
                        chapter_id=chapter_id,
                        page_number=page_number,
                        image_url=uploaded_path
                    )
                    db.session.add(new_page)
                    page_number += 1
        
        db.session.commit()
        flash(f'{page_number - 1} pages uploaded successfully!', 'success')
        return redirect(url_for('admin_chapter_list', manga_id=manga.id))
    
    return render_template('admin/upload_pages.html', chapter=chapter, manga=manga)

@app.route('/admin/chapter/<int:chapter_id>/pages/upload-zip', methods=['POST'])
@login_required
@admin_required
def admin_upload_zip(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)
    
    if 'zip_file' in request.files:
        file = request.files['zip_file']
        if file and file.filename != '' and file.filename.endswith('.zip'):
            # Save the zip file temporarily
            import zipfile
            import tempfile
            
            temp_dir = tempfile.mkdtemp()
            zip_path = os.path.join(temp_dir, file.filename)
            file.save(zip_path)
            
            # Extract zip file
            extracted_dir = os.path.join(temp_dir, 'extracted')
            os.makedirs(extracted_dir, exist_ok=True)
            
            try:
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(extracted_dir)
                
                # Process extracted images
                image_files = []
                for root, dirs, files in os.walk(extracted_dir):
                    for filename in files:
                        if allowed_file(filename):
                            image_files.append(os.path.join(root, filename))
                
                # Sort files naturally (to handle page order correctly)
                import re
                image_files.sort(key=lambda x: [int(c) if c.isdigit() else c for c in re.split(r'(\d+)', x)])
                
                # Add pages to database
                page_number = 1
                for image_path in image_files:
                    # Generate a unique filename
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    new_filename = f"{timestamp}_{page_number}_{os.path.basename(image_path)}"
                    new_filename = secure_filename(new_filename)
                    
                    # Define destination path
                    dest_path = os.path.join(app.config['UPLOAD_FOLDER'], 'pages', new_filename)
                    
                    # Move file to upload directory
                    os.rename(image_path, dest_path)
                    
                    # Add to database
                    new_page = Page(
                        chapter_id=chapter_id,
                        page_number=page_number,
                        image_url=f"/static/uploads/pages/{new_filename}"
                    )
                    db.session.add(new_page)
                    page_number += 1
                
                db.session.commit()
                flash(f'{page_number - 1} pages uploaded from ZIP file!', 'success')
                
            except Exception as e:
                flash(f'Error processing ZIP file: {str(e)}', 'danger')
            
            finally:
                # Clean up temporary files
                import shutil
                shutil.rmtree(temp_dir)
        
        else:
            flash('Invalid file format. Please upload a ZIP file.', 'danger')
    
    return redirect(url_for('admin_chapter_list', manga_id=chapter.manga_id))

@app.route('/admin/page/<int:page_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_page(page_id):
    page = Page.query.get_or_404(page_id)
    chapter_id = page.chapter_id
    chapter = Chapter.query.get_or_404(chapter_id)
    
    # Delete the physical file
    if page.image_url.startswith('/static/uploads/'):
        file_path = page.image_url.replace('/static/', 'static/')
        if os.path.exists(file_path):
            os.remove(file_path)
    
    db.session.delete(page)
    db.session.commit()
    
    flash('Page deleted successfully!', 'success')
    return redirect(url_for('admin_upload_pages', chapter_id=chapter_id))

@app.route('/admin/chapter/<int:chapter_id>/pages')
@login_required
@admin_required
def admin_view_pages(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)
    manga = Manga.query.get_or_404(chapter.manga_id)
    pages = Page.query.filter_by(chapter_id=chapter_id).order_by(Page.page_number).all()
    
    return render_template('admin/view_pages.html', chapter=chapter, manga=manga, pages=pages)

# Admin User Management
@app.route('/admin/users')
@login_required
@admin_required
def admin_user_list():
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('q', '')
    
    query = User.query
    
    if search_query:
        query = query.filter(
            db.or_(
                User.username.ilike(f'%{search_query}%'),
                User.email.ilike(f'%{search_query}%')
            )
        )
    
    users = query.order_by(User.username).paginate(page=page, per_page=10, error_out=False)
    
    return render_template('admin/user_list.html', users=users, search_query=search_query)

@app.route('/admin/user/<int:user_id>/toggle-admin', methods=['POST'])
@login_required
@admin_required
def admin_toggle_user_role(user_id):
    user = User.query.get_or_404(user_id)
    
    # Prevent self-demotion
    if user.id == session['user_id']:
        flash('You cannot change your own role!', 'danger')
        return redirect(url_for('admin_user_list'))
    
    user.role = 'admin' if user.role != 'admin' else 'user'
    db.session.commit()
    
    flash(f'User role updated to {user.role}!', 'success')
    return redirect(url_for('admin_user_list'))

@app.route('/admin/user/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    # Prevent self-deletion
    if user.id == session['user_id']:
        flash('You cannot delete your own account!', 'danger')
        return redirect(url_for('admin_user_list'))
    
    db.session.delete(user)
    db.session.commit()
    
    flash('User deleted successfully!', 'success')
    return redirect(url_for('admin_user_list'))

# Admin comment management
@app.route('/admin/comments')
@login_required
@admin_required
def admin_comment_list():
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('q', '')
    
    query = Comment.query.join(User).join(Chapter).join(Manga)
    
    if search_query:
        query = query.filter(
            db.or_(
                Comment.text.ilike(f'%{search_query}%'),
                User.username.ilike(f'%{search_query}%'),
                Manga.title.ilike(f'%{search_query}%')
            )
        )
    
    comments = query.order_by(Comment.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    
    return render_template('admin/comment_list.html', comments=comments, search_query=search_query)

@app.route('/admin/comment/<int:comment_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    
    db.session.delete(comment)
    db.session.commit()
    
    flash('Comment deleted successfully!', 'success')
    return redirect(url_for('admin_comment_list'))

# Initialize database with sample data
def init_db():
    with app.app_context():
        db.create_all()
        
        # Create admin user if not exists
        if not User.query.filter_by(username='admin').first():
            admin_user = User(username='admin', email='admin@manga.com', role='admin')
            admin_user.set_password('admin123')
            db.session.add(admin_user)
            db.session.commit()
            print("Admin user created: admin/admin123")
        
        # Add sample manga if none exists
        if Manga.query.count() == 0:
            sample_manga = Manga(
                title="One Piece",
                author="Eiichiro Oda",
                description="Monkey D. Luffy and his pirate crew explore the Grand Line in search of the world's ultimate treasure.",
                genres="Adventure, Fantasy, Action, Comedy",
                cover_url="/static/images/default-cover.jpg"
            )
            db.session.add(sample_manga)
            db.session.commit()
            print("Sample manga added")

if __name__ == '__main__':
    init_db()
    app.run(debug=True)