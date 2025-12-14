"""
Flask Backend Server untuk University Course Scheduling Chatbot
"""

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from scheduler import CourseScheduler
import re

app = Flask(__name__)
CORS(app)

# Session storage (in production, gunakan Redis atau database)
sessions = {}


class ChatSession:
    """Class untuk manage conversation state"""
    
    STATES = {
        'INIT': 'init',
        'COLLECTING_COURSES': 'collecting_courses',
        'COLLECTING_ROOMS': 'collecting_rooms',
        'COLLECTING_TIMES': 'collecting_times',
        'CONFIRMING': 'confirming',
        'GENERATING': 'generating',
        'DONE': 'done'
    }
    
    def __init__(self, session_id):
        self.session_id = session_id
        self.state = self.STATES['INIT']
        self.courses = []
        self.rooms = []
        self.time_slots = []
        self.schedule = None
        
    def reset(self):
        """Reset session"""
        self.state = self.STATES['INIT']
        self.courses = []
        self.rooms = []
        self.time_slots = []
        self.schedule = None


def get_session(session_id):
    """Get or create session"""
    if session_id not in sessions:
        sessions[session_id] = ChatSession(session_id)
    return sessions[session_id]


def parse_list_input(text):
    """
    Parse input text menjadi list
    Support format: "A, B, C" atau "A; B; C" atau "A | B | C" atau per line
    """
    # Remove extra whitespace
    text = text.strip()
    
    # Try different separators
    if ',' in text:
        items = [item.strip() for item in text.split(',')]
    elif ';' in text:
        items = [item.strip() for item in text.split(';')]
    elif '|' in text:
        items = [item.strip() for item in text.split('|')]
    elif '\n' in text:
        items = [item.strip() for item in text.split('\n')]
    else:
        # Single item or space-separated
        items = [item.strip() for item in text.split()]
    
    # Filter empty items
    items = [item for item in items if item]
    
    return items


def generate_response(session, user_message):
    """
    Generate bot response berdasarkan current state dan user message
    """
    user_message = user_message.strip().lower()
    
    # Handle restart command
    if user_message in ['restart', 'mulai lagi', 'reset', 'ulang']:
        session.reset()
        return {
            'message': '🔄 Baik, saya akan mulai dari awal.\n\nSelamat datang di Sistem Penjadwalan Kuliah Otomatis! 🎓\n\nSaya akan membantu Anda membuat jadwal kuliah tanpa bentrok.\n\nSilakan masukkan daftar mata kuliah yang ingin dijadwalkan.\nContoh: Matematika, Fisika, Kimia',
            'state': session.state
        }
    
    # State: INIT
    if session.state == ChatSession.STATES['INIT']:
        session.state = ChatSession.STATES['COLLECTING_COURSES']
        return {
            'message': 'Selamat datang di Sistem Penjadwalan Kuliah Otomatis! 🎓\n\nSaya akan membantu Anda membuat jadwal kuliah tanpa bentrok.\n\nSilakan masukkan daftar mata kuliah yang ingin dijadwalkan.\nContoh: Matematika, Fisika, Kimia, Biologi',
            'state': session.state
        }
    
    # State: COLLECTING_COURSES
    elif session.state == ChatSession.STATES['COLLECTING_COURSES']:
        courses = parse_list_input(user_message)
        if not courses:
            return {
                'message': '❌ Mohon masukkan minimal satu mata kuliah.\nContoh: Matematika, Fisika, Kimia',
                'state': session.state
            }
        
        session.courses = courses
        session.state = ChatSession.STATES['COLLECTING_ROOMS']
        
        return {
            'message': f'✅ Baik, saya catat {len(courses)} mata kuliah:\n' + 
                    '\n'.join([f'  • {course}' for course in courses]) +
                    '\n\nSekarang, silakan masukkan daftar ruangan yang tersedia.\nContoh: R101, R102, R103',
            'state': session.state
        }
    
    # State: COLLECTING_ROOMS
    elif session.state == ChatSession.STATES['COLLECTING_ROOMS']:
        rooms = parse_list_input(user_message)
        if not rooms:
            return {
                'message': '❌ Mohon masukkan minimal satu ruangan.\nContoh: R101, R102, R103',
                'state': session.state
            }
        
        session.rooms = rooms
        session.state = ChatSession.STATES['COLLECTING_TIMES']
        
        return {
            'message': f'✅ Baik, saya catat {len(rooms)} ruangan:\n' +
                    '\n'.join([f'  • {room}' for room in rooms]) +
                    '\n\nTerakhir, silakan masukkan daftar waktu yang tersedia.\nContoh: 08:00-10:00, 10:00-12:00, 13:00-15:00',
            'state': session.state
        }
    
    # State: COLLECTING_TIMES
    elif session.state == ChatSession.STATES['COLLECTING_TIMES']:
        time_slots = parse_list_input(user_message)
        if not time_slots:
            return {
                'message': '❌ Mohon masukkan minimal satu waktu.\nContoh: 08:00-10:00, 10:00-12:00',
                'state': session.state
            }
        
        session.time_slots = time_slots
        session.state = ChatSession.STATES['CONFIRMING']
        
        # Create confirmation message
        total_slots = len(session.rooms) * len(session.time_slots)
        can_schedule = len(session.courses) <= total_slots
        
        confirmation = f'✅ Baik, saya catat {len(time_slots)} waktu:\n' + \
                        '\n'.join([f'  • {time}' for time in time_slots]) + \
                        f'\n\n📊 Ringkasan:\n' + \
                        f'  • Mata Kuliah: {len(session.courses)}\n' + \
                        f'  • Ruangan: {len(session.rooms)}\n' + \
                        f'  • Waktu: {len(session.time_slots)}\n' + \
                        f'  • Total Slot Tersedia: {total_slots}\n\n'
        
        if not can_schedule:
            confirmation += f'⚠️ PERINGATAN: Jumlah mata kuliah ({len(session.courses)}) lebih banyak dari slot tersedia ({total_slots}).\n'
            confirmation += 'Mungkin tidak semua mata kuliah dapat dijadwalkan.\n\n'
        
        confirmation += 'Apakah data sudah benar? (ya/tidak)'
        
        return {
            'message': confirmation,
            'state': session.state
        }
    
    # State: CONFIRMING
    elif session.state == ChatSession.STATES['CONFIRMING']:
        if user_message in ['ya', 'yes', 'benar', 'ok', 'oke', 'lanjut']:
            session.state = ChatSession.STATES['GENERATING']
            
            # Generate schedule
            try:
                scheduler = CourseScheduler(
                    session.courses,
                    session.rooms,
                    session.time_slots
                )
                
                result = scheduler.generate_schedule(use_backtracking=True)
                
                if result:
                    session.schedule = scheduler.get_formatted_schedule()
                    is_valid, conflicts = scheduler.validate_schedule()
                    
                    response = '🎉 Jadwal berhasil dibuat tanpa bentrok!\n\n'
                    response += '📅 JADWAL KULIAH:\n'
                    response += '─' * 50 + '\n'
                    
                    for item in session.schedule:
                        response += f"📚 {item['course']}\n"
                        response += f"   🏫 Ruangan: {item['room']}\n"
                        response += f"   🕐 Waktu: {item['time']}\n"
                        response += '─' * 50 + '\n'
                    
                    response += '\n✅ Validasi: Tidak ada bentrok waktu!\n\n'
                    response += 'Ketik "restart" untuk membuat jadwal baru.'
                    
                    session.state = ChatSession.STATES['DONE']
                    
                    return {
                        'message': response,
                        'state': session.state,
                        'schedule': session.schedule
                    }
                else:
                    response = '❌ Maaf, tidak dapat membuat jadwal tanpa bentrok dengan data yang diberikan.\n\n'
                    response += 'Kemungkinan:\n'
                    response += '  • Jumlah mata kuliah terlalu banyak untuk slot yang tersedia\n'
                    response += '  • Kombinasi ruangan dan waktu tidak mencukupi\n\n'
                    response += 'Ketik "restart" untuk mencoba lagi dengan data berbeda.'
                    
                    session.state = ChatSession.STATES['DONE']
                    
                    return {
                        'message': response,
                        'state': session.state
                    }
                    
            except Exception as e:
                return {
                    'message': f'❌ Terjadi kesalahan: {str(e)}\n\nKetik "restart" untuk mencoba lagi.',
                    'state': session.state
                }
        
        elif user_message in ['tidak', 'no', 'salah', 'belum']:
            session.reset()
            return {
                'message': '🔄 Baik, mari kita mulai dari awal.\n\nSilakan masukkan daftar mata kuliah yang ingin dijadwalkan.\nContoh: Matematika, Fisika, Kimia',
                'state': session.state
            }
        else:
            return {
                'message': '❓ Mohon jawab dengan "ya" atau "tidak".',
                'state': session.state
            }
    
    # State: DONE
    elif session.state == ChatSession.STATES['DONE']:
        return {
            'message': 'Proses penjadwalan sudah selesai.\n\nKetik "restart" jika ingin membuat jadwal baru.',
            'state': session.state
        }
    
    return {
        'message': 'Maaf, terjadi kesalahan. Ketik "restart" untuk memulai lagi.',
        'state': session.state
    }


@app.route('/')
def index():
    """Render main page"""
    return render_template('index.html')


@app.route('/api/chat', methods=['POST'])
def chat():
    """
    API endpoint untuk chatbot
    Expects JSON: { "session_id": "xxx", "message": "user message" }
    Returns JSON: { "response": "bot response", "state": "current_state", "schedule": [...] }
    """
    try:
        data = request.get_json()
        session_id = data.get('session_id', 'default')
        user_message = data.get('message', '')
        
        if not user_message:
            return jsonify({
                'response': 'Mohon masukkan pesan.',
                'state': 'error'
            }), 400
        
        # Get or create session
        session = get_session(session_id)
        
        # Generate response
        response_data = generate_response(session, user_message)
        
        return jsonify({
            'response': response_data['message'],
            'state': response_data['state'],
            'schedule': response_data.get('schedule', None)
        })
        
    except Exception as e:
        return jsonify({
            'response': f'Terjadi kesalahan: {str(e)}',
            'state': 'error'
        }), 500


@app.route('/api/reset', methods=['POST'])
def reset():
    """Reset session"""
    try:
        data = request.get_json()
        session_id = data.get('session_id', 'default')
        
        if session_id in sessions:
            sessions[session_id].reset()
        
        return jsonify({
            'success': True,
            'message': 'Session berhasil direset'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Gagal reset: {str(e)}'
        }), 500


if __name__ == '__main__':
    print("🚀 Starting University Course Scheduling Chatbot Server...")
    print("📍 Server running on http://localhost:5000")
    print("🤖 Chatbot ready to help with scheduling!")
    app.run(debug=True, port=5000) 