"use client"

import { useState, useEffect } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { toast } from "sonner"

interface Team {
  team_id: string
  team_name: string
  long_abbr: string
  short_name: string
  division: string
  owner_name: string
  total_salary?: number
  active_players?: number
  total_players?: number
}

interface LeagueStats {
  total_teams: number
  total_salary: number
  avg_team_salary: number
  total_players: number
  avg_players_per_team: number
  position_breakdown: Record<string, number>
  division_breakdown: Record<string, number>
}

interface CapSummaryTabProps {
  leagueId: string
}

export default function CapSummaryTab({ leagueId }: CapSummaryTabProps) {
  const [teams, setTeams] = useState<Team[]>([])
  const [leagueStats, setLeagueStats] = useState<LeagueStats | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  // Load league teams and calculate stats
  useEffect(() => {
    const loadLeagueData = async () => {
      setIsLoading(true)
      try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE}/api/public/cbs/league/uhhp/teams`)
        if (response.ok) {
          const teamsData = await response.json()
          setTeams(teamsData)
          
          // Calculate league-wide statistics
          const stats = calculateLeagueStats(teamsData)
          setLeagueStats(stats)
        } else {
          toast.error('Failed to load league data')
        }
      } catch (error) {
        console.error('Failed to load league data:', error)
        toast.error('Failed to load league data')
      } finally {
        setIsLoading(false)
      }
    }

    if (leagueId) {
      loadLeagueData()
    }
  }, [leagueId])

  const calculateLeagueStats = (teamsData: Team[]): LeagueStats => {
    const totalTeams = teamsData.length
    const totalSalary = teamsData.reduce((sum, team) => sum + (team.total_salary || 0), 0)
    const avgTeamSalary = totalTeams > 0 ? totalSalary / totalTeams : 0
    const totalPlayers = teamsData.reduce((sum, team) => sum + (team.total_players || 0), 0)
    const avgPlayersPerTeam = totalTeams > 0 ? totalPlayers / totalTeams : 0

    // Position breakdown (would need to be calculated from roster data)
    const positionBreakdown: Record<string, number> = {
      'C': 0,
      'W': 0,
      'D': 0,
      'G': 0
    }

    // Division breakdown
    const divisionBreakdown = teamsData.reduce((counts, team) => {
      const division = team.division || 'Unknown'
      counts[division] = (counts[division] || 0) + 1
      return counts
    }, {} as Record<string, number>)

    return {
      total_teams: totalTeams,
      total_salary: totalSalary,
      avg_team_salary: avgTeamSalary,
      total_players: totalPlayers,
      avg_players_per_team: avgPlayersPerTeam,
      position_breakdown: positionBreakdown,
      division_breakdown: divisionBreakdown
    }
  }

  if (isLoading) {
    return (
      <div className="p-4 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-500"></div>
      </div>
    )
  }

  return (
    <div className="p-4 space-y-6">
      {/* League Overview */}
      {leagueStats && (
        <Card>
          <CardContent className="p-4">
            <h3 className="text-lg font-semibold mb-4">League Overview</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">{leagueStats.total_teams}</div>
                <div className="text-sm text-gray-600">Total Teams</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">${Math.round(leagueStats.total_salary).toLocaleString()}</div>
                <div className="text-sm text-gray-600">Total Salary</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-orange-600">${Math.round(leagueStats.avg_team_salary).toLocaleString()}</div>
                <div className="text-sm text-gray-600">Avg Team Salary</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-600">{Math.round(leagueStats.avg_players_per_team)}</div>
                <div className="text-sm text-gray-600">Avg Players/Team</div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Division Breakdown */}
      {leagueStats && Object.keys(leagueStats.division_breakdown).length > 0 && (
        <Card>
          <CardContent className="p-4">
            <h3 className="text-lg font-semibold mb-4">Division Breakdown</h3>
            <div className="flex flex-wrap gap-2">
              {Object.entries(leagueStats.division_breakdown).map(([division, count]) => (
                <Badge key={division} variant="outline" className="text-sm">
                  {division}: {count} teams
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Team Rankings */}
      <Card>
        <CardContent className="p-4">
          <h3 className="text-lg font-semibold mb-4">Team Rankings</h3>
          <div className="space-y-2">
            <div className="grid grid-cols-6 gap-2 text-xs font-semibold text-gray-600 border-b pb-2">
              <div>Rank</div>
              <div>Team</div>
              <div>Division</div>
              <div>Owner</div>
              <div>Salary</div>
              <div>Players</div>
            </div>
            {teams
              .sort((a, b) => (b.total_salary || 0) - (a.total_salary || 0))
              .map((team, index) => (
                <div key={team.team_id} className="grid grid-cols-6 gap-2 py-2 text-sm border-b border-gray-100">
                  <div className="font-medium text-gray-600">#{index + 1}</div>
                  <div className="font-medium">{team.team_name}</div>
                  <div>
                    <Badge variant="outline" className="text-xs">
                      {team.division || 'Unknown'}
                    </Badge>
                  </div>
                  <div className="text-gray-600">{team.owner_name || 'N/A'}</div>
                  <div className="font-mono">${(team.total_salary || 0).toLocaleString()}</div>
                  <div className="text-gray-600">{team.total_players || 0}</div>
                </div>
              ))}
          </div>
        </CardContent>
      </Card>

      {/* Salary Distribution */}
      {teams.length > 0 && (
        <Card>
          <CardContent className="p-4">
            <h3 className="text-lg font-semibold mb-4">Salary Distribution</h3>
            <div className="space-y-2">
              {(() => {
                const salaries = teams.map(t => t.total_salary || 0).sort((a, b) => a - b)
                const min = Math.min(...salaries)
                const max = Math.max(...salaries)
                const median = salaries[Math.floor(salaries.length / 2)]
                const q1 = salaries[Math.floor(salaries.length * 0.25)]
                const q3 = salaries[Math.floor(salaries.length * 0.75)]
                
                return (
                  <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                    <div className="text-center">
                      <div className="text-lg font-bold text-red-600">${min.toLocaleString()}</div>
                      <div className="text-sm text-gray-600">Minimum</div>
                    </div>
                    <div className="text-center">
                      <div className="text-lg font-bold text-orange-600">${q1.toLocaleString()}</div>
                      <div className="text-sm text-gray-600">Q1 (25%)</div>
                    </div>
                    <div className="text-center">
                      <div className="text-lg font-bold text-blue-600">${median.toLocaleString()}</div>
                      <div className="text-sm text-gray-600">Median</div>
                    </div>
                    <div className="text-center">
                      <div className="text-lg font-bold text-purple-600">${q3.toLocaleString()}</div>
                      <div className="text-sm text-gray-600">Q3 (75%)</div>
                    </div>
                    <div className="text-center">
                      <div className="text-lg font-bold text-green-600">${max.toLocaleString()}</div>
                      <div className="text-sm text-gray-600">Maximum</div>
                    </div>
                  </div>
                )
              })()}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
