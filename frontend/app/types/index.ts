export interface JobItem {
  id: number
  title: string
  company: string | null
  source: string
  source_url: string
  posted_date: string | null
  location: string | null
  similarity: number
  top_skills: string[]
  description?: string
  hard_skills?: string[]
  soft_skills?: string[]
  tools?: string[]
  experience_level?: string
  min_years_experience?: number | null
  employment_type?: string
}

export interface SkillRank {
  name: string
  category: string
  freq: number
}
