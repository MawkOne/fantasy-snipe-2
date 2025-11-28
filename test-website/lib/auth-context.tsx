"use client"

import { createContext, useContext, useEffect, useState } from "react"

interface User {
  id: string
  email: string
  name?: string
  picture?: string
}

interface TeamMembership {
  id: number
  team_id: string
  team_name: string
  role: string
  league_id: number
  league_name: string
  is_admin?: boolean
}

interface AuthContextType {
  user: User | null
  teamMembership: TeamMembership | null
  isLoading: boolean
  attachToTeam: (teamId: string, leagueSlug: string) => Promise<boolean>
  refreshTeamMembership: () => Promise<void>
  login: (email?: string, name?: string, password?: string) => void
  logout: () => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [teamMembership, setTeamMembership] = useState<TeamMembership | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  // Load user/membership from localStorage on mount
  useEffect(() => {
    const savedUser = localStorage.getItem('fantasy_user')
    if (savedUser) {
      try {
        setUser(JSON.parse(savedUser))
      } catch (error) {
        console.error('Failed to parse saved user:', error)
        localStorage.removeItem('fantasy_user')
      }
    }
    const savedMember = localStorage.getItem('fantasy_membership')
    if (savedMember) {
      try {
        setTeamMembership(JSON.parse(savedMember))
      } catch (error) {
        console.error('Failed to parse saved membership:', error)
        localStorage.removeItem('fantasy_membership')
      }
    }
  }, [])

  // Helper: hydrate membership (and is_admin) from backend using current user email
  const hydrateMembershipFromBackend = async (email: string) => {
    try {
      const apiBase = (process.env.NEXT_PUBLIC_API_BASE && (process.env.NEXT_PUBLIC_API_BASE as string).startsWith("http"))
        ? (process.env.NEXT_PUBLIC_API_BASE as string)
        : "http://localhost:8000"
      const res = await fetch(`${apiBase}/api/public/cbs/league/uhhp/teams`, { cache: 'no-store' })
      if (!res.ok) return
      const data = await res.json()
      const teams = Array.isArray(data?.teams) ? data.teams : []
      const lower = email.toLowerCase()
      const matched = teams.find((t: any) => {
        const login = (t?.login || '').toString().toLowerCase()
        const attached = (t?.attached_email || '').toString().toLowerCase()
        return login === lower || attached === lower
      })
      if (matched) {
        const membership: TeamMembership = {
          id: Number(matched.team_id) || 0,
          team_id: String(matched.team_id),
          team_name: String(matched.team_name || `Team ${matched.team_id}`),
          role: String(matched.attached_role || 'member'),
          league_id: 1,
          league_name: 'UHHP League',
          is_admin: !!matched.is_admin
        }
        setTeamMembership(membership)
        localStorage.setItem('fantasy_membership', JSON.stringify(membership))
      }
    } catch (e) {
      console.error('Failed to hydrate membership:', e)
    }
  }

  const login = (email?: string, name?: string, password?: string) => {
    const newUser: User = {
      id: email || 'demo-user',
      email: email || 'demo@example.com',
      name: name || 'Demo User'
    }
    setUser(newUser)
    localStorage.setItem('fantasy_user', JSON.stringify(newUser))

    // Always try to hydrate membership (and is_admin) from backend
    if (email) {
      hydrateMembershipFromBackend(email)
    }
  }

  const logout = () => {
    setUser(null)
    setTeamMembership(null)
    localStorage.removeItem('fantasy_user')
    localStorage.removeItem('fantasy_membership')
  }

  const refreshTeamMembership = async () => {
    if (!user) {
      setTeamMembership(null)
      return
    }

    try {
      await hydrateMembershipFromBackend(user.email)
    } catch (error) {
      console.error('Failed to fetch team membership:', error)
      setTeamMembership(null)
    }
  }

  const attachToTeam = async (teamId: string, leagueSlug: string): Promise<boolean> => {
    if (!user) return false

    try {
      // For now, we'll implement this when we have the actual auth token
      // In a real implementation, you'd make an API call here
      console.log('Attaching user to team:', { teamId, leagueSlug, user: user.email })
      
      // Simulate successful attachment
      const mockMembership: TeamMembership = {
        id: 1,
        team_id: teamId,
        team_name: `Team ${teamId}`,
        role: 'member',
        league_id: 1,
        league_name: 'UHHP League'
      }
      setTeamMembership(mockMembership)
      return true
    } catch (error) {
      console.error('Failed to attach to team:', error)
      return false
    }
  }

  return (
    <AuthContext.Provider value={{
      user,
      teamMembership,
      isLoading,
      attachToTeam,
      refreshTeamMembership,
      login,
      logout
    }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}