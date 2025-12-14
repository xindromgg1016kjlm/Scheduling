"""
University Course Scheduler using Constraint Satisfaction Problem (CSP)
Menggunakan algoritma Backtracking untuk menyelesaikan scheduling problem
"""

class CourseScheduler:
    def __init__(self, courses, rooms, time_slots):
        """
        Initialize scheduler dengan courses, rooms, dan time slots
        
        Args:
            courses: list of course names
            rooms: list of available rooms
            time_slots: list of available time slots
        """
        self.courses = courses
        self.rooms = rooms
        self.time_slots = time_slots
        self.schedule = {}
        self.domain = self._create_domain()
        
    def _create_domain(self):
        """
        Membuat domain untuk setiap course (semua kemungkinan (room, time) pairs)
        """
        domain = {}
        for course in self.courses:
            domain[course] = []
            for room in self.rooms:
                for time_slot in self.time_slots:
                    domain[course].append((room, time_slot))
        return domain
    
    def _is_consistent(self, course, assignment, schedule):
        """
        Check apakah assignment (room, time) untuk course tidak conflict dengan schedule yang ada
        
        Args:
            course: nama course yang akan di-assign
            assignment: tuple (room, time_slot)
            schedule: current schedule dictionary
            
        Returns:
            True jika tidak ada conflict, False otherwise
        """
        room, time_slot = assignment
        
        # Check semua courses yang sudah di-schedule
        for scheduled_course, (scheduled_room, scheduled_time) in schedule.items():
            # Constraint 1: Tidak boleh ada 2 course di room yang sama pada waktu yang sama
            if scheduled_room == room and scheduled_time == time_slot:
                return False
            
            # Optional Constraint: Bisa ditambahkan constraint lain di sini
            # Misalnya: satu course tidak boleh dijadwalkan 2x, dll
            
        return True
    
    def _backtracking(self, unassigned_courses, schedule):
        """
        Algoritma Backtracking untuk CSP
        
        Args:
            unassigned_courses: list of courses yang belum di-assign
            schedule: current schedule dictionary
            
        Returns:
            schedule dictionary jika berhasil, None jika gagal
        """
        # Base case: semua course sudah di-assign
        if not unassigned_courses:
            return schedule
        
        # Pilih course pertama dari unassigned courses
        course = unassigned_courses[0]
        remaining_courses = unassigned_courses[1:]
        
        # Try setiap possible assignment dari domain
        for assignment in self.domain[course]:
            # Check consistency
            if self._is_consistent(course, assignment, schedule):
                # Assign course ke schedule
                schedule[course] = assignment
                
                # Recursive call dengan course yang tersisa
                result = self._backtracking(remaining_courses, schedule.copy())
                
                # Jika berhasil, return result
                if result is not None:
                    return result
                
                # Backtrack: remove assignment
                del schedule[course]
        
        # Tidak ada assignment yang valid
        return None
    
    def _greedy_schedule(self):
        """
        Algoritma Greedy sebagai alternatif/fallback
        Assign course ke slot pertama yang available
        """
        schedule = {}
        used_slots = set()
        
        for course in self.courses:
            assigned = False
            for room in self.rooms:
                if assigned:
                    break
                for time_slot in self.time_slots:
                    slot = (room, time_slot)
                    if slot not in used_slots:
                        schedule[course] = slot
                        used_slots.add(slot)
                        assigned = True
                        break
            
            if not assigned:
                # Tidak cukup slot untuk semua courses
                return None
        
        return schedule
    
    def generate_schedule(self, use_backtracking=True):
        """
        Generate schedule menggunakan CSP algorithm
        
        Args:
            use_backtracking: True untuk backtracking, False untuk greedy
            
        Returns:
            dictionary: {course: (room, time_slot)} jika berhasil
            None: jika tidak bisa membuat schedule tanpa conflict
        """
        if use_backtracking:
            result = self._backtracking(self.courses.copy(), {})
        else:
            result = self._greedy_schedule()
        
        if result:
            self.schedule = result
            return result
        else:
            return None
    
    def get_formatted_schedule(self):
        """
        Format schedule untuk display
        
        Returns:
            list of dictionaries dengan format yang mudah dibaca
        """
        if not self.schedule:
            return []
        
        formatted = []
        for course, (room, time_slot) in sorted(self.schedule.items()):
            formatted.append({
                'course': course,
                'room': room,
                'time': time_slot
            })
        
        return formatted
    
    def validate_schedule(self):
        """
        Validate bahwa schedule tidak ada conflict
        
        Returns:
            (is_valid, conflicts): tuple of boolean dan list of conflicts
        """
        conflicts = []
        slot_usage = {}
        
        for course, (room, time_slot) in self.schedule.items():
            slot = (room, time_slot)
            if slot in slot_usage:
                conflicts.append({
                    'course1': slot_usage[slot],
                    'course2': course,
                    'room': room,
                    'time': time_slot
                })
            else:
                slot_usage[slot] = course
        
        return len(conflicts) == 0, conflicts


def test_scheduler():
    """
    Test function untuk scheduler
    """
    courses = ['Matematika', 'Fisika', 'Kimia', 'Biologi']
    rooms = ['R101', 'R102']
    time_slots = ['08:00-10:00', '10:00-12:00', '13:00-15:00']
    
    scheduler = CourseScheduler(courses, rooms, time_slots)
    result = scheduler.generate_schedule()
    
    if result:
        print("Schedule berhasil dibuat:")
        for course, (room, time) in result.items():
            print(f"{course}: {room} pada {time}")
        
        is_valid, conflicts = scheduler.validate_schedule()
        print(f"\nValid: {is_valid}")
        if conflicts:
            print(f"Conflicts: {conflicts}")
    else:
        print("Tidak bisa membuat schedule tanpa conflict")


if __name__ == '__main__':
    test_scheduler()