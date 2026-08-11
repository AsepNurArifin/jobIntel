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
}

export interface SkillRank {
  name: string
  category: string
  freq: number
}
