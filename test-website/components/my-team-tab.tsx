"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { useAuth } from "@/lib/auth-context"
import { toast } from "sonner"

interface Team {
  team_id: string
  team_name: string
  long_abbr: string
  short_name: string
  division: string
  owner_name: string
}

interface Player {
  player_name: string
  position: string
  salary: number
  years: number
  slot_type: 'A' | 'I'
  nhl_player_id?: number
}

interface MyTeamTabProps {
  leagueId: string
}

export default function MyTeamTab({ leagueId }: MyTeamTabProps) {
  const { user, teamMembership, attachToTeam, isLoading: authLoading } = useAuth()
  const [teams, setTeams] = useState<Team[]>([])
  const [selectedTeamId, setSelectedTeamId] = useState<string>("")
  const [players, setPlayers] = useState<Player[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [isAttaching, setIsAttaching] = useState(false)

  // Load available teams
  useEffect(() => {
    const loadTeams = async () => {
      try {
        const apiBase = (process.env.NEXT_PUBLIC_API_BASE && (process.env.NEXT_PUBLIC_API_BASE as string).startsWith("http"))
          ? (process.env.NEXT_PUBLIC_API_BASE as string)
          : "http://localhost:8000"
        const response = await fetch(`${apiBase}/api/public/cbs/league/uhhp/teams`)
        if (response.ok) {
          const data = await response.json()
          setTeams(Array.isArray(data?.teams) ? data.teams as any : [])
        }
      } catch (error) {
        console.error('Failed to load teams:', error)
        toast.error('Failed to load teams')
      }
    }

    if (leagueId) {
      loadTeams()
    }
  }, [leagueId])

  // Load team players
  const loadTeamPlayers = async (teamId: string) => {
    if (!teamId) return

    setIsLoading(true)
    try {
      const apiBase = (process.env.NEXT_PUBLIC_API_BASE && (process.env.NEXT_PUBLIC_API_BASE as string).startsWith("http"))
        ? (process.env.NEXT_PUBLIC_API_BASE as string)
        : "http://localhost:8000"
      const response = await fetch(`${apiBase}/api/public/cbs/teams/${teamId}/roster`)
      if (response.ok) {
        const data = await response.json()
        const roster = Array.isArray(data?.roster) ? data.roster as any[] : []
        setPlayers(
          roster.map((r) => ({
            player_name: r.player_name || String(r.cbs_player_id) || String(r.nhl_player_id || ''),
            position: r.position,
            salary: typeof r.salary === 'string' ? parseFloat(r.salary) : (r.salary || 0),
            years: r.years ?? 0,
            slot_type: (r.slot_type as 'A' | 'I') ?? 'A',
            nhl_player_id: r.nhl_player_id ? Number(r.nhl_player_id) : undefined,
          }))
        )
      } else {
        toast.error('Failed to load team roster')
      }
    } catch (error) {
      console.error('Failed to load team players:', error)
      toast.error('Failed to load team players')
    } finally {
      setIsLoading(false)
    }
  }

  // Handle team selection
  const handleTeamSelect = (teamId: string) => {
    setSelectedTeamId(teamId)
    loadTeamPlayers(teamId)
  }

  // Auto-load roster when membership is present
  useEffect(() => {
    if (teamMembership?.team_id) {
      setSelectedTeamId(teamMembership.team_id)
      loadTeamPlayers(teamMembership.team_id)
    }
  }, [teamMembership])

  // If user is logged in and no membership yet, default to "New Oilers Nation"
  useEffect(() => {
    if (user && !teamMembership && teams.length && !selectedTeamId) {
      const you = teams.find(t => (t.team_name || '').toLowerCase() === 'new oilers nation'.toLowerCase())
      if (you?.team_id) {
        setSelectedTeamId(you.team_id)
        loadTeamPlayers(you.team_id)
      }
    }
  }, [user, teamMembership, teams, selectedTeamId])

  // Handle team attachment
  const handleAttachToTeam = async () => {
    if (!selectedTeamId || !user) return

    setIsAttaching(true)
    try {
      const success = await attachToTeam(selectedTeamId, 'uhhp')
      if (success) {
        toast.success('Successfully attached to team!')
        // Refresh team membership to get the updated data
        await refreshTeamMembership()
        loadTeamPlayers(selectedTeamId)
      } else {
        toast.error('Failed to attach to team')
      }
    } catch (error) {
      console.error('Failed to attach to team:', error)
      toast.error('Failed to attach to team')
    } finally {
      setIsAttaching(false)
    }
  }

  // Calculate team totals
  const activePlayers = players.filter(p => p.slot_type === 'A')
  const totalSalary = activePlayers.reduce((sum, p) => sum + (p.salary || 0), 0)
  const avgSalary = activePlayers.length > 0 ? totalSalary / activePlayers.length : 0

  const positionCounts = activePlayers.reduce((counts, player) => {
    const pos = player.position?.toUpperCase() || 'UNKNOWN'
    counts[pos] = (counts[pos] || 0) + 1
    return counts
  }, {} as Record<string, number>)

  if (authLoading) {
    return (
      <div className="p-4 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-500"></div>
      </div>
    )
  }

  if (!user) {
    return (
      <div className="p-4 text-center">
        <p className="text-gray-600 mb-4">Please log in to view your team</p>
        <Button onClick={() => window.location.href = '/callback'}>
          Login
        </Button>
      </div>
    )
  }

  return (
    <div className="p-4 space-y-6">
      {/* Team Selection */}
      <Card>
        <CardContent className="p-4">
          <h3 className="text-lg font-semibold mb-4">Team Management</h3>
          
          {teamMembership ? (
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <Badge variant="default" className="bg-green-100 text-green-800">
                  Attached
                </Badge>
                <span className="font-medium">{teamMembership.team_name}</span>
              </div>
              <p className="text-sm text-gray-600">
                You are currently attached to {teamMembership.team_name} in the {teamMembership.league_name} league.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              <p className="text-sm text-gray-600">
                Select a team to attach to your account:
              </p>
              <div className="flex gap-2">
                <Select value={selectedTeamId} onValueChange={handleTeamSelect}>
                  <SelectTrigger className="w-64">
                    <SelectValue placeholder="Choose a team..." />
                  </SelectTrigger>
                  <SelectContent>
                    {teams.map((team) => (
                      <SelectItem key={team.team_id} value={team.team_id}>
                        {team.team_name} ({team.long_abbr})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Button 
                  onClick={handleAttachToTeam}
                  disabled={!selectedTeamId || isAttaching}
                >
                  {isAttaching ? 'Attaching...' : 'Attach to Team'}
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Team Roster */}
      {teamMembership && (
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">{teamMembership.team_name} Roster</h3>
              <div className="text-sm text-gray-600">
                {activePlayers.length} active players
              </div>
            </div>

            {/* Team Summary */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <div className="text-center">
                <div className="text-2xl font-bold text-orange-600">${totalSalary.toLocaleString()}</div>
                <div className="text-sm text-gray-600">Total Salary</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">${Math.round(avgSalary).toLocaleString()}</div>
                <div className="text-sm text-gray-600">Avg Salary</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">{activePlayers.length}</div>
                <div className="text-sm text-gray-600">Active Players</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-600">{players.length - activePlayers.length}</div>
                <div className="text-sm text-gray-600">Inactive Players</div>
              </div>
            </div>

            {/* Position Breakdown */}
            <div className="mb-6">
              <h4 className="text-md font-semibold mb-2">Position Breakdown</h4>
              <div className="flex flex-wrap gap-2">
                {Object.entries(positionCounts).map(([pos, count]) => (
                  <Badge key={pos} variant="outline">
                    {pos}: {count}
                  </Badge>
                ))}
              </div>
            </div>

            {/* Player List */}
            {isLoading ? (
              <div className="flex items-center justify-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-500"></div>
              </div>
            ) : (
              <div className="space-y-2">
                <div className="grid grid-cols-6 gap-2 text-xs font-semibold text-gray-600 border-b pb-2">
                  <div>Player</div>
                  <div>Position</div>
                  <div>Status</div>
                  <div>Salary</div>
                  <div>Years</div>
                  <div>NHL ID</div>
                </div>
                {players.map((player, index) => (
                  <div 
                    key={index}
                    className={`grid grid-cols-6 gap-2 py-2 text-sm border-b border-gray-100 ${
                      player.slot_type === 'A' ? 'bg-green-50' : 'bg-gray-50'
                    }`}
                  >
                    <div className="font-medium">{player.player_name}</div>
                    <div>{player.position}</div>
                    <div>
                      <Badge variant={player.slot_type === 'A' ? 'default' : 'secondary'}>
                        {player.slot_type === 'A' ? 'Active' : 'Inactive'}
                      </Badge>
                    </div>
                    <div>${player.salary?.toLocaleString() || 'N/A'}</div>
                    <div>{player.years || 'N/A'}</div>
                    <div className="text-xs text-gray-500">{player.nhl_player_id || 'N/A'}</div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  )
}
