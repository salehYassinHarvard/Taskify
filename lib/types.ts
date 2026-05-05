export type AssignmentStatus = "todo" | "in_progress" | "done";

export interface Course {
  id: number;
  user_id: string;
  canvas_course_id: number | null;
  name: string;
  course_code: string;
  color: string;
}

export interface Assignment {
  id: number;
  user_id: string;
  course_id: number | null;
  canvas_assignment_id: number | null;
  title: string;
  description: string;
  due_at: string | null;
  points_possible: number | null;
  status: AssignmentStatus;
  gcal_event_id: string;
  courses?: Pick<Course, "name" | "course_code" | "color"> | null;
}

export interface CalendarEvent {
  id: number;
  user_id: string;
  gcal_event_id: string;
  summary: string;
  start_at: string | null;
  end_at: string | null;
  location: string;
  is_all_day: boolean;
}
